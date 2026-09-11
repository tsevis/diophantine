"""A recovery phrase must still open archives written before derivation.

Encryption now stretches the phrase into a high-entropy secret, but archives
written earlier were encrypted with the bare phrase.  Changing the secret
without keeping the old one reachable would lock the user out of their own
files permanently, so this exercises both against a real 7-Zip.
"""

import shutil

import pytest

from crypto.sevenz_engine import create_encrypted_7z, extract_encrypted_7z
from utils.recovery_phrase import (
    legacy_secret_from_phrase,
    phrase_secret_candidates,
    secret_from_phrase,
)
from utils.secret_attempts import attempt_with_secrets

pytestmark = pytest.mark.skipif(
    shutil.which("7z") is None and shutil.which("7zz") is None,
    reason="7-Zip is not installed",
)

# BIP-39 English test vector 2, so the phrase is a real, valid one.
PHRASE = [
    "legal", "winner", "thank", "year", "wave", "sausage",
    "worth", "useful", "legal", "winner", "thank", "yellow",
]


def _archive_with(tmp_path, secret, name):
    source = tmp_path / f"{name}.txt"
    source.write_text("confidential", encoding="utf-8")
    archive = tmp_path / f"{name}.7z"
    create_encrypted_7z([str(source)], str(archive), secret)
    return archive


def _decrypt_as_the_app_does(archive, output_dir):
    """Mirror what the decrypt tab does: try each candidate in order."""
    attempt_with_secrets(
        lambda secret: extract_encrypted_7z(
            str(archive), str(output_dir), secret),
        phrase_secret_candidates(PHRASE),
    )


def test_an_archive_written_today_opens_with_the_derived_secret(tmp_path):
    archive = _archive_with(tmp_path, secret_from_phrase(PHRASE), "current")
    output = tmp_path / "out-current"

    _decrypt_as_the_app_does(archive, output)

    assert (output / "current.txt").read_text(encoding="utf-8") == "confidential"


def test_an_archive_written_before_derivation_still_opens(tmp_path):
    archive = _archive_with(
        tmp_path, legacy_secret_from_phrase(PHRASE), "legacy")
    output = tmp_path / "out-legacy"

    _decrypt_as_the_app_does(archive, output)

    assert (output / "legacy.txt").read_text(encoding="utf-8") == "confidential"


def test_a_failed_first_attempt_leaves_nothing_for_the_second_to_collide_with(
        tmp_path):
    """The fallback only works because staging cleans up after a failure."""
    archive = _archive_with(
        tmp_path, legacy_secret_from_phrase(PHRASE), "legacy")
    output = tmp_path / "out"
    output.mkdir()

    _decrypt_as_the_app_does(archive, output)

    assert sorted(path.name for path in output.iterdir()) == ["legacy.txt"]


def test_the_wrong_phrase_opens_neither(tmp_path):
    archive = _archive_with(tmp_path, secret_from_phrase(PHRASE), "current")
    other = ["abandon"] * 11 + ["about"]

    with pytest.raises(RuntimeError):
        attempt_with_secrets(
            lambda secret: extract_encrypted_7z(
                str(archive), str(tmp_path / "nope"), secret),
            phrase_secret_candidates(other),
        )
