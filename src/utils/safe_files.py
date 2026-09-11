"""Safe filesystem helpers for encryption and extraction workflows."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path


class OutputCollisionError(FileExistsError):
    """Raised when an operation would overwrite an existing user file."""


def require_single_line_secret(secret: str) -> str:
    """Reject empty or multi-line secrets before invoking external tools."""
    if not isinstance(secret, str) or not secret:
        raise ValueError("Passwords and recovery phrases cannot be empty.")
    if "\n" in secret or "\r" in secret:
        raise ValueError("Passwords and recovery phrases cannot contain newlines.")
    return secret


def require_new_file(path: str) -> None:
    """Refuse to create an output file over an existing path."""
    if os.path.lexists(path):
        raise OutputCollisionError(
            f"Refusing to overwrite existing output: {path}")


def validate_input_items(items: list[str]) -> None:
    """Accept only regular files and real directories without symlinks.

    Following a symlink while encrypting can silently include data located
    outside the user's selected tree.  Device files and FIFOs are likewise
    unsuitable for a desktop archive workflow and may block a tool process.
    """
    for item in items:
        if os.path.islink(item):
            raise ValueError(f"Refusing to encrypt symbolic link: {item}")
        if os.path.isfile(item):
            continue
        if not os.path.isdir(item):
            raise ValueError(
                f"Only regular files and directories can be encrypted: {item}")

        for directory, subdirectories, filenames in os.walk(item):
            for name in subdirectories:
                path = os.path.join(directory, name)
                if os.path.islink(path):
                    raise ValueError(f"Refusing to encrypt symbolic link: {path}")
            for name in filenames:
                path = os.path.join(directory, name)
                if os.path.islink(path):
                    raise ValueError(f"Refusing to encrypt symbolic link: {path}")
                if not os.path.isfile(path):
                    raise ValueError(
                        "Only regular files and directories can be encrypted: "
                        f"{path}")


def make_staging_dir(output_dir: str) -> str:
    """Create a private staging directory on the destination filesystem."""
    os.makedirs(output_dir, exist_ok=True)
    return tempfile.mkdtemp(prefix=".diophantine-", dir=output_dir)


def commit_staging_dir(staging_dir: str, output_dir: str) -> None:
    """Move staged top-level outputs into place only when none collide.

    The staging directory is created below ``output_dir`` so renames remain on
    the same filesystem.  Files are never replaced.
    """
    staging = Path(staging_dir)
    destination = Path(output_dir)
    entries = list(staging.iterdir())
    try:
        collisions = [
            entry.name for entry in entries
            if os.path.lexists(destination / entry.name)
        ]
        if collisions:
            joined = ", ".join(sorted(collisions))
            raise OutputCollisionError(
                f"Refusing to overwrite existing output: {joined}")
        for entry in entries:
            os.rename(entry, destination / entry.name)
    finally:
        # After a failed commit, leave no app-created plaintext behind.
        shutil.rmtree(staging_dir, ignore_errors=True)


def remove_staging_dir(staging_dir: str | None) -> None:
    """Remove a private staging directory created by ``make_staging_dir``."""
    if staging_dir:
        shutil.rmtree(staging_dir, ignore_errors=True)
