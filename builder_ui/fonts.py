"""Font helpers with caching to avoid file descriptor leaks.

Uses the bundled Roboto font for all text rendering."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pygame


_FONT_PATH = Path(__file__).with_name("Roboto-Regular.ttf")


@lru_cache(maxsize=None)
def get_font(size: int) -> pygame.font.Font:
    """Return a cached Roboto font of the given size."""
    return pygame.font.Font(str(_FONT_PATH), size)
