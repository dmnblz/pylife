"""Camera controller for world/screen transforms.

This class centralises camera state and common operations like
zooming around a point, panning and rotating around a pivot. It
does not own rendering; instead it pushes camera state to the
``renderer`` when values change.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
import pygame
import math


@dataclass
class CameraState:
    offset: pygame.Vector2
    zoom: float
    angle: float


class CameraController:
    def __init__(self, renderer: "Renderer", *,
                 offset: Tuple[float, float] = (0.0, 0.0),
                 zoom: float = 1.0,
                 angle: float = 0.0) -> None:
        self.renderer = renderer
        self.state = CameraState(pygame.Vector2(offset), float(zoom), float(angle))
        self._sync()

    # basic state ------------------------------------------------------
    @property
    def offset(self) -> pygame.Vector2:
        return self.state.offset

    @property
    def zoom(self) -> float:
        return self.state.zoom

    @property
    def angle(self) -> float:
        return self.state.angle

    def set(self, *, offset: pygame.Vector2 | None = None, zoom: float | None = None, angle: float | None = None) -> None:
        if offset is not None:
            self.state.offset = pygame.Vector2(offset)
        if zoom is not None:
            self.state.zoom = max(0.1, min(10.0, float(zoom)))
        if angle is not None:
            self.state.angle = float(angle)
        self._sync()

    def _sync(self) -> None:
        self.renderer.set_camera(self.state.offset, self.state.zoom, self.state.angle)

    # operations -------------------------------------------------------
    def zoom_at_screen(self, factor: float, screen_pos: Tuple[int, int]) -> None:
        """Zoom by ``factor`` anchored at ``screen_pos`` (pixels)."""
        old_zoom = self.state.zoom
        new_zoom = max(0.1, min(10.0, old_zoom * factor))
        if new_zoom == old_zoom:
            return
        # keep anchor stable in world space
        before = self.renderer.screen_to_world(screen_pos)
        self.state.zoom = new_zoom
        self._sync()
        after = self.renderer.screen_to_world(screen_pos)
        self.state.offset += (before - after)
        self._sync()

    def pan_screen_delta(self, rel_px: Tuple[float, float]) -> None:
        """Pan by a screen-space delta in pixels, accounting for zoom and rotation."""
        rel = pygame.Vector2(rel_px) / self.state.zoom
        c = math.cos(self.state.angle)
        s = math.sin(self.state.angle)
        world_rel = pygame.Vector2(c * rel.x + s * rel.y, -s * rel.x + c * rel.y)
        self.state.offset -= world_rel
        self._sync()

    def rotate_around_point(self, delta_angle: float, world_pivot: pygame.Vector2) -> None:
        """Rotate camera around ``world_pivot`` by ``delta_angle`` radians."""
        v = pygame.Vector2(world_pivot) - self.state.offset
        c = math.cos(delta_angle)
        s = math.sin(delta_angle)
        v_rot = pygame.Vector2(c * v.x + s * v.y, -s * v.x + c * v.y)
        self.state.offset = pygame.Vector2(world_pivot) - v_rot
        self.state.angle += delta_angle
        self._sync()

    def fit_world_rect(self, rect: pygame.Rect, screen_size: Tuple[int, int], *, padding: int = 24) -> None:
        """Fit camera view around a world-space ``rect`` with screen ``screen_size``.

        Padding is in screen pixels.
        """
        if rect.width <= 0 or rect.height <= 0:
            return
        sw, sh = screen_size
        if sw <= 0 or sh <= 0:
            return
        # ignore rotation for fit; compute uniform zoom
        zx = (sw - 2 * padding) / max(1.0, rect.width)
        zy = (sh - 2 * padding) / max(1.0, rect.height)
        z = max(0.1, min(10.0, min(zx, zy)))
        self.state.zoom = z
        # center the rect
        center = pygame.Vector2(rect.center)
        self.state.offset = center - pygame.Vector2(sw / (2 * z), sh / (2 * z))
        self._sync()
