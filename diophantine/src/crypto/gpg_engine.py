import subprocess
import os
import shutil
import tarfile
import tempfile


def _find_gpg():
    for name in ("gpg", "gpg2"):
        if shutil.which(name):
            return name
    raise FileNotFoundError(
        "GPG is not installed.\n\n"
        "Install via Homebrew:  brew install gnupg")


def _run_gpg(cmd, password=None):
    """Run a GPG command, passing password via stdin for security."""
    proc = subprocess.run(
        cmd,
        input=password,
        capture_output=True,
        text=True)
    if proc.returncode != 0:
        error_lines = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(
            f"GPG failed (exit code {proc.returncode}).\n{error_lines}")


def create_gpg_encrypted(items, output_path, password, single_archive=False):
    """
    Encrypt files using GPG symmetric AES-256.

    Multiple files are tarred first, then encrypted -> output.tar.gpg
    Single file is encrypted directly -> output.gpg
    """
    gpg = _find_gpg()

    if len(items) > 1 or single_archive:
        # Tar first, then encrypt
        tar_path = output_path + ".tar"
        try:
            with tarfile.open(tar_path, "w") as tar:
                for item in items:
                    tar.add(item, arcname=os.path.basename(item))

            cmd = [
                gpg,
                "--batch", "--yes",
                "--symmetric",
                "--cipher-algo", "AES256",
                "--passphrase-fd", "0",
                "--output", output_path,
                tar_path,
            ]
            _run_gpg(cmd, password=password)
        finally:
            if os.path.exists(tar_path):
                os.remove(tar_path)
    else:
        # Single file, encrypt directly
        cmd = [
            gpg,
            "--batch", "--yes",
            "--symmetric",
            "--cipher-algo", "AES256",
            "--passphrase-fd", "0",
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

    if is_tar:
        # Decrypt to temp, then extract tar
        with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            cmd = [
                gpg,
                "--batch", "--yes",
                "--decrypt",
                "--passphrase-fd", "0",
                "--output", tmp_path,
                file_path,
            ]
            _run_gpg(cmd, password=password)

            if progress_callback:
                progress_callback(50.0)

            with tarfile.open(tmp_path, "r") as tar:
                tar.extractall(path=output_dir)

            if progress_callback:
                progress_callback(100.0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    else:
        # Decrypt directly to output
        decrypted_path = os.path.join(output_dir, decrypted_name)
        cmd = [
            gpg,
            "--batch", "--yes",
            "--decrypt",
            "--passphrase-fd", "0",
            "--output", decrypted_path,
            file_path,
        ]
        _run_gpg(cmd, password=password)

        if progress_callback:
            progress_callback(100.0)
