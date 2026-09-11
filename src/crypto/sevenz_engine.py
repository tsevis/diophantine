import shutil

from utils.safe_files import (
    commit_staging_dir,
    make_staging_dir,
    remove_staging_dir,
    require_new_file,
    validate_input_items,
)
from utils.secure_process import run_password_prompted


def _find_7z():
    for name in ("7z", "7zz"):
        if shutil.which(name):
            return name
    raise FileNotFoundError(
        "7-Zip is not installed.\n\n"
        "Install via Homebrew:  brew install p7zip")


def _run_7z(cmd, password, confirm_password=False, progress_callback=None):
    """Run a 7z command, raising a sanitized error on failure."""
    returncode, output = run_password_prompted(
        cmd,
        password,
        confirm_password=confirm_password,
        progress_callback=progress_callback,
    )
    if returncode != 0:
        error_lines = output.strip()
        raise RuntimeError(
            f"7-Zip failed (exit code {returncode}).\n{error_lines}")


def create_encrypted_7z(items, output_path, password):
    """
    Create a 7z archive with AES-256 encryption and header encryption.
    """
    sz = _find_7z()
    validate_input_items(items)
    require_new_file(output_path)

    cmd = [
        sz, "a",
        "-t7z",
        "-mhe=on",
        "-p",
        output_path,
        "--",
    ] + list(items)

    _run_7z(cmd, password, confirm_password=True)


def extract_encrypted_7z(archive_path, output_dir, password, progress_callback=None):
    """
    Extract an AES-256 encrypted 7z archive.
    """
    sz = _find_7z()
    staging_dir = make_staging_dir(output_dir)

    cmd = [
        sz, "x",
        "-t7z",
        f"-o{staging_dir}",
        "-y",
        "--",
        archive_path,
    ]

    try:
        if progress_callback is None:
            _run_7z(cmd, password)
        else:
            _run_7z(cmd, password, progress_callback=progress_callback)
        commit_staging_dir(staging_dir, output_dir)
    finally:
        remove_staging_dir(staging_dir)
