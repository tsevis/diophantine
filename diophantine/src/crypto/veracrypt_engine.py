import subprocess
import os
import tempfile
import shutil

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


def create_veracrypt_container(
    items,
    container_path,
    password,
    size_mb=500
):
    vc = _find_veracrypt()
    mount_dir = tempfile.mkdtemp()

    try:
        subprocess.run([
            vc,
            "--text",
            "--create", container_path,
            "--size", f"{size_mb}M",
            "--encryption", "AES",
            "--hash", "SHA-512",
            "--filesystem", "FAT",
            "--password", password,
            "--pim", "0",
            "--non-interactive"
        ], check=True)

        subprocess.run([
            vc,
            "--text",
            "--mount", container_path,
            mount_dir,
            "--password", password,
            "--non-interactive"
        ], check=True)

        for item in items:
            shutil.copytree(item, os.path.join(mount_dir, os.path.basename(item))) \
                if os.path.isdir(item) else shutil.copy(item, mount_dir)

    finally:
        subprocess.run([vc, "-d"], check=False)
        shutil.rmtree(mount_dir)


def mount_veracrypt_container(container_path, mount_dir, password):
    """
    Mount a VeraCrypt container at the specified directory.

    Returns:
        str: The mount directory path.
    """
    vc = _find_veracrypt()
    os.makedirs(mount_dir, exist_ok=True)
    subprocess.run([
        vc,
        "--text",
        "--mount", container_path,
        mount_dir,
        "--password", password,
        "--non-interactive"
    ], check=True)
    return mount_dir


def unmount_veracrypt_container(mount_dir=None):
    """
    Unmount a VeraCrypt container.

    Args:
        mount_dir: Specific mount point to unmount. If None, unmounts all.
    """
    vc = _find_veracrypt()
    if mount_dir:
        subprocess.run([
            vc, "--text", "--dismount", mount_dir
        ], check=True)
    else:
        subprocess.run([vc, "-d"], check=True)


def extract_veracrypt_container(container_path, output_dir, password, progress_callback=None):
    """
    Mount, copy all files to output_dir, then unmount.
    """
    mount_dir = tempfile.mkdtemp()
    mounted = False

    try:
        mount_veracrypt_container(container_path, mount_dir, password)
        mounted = True

        # Collect all items in the mounted container
        entries = os.listdir(mount_dir)
        total = len(entries)

        os.makedirs(output_dir, exist_ok=True)

        for i, entry in enumerate(entries):
            src = os.path.join(mount_dir, entry)
            dst = os.path.join(output_dir, entry)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

            if progress_callback and total > 0:
                progress_callback((i + 1) / total * 100)

    finally:
        if mounted:
            unmount_veracrypt_container(mount_dir)
        shutil.rmtree(mount_dir, ignore_errors=True)