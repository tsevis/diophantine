import contextlib
import json
import os
import re
import tempfile

_PROFILE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9 _-]{0,79}\Z")


def _profiles_dir():
    """Return the profiles directory inside config/."""
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(here))
    return os.path.join(project_root, "config", "profiles")


def _profile_path(name):
    """Resolve a validated profile name without permitting path traversal."""
    if not isinstance(name, str) or not _PROFILE_NAME.fullmatch(name):
        raise ValueError(
            "Profile names may contain letters, numbers, spaces, underscores, "
            "and hyphens only.")
    return os.path.join(_profiles_dir(), f"{name}.json")


def _write_json_private(path, content):
    """Atomically write user metadata with owner-only permissions."""
    directory = os.path.dirname(path)
    fd, temporary_path = tempfile.mkstemp(prefix=".profile-", dir=directory)
    try:
        if os.name != "nt":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(content, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    except Exception:
        with contextlib.suppress(OSError):
            os.close(fd)
        if os.path.exists(temporary_path):
            os.remove(temporary_path)
        raise


def save_profile(name, settings):
    """Save a profile to config/profiles/{name}.json."""
    profiles_dir = _profiles_dir()
    os.makedirs(profiles_dir, exist_ok=True)
    _write_json_private(_profile_path(name), settings)


def load_profile(name):
    """Load a profile by name. Returns dict or None."""
    try:
        path = _profile_path(name)
    except ValueError:
        return None
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
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
        if f.endswith(".json") and _PROFILE_NAME.fullmatch(f[:-5]):
            names.append(f[:-5])
    return names


def delete_profile(name):
    """Delete a profile by name."""
    path = _profile_path(name)
    if os.path.isfile(path):
        os.remove(path)
