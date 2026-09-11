from pathlib import Path

import pytest

from utils.safe_files import (
    OutputCollisionError,
    commit_staging_dir,
    make_staging_dir,
    require_single_line_secret,
    validate_input_items,
)


def test_commit_staging_dir_moves_new_output_without_overwriting(tmp_path):
    destination = tmp_path / "output"
    staging = make_staging_dir(str(destination))
    staged_file = Path(staging) / "new.txt"
    staged_file.write_text("safe output", encoding="utf-8")

    commit_staging_dir(staging, str(destination))

    assert (destination / "new.txt").read_text(encoding="utf-8") == "safe output"


def test_commit_staging_dir_rejects_existing_output(tmp_path):
    destination = tmp_path / "output"
    destination.mkdir()
    existing = destination / "same.txt"
    existing.write_text("preserve me", encoding="utf-8")
    staging = make_staging_dir(str(destination))
    (Path(staging) / "same.txt").write_text(
        "replacement", encoding="utf-8")

    with pytest.raises(OutputCollisionError):
        commit_staging_dir(staging, str(destination))

    assert existing.read_text(encoding="utf-8") == "preserve me"


@pytest.mark.parametrize("secret", ["", "line\nbreak", "line\rbreak"])
def test_secret_must_be_nonempty_and_single_line(secret):
    with pytest.raises(ValueError):
        require_single_line_secret(secret)


def test_input_validation_rejects_a_symbolic_link(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("sensitive", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(target)

    with pytest.raises(ValueError, match="symbolic link"):
        validate_input_items([str(link)])
