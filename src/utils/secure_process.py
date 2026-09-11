"""Helpers for tools that prompt for secrets only from an interactive TTY."""

from __future__ import annotations

import os
import select
import signal
import termios
import time
from collections.abc import Callable

from utils.safe_files import require_single_line_secret

# How long the tool may stay completely silent while the secret is still
# owed.  Silence is the signal: a working tool keeps printing, and failing
# loudly beats leaving the caller blocked forever.
PROMPT_TIMEOUT_SECONDS = 120.0

_POLL_INTERVAL_SECONDS = 0.05
_READ_SIZE = 4096
# Enough tail to hold any prompt plus the lines around it.
_RECENT_WINDOW = 8192
_REDACTION = "[REDACTED]"


def _child_environment() -> dict[str, str]:
    """Ask for English tool messages without disturbing filename encoding.

    Only the message category is pinned: p7zip reads ``LC_CTYPE`` to decode
    non-ASCII member names, and overriding that would corrupt archives for the
    sake of prompt text.  ``LC_ALL`` outranks every other category, so it is
    folded into ``LC_CTYPE`` rather than left in place or simply dropped, and
    ``LANGUAGE`` outranks ``LC_MESSAGES`` for translations, so it goes.
    """
    environment = {**os.environ, "LC_MESSAGES": "C"}
    everything = environment.pop("LC_ALL", "")
    if everything:
        environment["LC_CTYPE"] = everything
    environment.pop("LANGUAGE", None)
    return environment


def _echo_disabled(terminal_fd: int) -> bool:
    """Report whether the child has switched the terminal to silent entry.

    A tool about to read a secret turns off terminal echo first.  That signal
    is locale-independent, and it marks the only safe moment to write: the
    switch is issued with ``TCSAFLUSH``, which discards anything already
    typed, so a password sent one instant early is both echoed in clear text
    and silently thrown away.
    """
    try:
        return not termios.tcgetattr(terminal_fd)[3] & termios.ECHO
    except (termios.error, OSError):
        return False


def _awaiting_secret(output: str, already_sent: int, terminal_fd: int) -> bool:
    """Report whether the tool is waiting for the next line of the secret."""
    prompt = "Enter password" if already_sent == 0 else "Verify password"
    return prompt in output and _echo_disabled(terminal_fd)


def _read_available(terminal_fd: int, output: bytearray) -> bool:
    """Append whatever the child has written.  False once the stream closes."""
    readable, _, _ = select.select(
        [terminal_fd], [], [], _POLL_INTERVAL_SECONDS)
    if terminal_fd not in readable:
        return True
    try:
        chunk = os.read(terminal_fd, _READ_SIZE)
    except OSError:
        return False
    if not chunk:
        return False
    output.extend(chunk)
    return True


def _drain(terminal_fd: int, output: bytearray) -> None:
    """Collect output the tool wrote just before exiting, for error reports."""
    while True:
        readable, _, _ = select.select([terminal_fd], [], [], 0)
        if terminal_fd not in readable:
            return
        try:
            chunk = os.read(terminal_fd, _READ_SIZE)
        except OSError:
            return
        if not chunk:
            return
        output.extend(chunk)


def _recent(output: bytearray) -> str:
    """Decode the tail of the transcript, which is where prompts appear.

    Rescanning the whole buffer every poll turns a chatty multi-gigabyte
    archive into quadratic work, and a prompt is never older than the last
    few lines: a tool waiting for a password has written nothing since.
    """
    return bytes(output[-_RECENT_WINDOW:]).decode("utf-8", errors="replace")


def _reap(process_id: int, terminal_fd: int, output: bytearray) -> int | None:
    """Return the child's exit status once it has finished, else ``None``."""
    child_id, status = os.waitpid(process_id, os.WNOHANG)
    if child_id != process_id:
        return None
    _drain(terminal_fd, output)
    return status


