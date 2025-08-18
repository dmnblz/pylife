"""Circular or sector sensors that trigger callbacks when objects enter view."""

import math
from typing import Callable, Iterable, Optional, Sequence

import pygame


class Sensor:
    """Detects objects within a radius and optional angular sector.

    Parameters
    ----------
    position:
        Centre of the sensor.
    forward:
        Direction the sensor faces. The vector is normalised internally.
    radius:
        Detection radius.
    half_angle:
        Half of the field of view in radians. ``math.pi`` covers a full circle.
    tags:
        Optional set of strings; if provided only objects whose ``tag``
        attribute matches one of them will trigger the sensor.
    """

    def __init__(
        self,
        position: Sequence[float],
        forward: Sequence[float] = (1, 0),
        radius: float = 1.0,
        half_angle: float = math.pi,
        tags: Optional[Iterable[str]] = None,
    ) -> None:
        self.pos = pygame.Vector2(position)
        self.forward = pygame.Vector2(forward).normalize()
        self.radius = float(radius)
        self.half_angle = float(half_angle)
        self.tags = set(tags) if tags else set()
        self.callbacks: list[Callable[["Sensor", object], None]] = []

    def add_callback(self, fn: Callable[["Sensor", object], None]) -> None:
        """Register a function called with ``(sensor, obj)`` when triggered."""

        self.callbacks.append(fn)

    def check(self, obj: object) -> None:
        """Trigger callbacks if *obj* satisfies the sensor conditions."""

        d = pygame.Vector2(obj.pos) - self.pos
        if d.length() > self.radius:
            return
        if self.half_angle < math.pi:
            if d.normalize().dot(self.forward) < math.cos(self.half_angle):
                return
        if self.tags and getattr(obj, "tag", None) not in self.tags:
            return
        for cb in self.callbacks:
            cb(self, obj)

    def scan(self, objects: Iterable[object]) -> None:
        """Run :meth:`check` on each object in *objects*."""

        for obj in objects:
            self.check(obj)
