import json
import os

DEFAULT_PREFERENCES = {
    "output_directory": "",
    "encryption_method": "zip",
    "naming_scheme": "original",
    "theme": "system",
}


def _config_dir():
    """Return the config directory inside the project root."""
    # Go from src/utils/ up to the project root
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(here))
    return os.path.join(project_root, "config")


def load_preferences():
    """Load preferences from config/preferences.json, merged with defaults."""
    path = os.path.join(_config_dir(), "preferences.json")
    prefs = dict(DEFAULT_PREFERENCES)
    if os.path.isfile(path):
        try:
            with open(path, "r") as f:
                saved = json.load(f)
            prefs.update(saved)
        except (json.JSONDecodeError, OSError):
            pass
    return prefs


def save_preferences(prefs):
    """Save preferences to config/preferences.json."""
    config_dir = _config_dir()
    os.makedirs(config_dir, exist_ok=True)
    path = os.path.join(config_dir, "preferences.json")
    with open(path, "w") as f:
        json.dump(prefs, f, indent=2)
