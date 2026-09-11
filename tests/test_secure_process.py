"""Regression tests for the private-terminal password channel.

The tools this app drives print their password prompt *before* switching the
terminal to silent entry, and they perform that switch with ``TCSAFLUSH``,
which discards anything already typed.  A password written on the strength of
the prompt text alone is therefore echoed in clear text and then thrown away,
leaving the tool waiting for input that will never arrive.
"""

import os
import sys
import textwrap

import pytest

from utils.secure_process import _child_environment, run_password_prompted

pytestmark = pytest.mark.skipif(
    os.name == "nt", reason="The pseudo-terminal channel is POSIX-only")

SECRET = "s3cret-passphrase"

# A stand-in for 7-Zip that reproduces the ordering that matters: prompt, then
# a deliberate pause, then silence the terminal and read.
PROMPTER = textwrap.dedent(
    """
    import sys
    import termios
    import time

    delay = float(sys.argv[1])
    expected = sys.argv[2]
    verifications = int(sys.argv[3])


    def prompt(label):
        sys.stdout.write(f"{label} password (will not be echoed):")
        sys.stdout.flush()


    prompt("Enter")
    time.sleep(delay)
    attributes = termios.tcgetattr(0)
    attributes[3] &= ~termios.ECHO
    termios.tcsetattr(0, termios.TCSAFLUSH, attributes)

    received = [sys.stdin.readline().rstrip("\\n")]
    for _ in range(verifications):
        prompt("Verify")
        received.append(sys.stdin.readline().rstrip("\\n"))

    sys.exit(0 if all(line == expected for line in received) else 3)
    """
)


@pytest.fixture
def prompter(tmp_path):
    """Return a factory for commands that prompt the way 7-Zip does."""
    script = tmp_path / "prompter.py"
    script.write_text(PROMPTER, encoding="utf-8")

    def command(delay=0.4, verifications=0):
        return [
            sys.executable, str(script), str(delay), SECRET,
            str(verifications),
        ]

    return command


def test_secret_waits_until_the_child_silences_the_terminal(prompter):
    returncode, output = run_password_prompted(prompter(), SECRET, timeout=15)

    assert returncode == 0
    # Redaction only rewrites text that actually appeared, so the absence of
    # the marker proves the secret was never written into an echoing terminal.
    assert "[REDACTED]" not in output


def test_confirmation_prompt_is_answered_as_well(prompter):
    returncode, output = run_password_prompted(
        prompter(verifications=1), SECRET,
        confirm_password=True, timeout=15)

    assert returncode == 0
    assert "[REDACTED]" not in output


def test_a_wrong_secret_still_surfaces_the_tool_exit_code(prompter):
    returncode, _ = run_password_prompted(
        prompter(), "not-the-passphrase", timeout=15)

    assert returncode == 3


def test_a_tool_that_never_prompts_fails_loudly_instead_of_hanging():
    with pytest.raises(TimeoutError):
        run_password_prompted(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            SECRET, timeout=1)


def test_an_empty_secret_is_refused_before_any_process_starts(prompter):
    with pytest.raises(ValueError):
        run_password_prompted(prompter(), "")


CHATTY_PROMPTER = textwrap.dedent(
    """
    import sys
    import termios
    import time

    expected = sys.argv[1]

    for _ in range(15):
        sys.stdout.write("Scanning the drive...\\n")
        sys.stdout.flush()
        time.sleep(0.2)

    sys.stdout.write("Enter password (will not be echoed):")
    sys.stdout.flush()
    attributes = termios.tcgetattr(0)
    attributes[3] &= ~termios.ECHO
    termios.tcsetattr(0, termios.TCSAFLUSH, attributes)

    sys.exit(0 if sys.stdin.readline().rstrip("\\n") == expected else 3)
    """
)


def test_a_tool_that_keeps_talking_is_not_killed_before_it_prompts(tmp_path):
    """The deadline measures silence, not elapsed time.

    Scanning a large selection takes far longer than the handshake, and a
    tool that is still reporting progress must never be mistaken for one
    stuck on a prompt this channel failed to recognize.
    """
    script = tmp_path / "chatty.py"
    script.write_text(CHATTY_PROMPTER, encoding="utf-8")

    returncode, _ = run_password_prompted(
        [sys.executable, str(script), SECRET], SECRET, timeout=1.0)

    assert returncode == 0


def test_message_locale_is_forced_without_disturbing_filename_encoding(
        monkeypatch):
    """``LC_ALL`` outranks every other category, so it cannot simply be left.

    Dropping it outright would also drop the character encoding the tool uses
    to decode member names, so its value is folded into ``LC_CTYPE`` first.
    """
    monkeypatch.setenv("LC_ALL", "el_GR.UTF-8")
    monkeypatch.setenv("LANGUAGE", "el")
    monkeypatch.delenv("LC_CTYPE", raising=False)

    environment = _child_environment()

    assert "LC_ALL" not in environment
    assert "LANGUAGE" not in environment
    assert environment["LC_CTYPE"] == "el_GR.UTF-8"
    assert environment["LC_MESSAGES"] == "C"


def test_message_locale_leaves_an_existing_ctype_alone(monkeypatch):
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.setenv("LC_CTYPE", "C.UTF-8")

    environment = _child_environment()

    assert environment["LC_CTYPE"] == "C.UTF-8"
    assert environment["LC_MESSAGES"] == "C"
