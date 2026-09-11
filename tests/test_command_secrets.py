import pytest

from crypto import sevenz_engine, veracrypt_engine, zip_engine


@pytest.mark.parametrize("engine", [zip_engine, sevenz_engine])
def test_7z_password_is_not_part_of_the_command(tmp_path, monkeypatch, engine):
    source = tmp_path / "source.txt"
    source.write_text("input", encoding="utf-8")
    archive = tmp_path / "archive"
    secret = "never-in-argv"
    captured = {}

    monkeypatch.setattr(engine, "_find_7z", lambda: "7z")
    monkeypatch.setattr(
        engine,
        "run_password_prompted",
        lambda command, password, **kwargs: captured.update(
            command=command, password=password) or (0, ""),
    )

    engine.create_encrypted_7z(
        [str(source)], str(archive), secret) if engine is sevenz_engine else (
        engine.create_encrypted_zip([str(source)], str(archive), secret))

    assert secret == captured["password"]
    assert all(secret not in argument for argument in captured["command"])


def test_veracrypt_password_is_not_part_of_the_command(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    source.write_text("input", encoding="utf-8")
    container = tmp_path / "vault.hc"
    secret = "never-in-argv"
    captured = []

    monkeypatch.setattr(veracrypt_engine, "_find_veracrypt", lambda: "veracrypt")
    monkeypatch.setattr(
        veracrypt_engine,
        "_run_veracrypt",
        lambda command, password=None, **kwargs: captured.append(
            (command, password)),
    )

    veracrypt_engine.create_veracrypt_container(
        [str(source)], str(container), secret, size_mb=10)

    assert [password for _, password in captured[:2]] == [secret, secret]
    assert all(
        secret not in argument
        for command, _ in captured
        for argument in command
    )
    assert captured[-1][0][2] == "--dismount"
    assert captured[-1][0][-1] != "-d"


def test_unmount_requires_an_explicit_mount_directory(monkeypatch):
    """Unmounting everything would dismount volumes this app never mounted."""
    monkeypatch.setattr(veracrypt_engine, "_find_veracrypt", lambda: "veracrypt")
    monkeypatch.setattr(
        veracrypt_engine, "_run_veracrypt",
        lambda *args, **kwargs: pytest.fail("should not have run"))

    with pytest.raises(TypeError):
        veracrypt_engine.unmount_veracrypt_container()

    with pytest.raises(ValueError, match="mount directory is required"):
        veracrypt_engine.unmount_veracrypt_container("")


def test_unmount_dismounts_only_the_directory_it_is_given(monkeypatch):
    captured = []
    monkeypatch.setattr(veracrypt_engine, "_find_veracrypt", lambda: "veracrypt")
    monkeypatch.setattr(
        veracrypt_engine, "_run_veracrypt",
        lambda command, *args, **kwargs: captured.append(command))

    veracrypt_engine.unmount_veracrypt_container("/Volumes/vault")

    assert captured == [["veracrypt", "--text", "--dismount", "/Volumes/vault"]]
