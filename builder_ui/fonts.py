"""Font helpers with caching to avoid file descriptor leaks."""

from __future__ import annotations

from functools import lru_cache

import pygame


@lru_cache(maxsize=None)
def get_font(size: int) -> pygame.font.Font:
    """Return a cached default pygame font of the given size."""
    return pygame.font.Font(None, size)