def _report_progress(output: str, progress_callback: Callable[[float], None]) -> None:
    """Forward the most recent percentage the tool printed, if any."""
    for line in output.splitlines()[-3:]:
        if "%" not in line:
            continue
        try:
            percent = int(line.split("%")[0].strip().split()[-1])
        except (ValueError, IndexError):
            continue
        progress_callback(float(percent))


def _terminate(process_id: int) -> None:
    """Kill and reap a child that never asked for the password."""
    try:
        os.kill(process_id, signal.SIGKILL)
        os.waitpid(process_id, 0)
    except (ProcessLookupError, ChildProcessError, OSError):
        pass


def _supervise_child(
        process_id: int,
        terminal_fd: int,
        output: bytearray,
        password: str,
        *,
        confirm_password: bool,
        progress_callback: Callable[[float], None] | None,
        timeout: float) -> int:
    """Feed the secret at the only safe moment and wait for the tool to exit."""
    wanted = 2 if confirm_password else 1
    sent = 0
    stream_open = True
    deadline = time.monotonic() + timeout

    while True:
        received = len(output)
        if stream_open:
            stream_open = _read_available(terminal_fd, output)
        else:
            time.sleep(_POLL_INTERVAL_SECONDS)
        if len(output) > received:
            # The tool is still talking, so treat it as working rather than
            # stuck on a prompt this channel failed to recognize.  A tool that
            # chatters without ever prompting is not caught by this; only one
            # that falls silent is.
            deadline = time.monotonic() + timeout

        decoded = _recent(output)
        if sent < wanted and _awaiting_secret(decoded, sent, terminal_fd):
            os.write(terminal_fd, f"{password}\n".encode())
            sent += 1
            deadline = time.monotonic() + timeout
        if progress_callback:
            _report_progress(decoded, progress_callback)

        status = _reap(process_id, terminal_fd, output)
        if status is not None:
            return status
        if sent < wanted and time.monotonic() > deadline:
            # The child may have exited in the instant since the check above;
            # its real status beats reporting a timeout that did not happen.
            status = _reap(process_id, terminal_fd, output)
            if status is not None:
                return status
            _terminate(process_id)
            raise TimeoutError(
                "The encryption tool stopped responding without asking for "
                f"a password ({timeout:.0f}s of silence). "
                "Check that 7-Zip is working.")


def run_password_prompted(
        command: list[str],
        password: str,
        *,
        confirm_password: bool = False,
        progress_callback: Callable[[float], None] | None = None,
        timeout: float = PROMPT_TIMEOUT_SECONDS) -> tuple[int, str]:
    """Run a Unix CLI password prompt through a private pseudo-terminal.

    7-Zip's ``-p`` switch accepts a password prompt, but p7zip does not
    reliably read that prompt from a pipe during extraction.  A pseudo-terminal
    keeps the password out of argv while preserving the tool's intended prompt
    behavior.  Windows has no stdlib pseudo-terminal equivalent suitable for
    this GUI; callers fail closed there instead of exposing a password in argv.
    """
    require_single_line_secret(password)
    if os.name == "nt":
        raise RuntimeError(
            "Secure 7-Zip password entry is unavailable on Windows. "
            "Use GPG or VeraCrypt instead.")

    import pty

    process_id, master_fd = pty.fork()
    if process_id == 0:
        try:
            os.execvpe(command[0], command, _child_environment())
        except OSError:
            os._exit(127)

    output = bytearray()
    try:
        status = _supervise_child(
            process_id,
            master_fd,
            output,
            password,
            confirm_password=confirm_password,
            progress_callback=progress_callback,
            timeout=timeout,
        )
    finally:
        os.close(master_fd)

    # The password is written only once echo is off, but never surface one if
    # a third-party build were to echo it unexpectedly.
    decoded_output = output.decode("utf-8", errors="replace")
    return os.waitstatus_to_exitcode(status), decoded_output.replace(
        password, _REDACTION)
