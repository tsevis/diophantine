import os
import shutil
import subprocess
import tarfile
import tempfile

from utils.safe_files import (
    commit_staging_dir,
    make_staging_dir,
    remove_staging_dir,
    require_new_file,
    require_single_line_secret,
    validate_input_items,
)


def _find_gpg():
    for name in ("gpg", "gpg2"):
        if shutil.which(name):
            return name
    raise FileNotFoundError(
        "GPG is not installed.\n\n"
        "Install via Homebrew:  brew install gnupg")


def _run_gpg(cmd, password=None):
    """Run a GPG command, passing password via stdin for security."""
    if password is not None:
        require_single_line_secret(password)
    proc = subprocess.run(
        cmd,
        input=f"{password}\n" if password is not None else None,
        capture_output=True,
        check=False,
        text=True)
    if proc.returncode != 0:
        error_lines = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(
            f"GPG failed (exit code {proc.returncode}).\n{error_lines}")


def _gpg_passphrase_args():
    """Return non-interactive arguments that keep the secret off argv."""
    return [
        "--batch",
        "--pinentry-mode", "loopback",
        "--no-symkey-cache",
        "--passphrase-fd", "0",
    ]


def _safe_extract_tar(tar, output_dir):
    """Extract regular archive data without links, devices, or path escapes."""
    root = os.path.realpath(output_dir)
    members = tar.getmembers()
    for member in members:
        target = os.path.realpath(os.path.join(root, member.name))
        try:
            contained = os.path.commonpath((root, target)) == root
        except ValueError:
            contained = False
        if not member.name or os.path.isabs(member.name) or not contained:
            raise ValueError(f"Unsafe archive path: {member.name!r}")
        if not (member.isfile() or member.isdir()):
            raise ValueError(
                f"Unsupported archive member type: {member.name!r}")

    if hasattr(tarfile, "data_filter"):
        tar.extractall(path=output_dir, filter="data")
    else:
        for member in members:
            tar.extract(member, path=output_dir, set_attrs=False)


def create_gpg_encrypted(items, output_path, password, single_archive=False):
    """
    Encrypt files using GPG symmetric AES-256.

    Multiple files are tarred first, then encrypted -> output.tar.gpg
    Single file is encrypted directly -> output.gpg
    """
    gpg = _find_gpg()
    validate_input_items(items)
    require_new_file(output_path)

    if len(items) > 1 or single_archive:
        # Tar first in a private directory, then encrypt.  Never materialize
        # plaintext beside the user's encrypted output with default permissions.
        parent_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(parent_dir, exist_ok=True)
        work_dir = tempfile.mkdtemp(prefix=".diophantine-", dir=parent_dir)
        tar_path = os.path.join(work_dir, "payload.tar")
        try:
            with tarfile.open(tar_path, "w") as tar:
                for item in items:
                    tar.add(item, arcname=os.path.basename(item))

            cmd = [
                gpg,
                "--symmetric",
                "--cipher-algo", "AES256",
                *_gpg_passphrase_args(),
                "--output", output_path,
                tar_path,
            ]
            _run_gpg(cmd, password=password)
        finally:
            remove_staging_dir(work_dir)
    else:
        # Single file, encrypt directly
        cmd = [
            gpg,
            "--symmetric",
            "--cipher-algo", "AES256",
            *_gpg_passphrase_args(),
            "--output", output_path,
            items[0],
        ]
        _run_gpg(cmd, password=password)


def extract_gpg_encrypted(file_path, output_dir, password, progress_callback=None):
    """
    Decrypt a GPG-encrypted file.
    Auto-detects and extracts tar archives.
    """
    gpg = _find_gpg()
    os.makedirs(output_dir, exist_ok=True)
    staging_dir = make_staging_dir(output_dir)
    work_dir = None

    # Determine decrypted output name
    base = os.path.basename(file_path)
    # Strip .gpg/.pgp/.asc extension
    for ext in (".tar.gpg", ".gpg", ".pgp", ".asc"):
        if base.lower().endswith(ext):
            decrypted_name = base[:-len(ext)]
            is_tar = ext == ".tar.gpg"
            break
    else:
        decrypted_name = base + ".decrypted"
        is_tar = False

    if progress_callback:
        progress_callback(10.0)

    try:
        if is_tar:
            # Decrypt into a private directory, then extract only safe members.
            work_dir = make_staging_dir(output_dir)
            # Name the payload without creating it: GnuPG runs with --batch
            # and no --yes, so it refuses to write over a file that exists.
            # The directory is private, so an unused name is safe here.
            tmp_path = os.path.join(work_dir, "payload.tar")
            cmd = [
                gpg,
                "--decrypt",
                *_gpg_passphrase_args(),
                "--output", tmp_path,
                file_path,
            ]
            _run_gpg(cmd, password=password)

            if progress_callback:
                progress_callback(50.0)

            with tarfile.open(tmp_path, "r") as tar:
                _safe_extract_tar(tar, staging_dir)

            if progress_callback:
                progress_callback(100.0)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        else:
            # Decrypt into staging so an existing file is never replaced.
            decrypted_path = os.path.join(staging_dir, decrypted_name)
            cmd = [
                gpg,
                "--decrypt",
                *_gpg_passphrase_args(),
                "--output", decrypted_path,
                file_path,
            ]
            _run_gpg(cmd, password=password)

            if progress_callback:
                progress_callback(100.0)
        commit_staging_dir(staging_dir, output_dir)
    finally:
        remove_staging_dir(staging_dir)
        remove_staging_dir(work_dir)
