"""Font helpers with caching to avoid file descriptor leaks."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pygame


@lru_cache(maxsize=None)
def get_font(size: int) -> pygame.font.Font:
    """Return a cached default pygame font of the given size."""
    default = Path(pygame.__file__).with_name(pygame.font.get_default_font())
    return pygame.font.Font(str(default), size)
