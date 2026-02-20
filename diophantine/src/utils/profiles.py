import json
import os


def _profiles_dir():
    """Return the profiles directory inside config/."""
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(here))
    return os.path.join(project_root, "config", "profiles")


def save_profile(name, settings):
    """Save a profile to config/profiles/{name}.json."""
    profiles_dir = _profiles_dir()
    os.makedirs(profiles_dir, exist_ok=True)
    path = os.path.join(profiles_dir, f"{name}.json")
    with open(path, "w") as f:
        json.dump(settings, f, indent=2)


def load_profile(name):
    """Load a profile by name. Returns dict or None."""
    path = os.path.join(_profiles_dir(), f"{name}.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def list_profiles():
    """Return a list of profile names."""
    profiles_dir = _profiles_dir()
    if not os.path.isdir(profiles_dir):
        return []
    names = []
    for f in sorted(os.listdir(profiles_dir)):
        if f.endswith(".json"):
            names.append(f[:-5])
    return names


def delete_profile(name):
    """Delete a profile by name."""
    path = os.path.join(_profiles_dir(), f"{name}.json")
    if os.path.isfile(path):
        os.remove(path)
