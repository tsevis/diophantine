import pytest

from utils import profiles


def test_profile_names_cannot_escape_profiles_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(profiles, "_profiles_dir", lambda: str(tmp_path))

    with pytest.raises(ValueError):
        profiles.save_profile("../outside", {"encryption_method": "7z"})

    assert not (tmp_path.parent / "outside.json").exists()


def test_profile_round_trip_uses_validated_name(tmp_path, monkeypatch):
    monkeypatch.setattr(profiles, "_profiles_dir", lambda: str(tmp_path))
    settings = {"encryption_method": "7z"}

    profiles.save_profile("Daily Backup", settings)

    assert profiles.load_profile("Daily Backup") == settings
    assert profiles.list_profiles() == ["Daily Backup"]
