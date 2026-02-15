import subprocess
import shutil


def _find_7z():
    for name in ("7z", "7zz"):
        if shutil.which(name):
            return name
    raise FileNotFoundError(
        "7-Zip is not installed.\n\n"
        "Install via Homebrew:  brew install p7zip")


def _run_7z(cmd):
    """Run a 7z command, raising a sanitized error on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        error_lines = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(
            f"7-Zip failed (exit code {result.returncode}).\n{error_lines}")


def create_encrypted_7z(items, output_path, password):
    """
    Create a 7z archive with AES-256 encryption and header encryption.
    """
    sz = _find_7z()

    cmd = [
        sz, "a",
        "-t7z",
        "-mhe=on",
        f"-p{password}",
        output_path,
    ] + list(items)

    _run_7z(cmd)


def extract_encrypted_7z(archive_path, output_dir, password, progress_callback=None):
    """
    Extract an AES-256 encrypted 7z archive.
    """
    sz = _find_7z()

    cmd = [
        sz, "x",
        "-t7z",
        f"-p{password}",
        f"-o{output_dir}",
        "-y",
        archive_path,
    ]

    if progress_callback is None:
        _run_7z(cmd)
        return

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True)
    for line in proc.stdout:
        line = line.strip()
        if "%" in line:
            try:
                pct = int(line.split("%")[0].strip().split()[-1])
                progress_callback(float(pct))
            except (ValueError, IndexError):
                pass
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(
            f"7-Zip extraction failed (exit code {proc.returncode}).")
