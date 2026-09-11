import os
import shutil
import subprocess
import tempfile

from utils.safe_files import (
    commit_staging_dir,
    make_staging_dir,
    remove_staging_dir,
    require_new_file,
    require_single_line_secret,
    validate_input_items,
)

# macOS: VeraCrypt CLI lives inside the app bundle
_VERACRYPT_PATHS = [
    "veracrypt",
    "/Applications/VeraCrypt.app/Contents/MacOS/VeraCrypt",
]


def _find_veracrypt():
    for path in _VERACRYPT_PATHS:
        if shutil.which(path):
            return path
    raise FileNotFoundError(
        "VeraCrypt is not installed.\n\n"
        "Install it from https://veracrypt.fr/en/Downloads.html\n"
        "then create a symlink:\n"
        "  sudo ln -s /Applications/VeraCrypt.app/Contents/MacOS/VeraCrypt "
        "/usr/local/bin/veracrypt")


def _run_veracrypt(cmd, password=None, check=True):
    """Run VeraCrypt without exposing a password in process arguments."""
    if password is not None:
        require_single_line_secret(password)
    result = subprocess.run(
        cmd,
        input=f"{password}\n" if password is not None else None,
        capture_output=True,
        check=False,
        text=True,
    )
    if check and result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(
            f"VeraCrypt failed (exit code {result.returncode}).\n{details}")
    return result


def _validate_container_items(items):
    """Reject duplicate archive roots before writing into a new volume."""
    names = [os.path.basename(os.path.normpath(item)) for item in items]
    duplicates = {name for name in names if names.count(name) > 1}
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        raise ValueError(f"Duplicate input names are not supported: {joined}")


def create_veracrypt_container(
    items,
    container_path,
    password,
    size_mb,
    filesystem="exFAT",
):
    vc = _find_veracrypt()
    validate_input_items(items)
    require_new_file(container_path)
    _validate_container_items(items)
    if size_mb < 10:
        raise ValueError("Container size must be at least 10 MB.")
    mount_dir = tempfile.mkdtemp()
    mounted = False

    try:
        _run_veracrypt([
            vc,
            "--text",
            "--create", container_path,
            "--size", f"{size_mb}M",
            "--encryption", "AES",
            "--hash", "SHA-512",
            "--filesystem", filesystem,
            "--pim", "0",
            "--stdin",
            "--non-interactive"
        ], password)

        _run_veracrypt([
            vc,
            "--text",
            "--mount", container_path,
            mount_dir,
            "--pim", "0",
            "--stdin",
            "--non-interactive"
        ], password)
        mounted = True

        for item in items:
            item_name = os.path.basename(os.path.normpath(item))
            shutil.copytree(item, os.path.join(mount_dir, item_name)) \
                if os.path.isdir(item) else shutil.copy(item, mount_dir)

    finally:
        if mounted:
            _run_veracrypt(
                [vc, "--text", "--dismount", mount_dir], check=False)
        shutil.rmtree(mount_dir, ignore_errors=True)


def mount_veracrypt_container(container_path, mount_dir, password):
    """
    Mount a VeraCrypt container at the specified directory.

    Returns:
        str: The mount directory path.
    """
    vc = _find_veracrypt()
    os.makedirs(mount_dir, exist_ok=True)
    _run_veracrypt([
        vc,
        "--text",
        "--mount", container_path,
        mount_dir,
        "--pim", "0",
        "--stdin",
        "--non-interactive"
    ], password)
    return mount_dir


def unmount_veracrypt_container(mount_dir=None):
    """
    Unmount a VeraCrypt container.

    Args:
        mount_dir: Specific mount point to unmount. If None, unmounts all.
    """
    vc = _find_veracrypt()
    if not mount_dir:
        raise ValueError("A specific VeraCrypt mount directory is required.")
    _run_veracrypt([vc, "--text", "--dismount", mount_dir])


def extract_veracrypt_container(container_path, output_dir, password, progress_callback=None):
    """
    Mount, copy all files to output_dir, then unmount.
    """
    mount_dir = tempfile.mkdtemp()
    staging_dir = make_staging_dir(output_dir)
    mounted = False

    try:
        mount_veracrypt_container(container_path, mount_dir, password)
        mounted = True

        # Collect all items in the mounted container
        entries = os.listdir(mount_dir)
        total = len(entries)

        for i, entry in enumerate(entries):
            src = os.path.join(mount_dir, entry)
            dst = os.path.join(staging_dir, entry)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

            if progress_callback and total > 0:
                progress_callback((i + 1) / total * 100)

        commit_staging_dir(staging_dir, output_dir)
    finally:
        try:
            if mounted:
                unmount_veracrypt_container(mount_dir)
        finally:
            shutil.rmtree(mount_dir, ignore_errors=True)
            remove_staging_dir(staging_dir)
