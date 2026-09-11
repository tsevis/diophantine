import json
import os
import tempfile

DEFAULT_PREFERENCES = {
    "output_directory": "",
    "encryption_method": "7z",
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
    fd, temporary_path = tempfile.mkstemp(prefix=".preferences-", dir=config_dir)
    try:
        if os.name != "nt":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(prefs, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        if os.path.exists(temporary_path):
            os.remove(temporary_path)
        raise
