"""Keyfile generation, validation and combination with a password.

A keyfile is one of the two things standing between an attacker and the
user's archives, so its randomness, its permissions and the refusal to
overwrite one that already exists all matter.
"""

import os
import stat

import pytest

from utils.keyfile_auth import (
    combine_keyfile_and_password,
    generate_keyfile,
    load_keyfile,
    validate_keyfile,
)
from utils.safe_files import OutputCollisionError


@pytest.fixture
def keyfile(tmp_path):
    path = tmp_path / "key.diophantus"
    generate_keyfile(str(path))
    return path


def test_a_generated_keyfile_has_the_default_size(keyfile):
    assert keyfile.stat().st_size == 64


def test_a_generated_keyfile_is_readable_only_by_its_owner(keyfile):
    assert stat.S_IMODE(keyfile.stat().st_mode) == 0o600


def test_two_generated_keyfiles_differ(tmp_path):
    first = tmp_path / "first.diophantus"
    second = tmp_path / "second.diophantus"
    generate_keyfile(str(first))
    generate_keyfile(str(second))

    assert first.read_bytes() != second.read_bytes()


def test_generating_over_an_existing_keyfile_is_refused(keyfile):
    original = keyfile.read_bytes()

    with pytest.raises(OutputCollisionError):
        generate_keyfile(str(keyfile))

    assert keyfile.read_bytes() == original


@pytest.mark.parametrize("size", [15, 1025, 0, -1])
def test_an_out_of_range_size_is_refused(tmp_path, size):
    with pytest.raises(ValueError, match="between 16 and 1024 bytes"):
        generate_keyfile(str(tmp_path / "key.diophantus"), size=size)


@pytest.mark.parametrize("size", [16, 64, 1024])
def test_sizes_within_range_are_honoured(tmp_path, size):
    path = tmp_path / f"key-{size}.diophantus"
    generate_keyfile(str(path), size=size)

    assert path.stat().st_size == size


def test_a_non_integer_size_is_refused(tmp_path):
    with pytest.raises(ValueError, match="between 16 and 1024 bytes"):
        generate_keyfile(str(tmp_path / "key.diophantus"), size=64.0)


def test_load_returns_the_bytes_that_were_written(keyfile):
    assert load_keyfile(str(keyfile)) == keyfile.read_bytes()


def test_validation_accepts_a_generated_keyfile(keyfile):
    assert validate_keyfile(str(keyfile)) is True


def test_validation_rejects_an_empty_or_missing_keyfile(tmp_path):
    empty = tmp_path / "empty.diophantus"
    empty.write_bytes(b"")

    assert validate_keyfile(str(empty)) is False
    assert validate_keyfile(str(tmp_path / "absent.diophantus")) is False


def test_validation_rejects_a_directory(tmp_path):
    assert validate_keyfile(str(tmp_path)) is False


def test_combining_is_deterministic(keyfile):
    first = combine_keyfile_and_password(str(keyfile), "correct horse")
    second = combine_keyfile_and_password(str(keyfile), "correct horse")

    assert first == second


def test_combining_depends_on_both_the_keyfile_and_the_password(
        tmp_path, keyfile):
    other_keyfile = tmp_path / "other.diophantus"
    generate_keyfile(str(other_keyfile))

    baseline = combine_keyfile_and_password(str(keyfile), "correct horse")

    assert combine_keyfile_and_password(str(keyfile), "battery staple") != baseline
    assert combine_keyfile_and_password(str(other_keyfile), "correct horse") != baseline


def test_the_combined_secret_never_contains_the_raw_password(keyfile):
    combined = combine_keyfile_and_password(str(keyfile), "correct horse")

    assert "correct horse" not in combined


def test_the_combined_secret_is_a_single_line_of_text(keyfile):
    combined = combine_keyfile_and_password(str(keyfile), "correct horse")

    assert isinstance(combined, str)
    assert combined
    assert "\n" not in combined
    assert "\r" not in combined


def test_a_keyfile_is_created_without_a_window_of_loose_permissions(tmp_path):
    """0600 comes from ``open`` itself, not a later ``chmod``.

    A keyfile created with the default umask and tightened afterwards is
    world-readable for the moment in between, which is long enough.
    """
    path = tmp_path / "key.diophantus"
    original_umask = os.umask(0)
    try:
        generate_keyfile(str(path))
    finally:
        os.umask(original_umask)

    assert stat.S_IMODE(path.stat().st_mode) == 0o600
