import io
import shutil
import tarfile
import tempfile
from pathlib import Path

import pytest

from crypto.gpg_engine import (
    _gpg_passphrase_args,
    _safe_extract_tar,
    create_gpg_encrypted,
    extract_gpg_encrypted,
)


def test_gpg_uses_loopback_mode_for_passphrase_fd():
    args = _gpg_passphrase_args()

    assert args[args.index("--pinentry-mode") + 1] == "loopback"
    assert "--passphrase-fd" in args
    assert "--no-symkey-cache" in args


def test_tar_extraction_rejects_path_traversal(tmp_path):
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w") as tar:
        member = tarfile.TarInfo("../../outside.txt")
        content = b"unsafe"
        member.size = len(content)
        tar.addfile(member, io.BytesIO(content))

    archive.seek(0)
    with (tarfile.open(fileobj=archive, mode="r") as tar,
          pytest.raises(ValueError, match="Unsafe archive path")):
        _safe_extract_tar(tar, str(tmp_path / "destination"))

    assert not (tmp_path / "outside.txt").exists()


@pytest.mark.skipif(
    not (shutil.which("gpg") or shutil.which("gpg2")),
    reason="GnuPG is not installed",
)
def test_gpg_symmetric_round_trip_uses_loopback_password(tmp_path, monkeypatch):
    gpg_home = Path(tempfile.mkdtemp(prefix="gpg-", dir="/tmp"))
    try:
        monkeypatch.setenv("GNUPGHOME", str(gpg_home))
        source = tmp_path / "document.txt"
        source.write_text("confidential", encoding="utf-8")
        encrypted = tmp_path / "document.txt.gpg"

        try:
            create_gpg_encrypted([str(source)], str(encrypted), "correct horse")
        except RuntimeError as error:
            if "gpg-agent" in str(error):
                pytest.skip("The sandbox blocks GnuPG agent startup")
            raise
        extract_gpg_encrypted(
            str(encrypted), str(tmp_path / "output"), "correct horse")

        assert (tmp_path / "output" / "document.txt").read_text(
            encoding="utf-8") == "confidential"
    finally:
        shutil.rmtree(gpg_home, ignore_errors=True)


@pytest.mark.skipif(
    not (shutil.which("gpg") or shutil.which("gpg2")),
    reason="GnuPG is not installed",
)
def test_gpg_bundle_round_trip_decrypts_into_place(tmp_path, monkeypatch):
    """Several inputs become one ``.tar.gpg``, the app's multi-file path.

    Decryption used to hand GnuPG an output path that had already been
    created, and ``--batch`` without ``--yes`` refuses to overwrite, so every
    bundle failed with "handle plaintext failed: File exists".
    """
    gpg_home = Path(tempfile.mkdtemp(prefix="gpg-", dir="/tmp"))
    try:
        monkeypatch.setenv("GNUPGHOME", str(gpg_home))
        first = tmp_path / "first.txt"
        second = tmp_path / "second.txt"
        first.write_text("alpha", encoding="utf-8")
        second.write_text("beta", encoding="utf-8")
        encrypted = tmp_path / "bundle.tar.gpg"

        try:
            create_gpg_encrypted(
                [str(first), str(second)], str(encrypted), "correct horse",
                single_archive=True)
        except RuntimeError as error:
            if "gpg-agent" in str(error):
                pytest.skip("The sandbox blocks GnuPG agent startup")
            raise

        output = tmp_path / "output"
        extract_gpg_encrypted(str(encrypted), str(output), "correct horse")

        assert (output / "first.txt").read_text(encoding="utf-8") == "alpha"
        assert (output / "second.txt").read_text(encoding="utf-8") == "beta"
    finally:
        shutil.rmtree(gpg_home, ignore_errors=True)


@pytest.mark.skipif(
    not (shutil.which("gpg") or shutil.which("gpg2")),
    reason="GnuPG is not installed",
)
def test_gpg_bundle_leaves_no_plaintext_tar_behind(tmp_path, monkeypatch):
    gpg_home = Path(tempfile.mkdtemp(prefix="gpg-", dir="/tmp"))
    try:
        monkeypatch.setenv("GNUPGHOME", str(gpg_home))
        source = tmp_path / "first.txt"
        source.write_text("alpha", encoding="utf-8")
        encrypted = tmp_path / "bundle.tar.gpg"

        try:
            create_gpg_encrypted(
                [str(source)], str(encrypted), "correct horse",
                single_archive=True)
        except RuntimeError as error:
            if "gpg-agent" in str(error):
                pytest.skip("The sandbox blocks GnuPG agent startup")
            raise

        output = tmp_path / "output"
        extract_gpg_encrypted(str(encrypted), str(output), "correct horse")

        assert sorted(path.name for path in output.iterdir()) == ["first.txt"]
        assert not list(tmp_path.glob("**/*.tar"))
    finally:
        shutil.rmtree(gpg_home, ignore_errors=True)
