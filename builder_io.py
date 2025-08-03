"""Helper functions for saving and loading builder scenes."""

from __future__ import annotations

import json
from file_dialog import choose_open_path, choose_save_path


def save_state(path: str, state: dict) -> None:
    """Write *state* to *path* as JSON."""
    with open(path, "w") as fh:
        json.dump(state, fh, indent=2)


def load_state(path: str) -> dict:
    """Return scene state loaded from *path*."""
    with open(path, "r") as fh:
        return json.load(fh)


def save_state_dialog(state: dict) -> None:
    """Prompt for a path and save *state* if one is chosen."""
    path = choose_save_path("scene.json")
    if path:
        save_state(path, state)


def load_state_dialog() -> dict | None:
    """Prompt for a path and return the loaded scene state."""
    path = choose_open_path()
    if path:
        return load_state(path)
    return None
