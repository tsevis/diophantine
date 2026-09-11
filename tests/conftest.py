"""Shared pytest configuration.

Two jobs:

1. Make ``src/`` importable so tests can ``from utils import ...`` the way the
   application does.
2. Keep tests that open real windows out of the default run. They are marked
   ``gui`` automatically, from the fixtures they request, rather than relying on
   each new test remembering to carry ``@pytest.mark.gui``. ``addopts`` in
   pyproject.toml then excludes them with ``-m "not gui"``.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Fixtures that put a real window on the developer's screen. Add new ones here;
# every test requesting one is marked ``gui`` by the hook below.
GUI_FIXTURES = frozenset({"tk_root"})


def pytest_collection_modifyitems(items):
    """Mark every test that requests a GUI fixture with ``gui``."""
    for item in items:
        if GUI_FIXTURES.intersection(getattr(item, "fixturenames", ())):
            item.add_marker(pytest.mark.gui)


@pytest.fixture
def tk_root():
    """A real Tk root window.

    Requesting this fixture marks the test ``gui``, so it never runs in a plain
    ``pytest`` invocation -- only under an explicit ``pytest -m gui``.
    """
    tkinter = pytest.importorskip("tkinter")
    root = tkinter.Tk()
    try:
        yield root
    finally:
        root.destroy()
