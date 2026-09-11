import shutil
import zipfile

import pytest

from crypto.sevenz_engine import create_encrypted_7z, extract_encrypted_7z
from crypto.zip_engine import create_encrypted_zip, extract_encrypted_zip
from utils.safe_files import OutputCollisionError

pytestmark = pytest.mark.skipif(
    shutil.which("7z") is None and shutil.which("7zz") is None,
    reason="7-Zip is not installed",
)


@pytest.mark.parametrize(
    ("create", "extract", "archive_name"),
    [
        (create_encrypted_zip, extract_encrypted_zip, "archive.zip"),
        (create_encrypted_7z, extract_encrypted_7z, "archive.7z"),
    ],
)
def test_7z_backends_round_trip_without_password_argv(
        tmp_path, create, extract, archive_name):
    source = tmp_path / "source.txt"
    source.write_text("confidential test content", encoding="utf-8")
    archive = tmp_path / archive_name
    output = tmp_path / "output"

    create([str(source)], str(archive), "test-passphrase")
    extract(str(archive), str(output), "test-passphrase")

    assert (output / "source.txt").read_text(encoding="utf-8") == (
        "confidential test content")


def test_7z_backends_refuse_to_overwrite_existing_archive(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("input", encoding="utf-8")
    archive = tmp_path / "archive.7z"
    archive.write_text("existing", encoding="utf-8")

    with pytest.raises(OutputCollisionError):
        create_encrypted_7z([str(source)], str(archive), "test-passphrase")


@pytest.mark.parametrize(
    ("create", "extract", "archive_name"),
    [
        (create_encrypted_zip, extract_encrypted_zip, "archive.zip"),
        (create_encrypted_7z, extract_encrypted_7z, "archive.7z"),
    ],
)
def test_7z_backends_refuse_to_overwrite_extracted_files(
        tmp_path, create, extract, archive_name):
    source = tmp_path / "source.txt"
    source.write_text("encrypted source", encoding="utf-8")
    archive = tmp_path / archive_name
    output = tmp_path / "output"
    output.mkdir()
    existing = output / "source.txt"
    existing.write_text("preserve me", encoding="utf-8")

    create([str(source)], str(archive), "test-passphrase")

    with pytest.raises(OutputCollisionError):
        extract(str(archive), str(output), "test-passphrase")

    assert existing.read_text(encoding="utf-8") == "preserve me"


def test_zip_extraction_does_not_escape_its_staging_directory(tmp_path):
    archive = tmp_path / "malicious.zip"
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("../../outside.txt", "unsafe")

    output = tmp_path / "output"
    extract_encrypted_zip(str(archive), str(output), "unused")

    assert not (tmp_path / "outside.txt").exists()
    assert (output / "outside.txt").read_text(encoding="utf-8") == "unsafe"


def test_7z_backends_round_trip_repeatedly(tmp_path):
    """A single green run proved nothing while the handshake was racy.

    The password used to be written as soon as the prompt appeared, which won
    or lost a race with 7-Zip disabling terminal echo, so roughly four runs in
    five hung forever.  Repetition is the only thing that catches a regression.
    """
    for attempt in range(3):
        source = tmp_path / f"source-{attempt}.txt"
        source.write_text(f"round trip {attempt}", encoding="utf-8")
        archive = tmp_path / f"archive-{attempt}.7z"
        output = tmp_path / f"output-{attempt}"

        create_encrypted_7z([str(source)], str(archive), "test-passphrase")
        extract_encrypted_7z(str(archive), str(output), "test-passphrase")

        assert (output / source.name).read_text(encoding="utf-8") == (
            f"round trip {attempt}")


def test_7z_extraction_reports_a_rising_percentage(tmp_path):
    """7-Zip repaints its percentage with backspaces instead of newlines.

    The parser used to split the transcript on newlines alone, so the whole
    run collapsed into one "line" whose first percentage was the leading
    ``0%`` -- and the bar sat at zero from start to finish.  Only an archive
    with enough members to be reported in stages exercises that.
    """
    source = tmp_path / "bulk"
    source.mkdir()
    for index in range(200):
        (source / f"f{index:03d}.bin").write_bytes(bytes(index % 256) * 8192)
    archive = tmp_path / "bulk.7z"
    output = tmp_path / "output"
    reported = []

    create_encrypted_7z([str(source)], str(archive), "test-passphrase")
    extract_encrypted_7z(
        str(archive), str(output), "test-passphrase", reported.append)

    assert reported, "extraction reported no progress at all"
    assert max(reported) > 0.0, f"progress never left zero: {reported}"
    assert reported == sorted(reported), f"progress went backwards: {reported}"
