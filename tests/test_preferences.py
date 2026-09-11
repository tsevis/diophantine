"""Preference loading and atomic saving.

Every test redirects the config directory: the real one lives in the project
tree and holds the developer's own settings.
"""

import json
import os
import stat

import pytest

from utils import preferences
from utils.preferences import (
    DEFAULT_PREFERENCES,
    load_preferences,
    save_preferences,
)


@pytest.fixture
def config_dir(tmp_path, monkeypatch):
    directory = tmp_path / "config"
    directory.mkdir()
    monkeypatch.setattr(preferences, "_config_dir", lambda: str(directory))
    return directory


def test_defaults_are_returned_when_nothing_has_been_saved(config_dir):
    assert load_preferences() == DEFAULT_PREFERENCES


def test_loading_does_not_hand_back_the_shared_defaults_object(config_dir):
    first = load_preferences()
    first["theme"] = "mutated"

    assert load_preferences()["theme"] == DEFAULT_PREFERENCES["theme"]
    assert DEFAULT_PREFERENCES["theme"] != "mutated"


def test_saved_values_survive_a_round_trip(config_dir):
    save_preferences({**DEFAULT_PREFERENCES, "theme": "light",
                      "encryption_method": "gpg"})

    loaded = load_preferences()

    assert loaded["theme"] == "light"
    assert loaded["encryption_method"] == "gpg"


def test_a_partial_file_is_merged_over_the_defaults(config_dir):
    (config_dir / "preferences.json").write_text(
        json.dumps({"theme": "light"}), encoding="utf-8")

    loaded = load_preferences()

    assert loaded["theme"] == "light"
    assert loaded["naming_scheme"] == DEFAULT_PREFERENCES["naming_scheme"]


def test_a_corrupt_file_falls_back_to_the_defaults(config_dir):
    (config_dir / "preferences.json").write_text("{not json", encoding="utf-8")

    assert load_preferences() == DEFAULT_PREFERENCES


def test_saved_preferences_are_readable_only_by_their_owner(config_dir):
    save_preferences(dict(DEFAULT_PREFERENCES))

    mode = os.stat(config_dir / "preferences.json").st_mode
    assert stat.S_IMODE(mode) == 0o600


def test_saving_leaves_no_temporary_file_behind(config_dir):
    save_preferences(dict(DEFAULT_PREFERENCES))
    save_preferences({**DEFAULT_PREFERENCES, "theme": "light"})

    assert sorted(path.name for path in config_dir.iterdir()) == [
        "preferences.json"]


def test_a_failed_save_neither_clears_the_previous_file_nor_leaves_debris(
        config_dir, monkeypatch):
    save_preferences({**DEFAULT_PREFERENCES, "theme": "light"})

    def explode(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(preferences.json, "dump", explode)
    with pytest.raises(OSError, match="disk full"):
        save_preferences({**DEFAULT_PREFERENCES, "theme": "dark"})

    assert load_preferences()["theme"] == "light"
    assert sorted(path.name for path in config_dir.iterdir()) == [
        "preferences.json"]
