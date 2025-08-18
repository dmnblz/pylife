"""Sensor-enabled particle detecting objects within a sector or radius."""

from __future__ import annotations

import math
from typing import Callable, Iterable, Optional, Sequence

import pygame

from particle import Particle


class SensorParticle(Particle):
    """Particle that triggers callbacks when objects enter its view.

    Parameters
    ----------
    position:
        Initial coordinates of the particle.
    forward:
        Direction the sensor faces. The vector is normalised internally.
    sense_radius:
        Detection radius in world units.
    half_angle:
        Half of the field of view in radians. ``math.pi`` covers a full circle.
    tags:
        Optional set of strings limiting which objects trigger the sensor.
    """

    def __init__(
        self,
        position: Sequence[float],
        *,
        forward: Sequence[float] = (1, 0),
        sense_radius: float = 1.0,
        half_angle: float = math.pi,
        tags: Optional[Iterable[str]] = None,
        mass: float = 1.0,
        color=None,
        radius: float | None = None,
        tag=None,
        drag: float = 1.0,
        elasticity: float = 1.0,
        trail_length: int = 40,
    ) -> None:
        super().__init__(
            position,
            mass=mass,
            color=color,
            radius=radius,
            tag=tag,
            drag=drag,
            elasticity=elasticity,
            trail_length=trail_length,
        )
        self.forward = pygame.Vector2(forward).normalize()
        self.sense_radius = float(sense_radius)
        self.half_angle = float(half_angle)
        self.tags = set(tags) if tags else set()
        self.callbacks: list[Callable[["SensorParticle", object], None]] = []

    def add_callback(self, fn: Callable[["SensorParticle", object], None]) -> None:
        """Register a function called with ``(sensor, obj)`` when triggered."""

        self.callbacks.append(fn)

    def check(self, obj: object) -> None:
        """Trigger callbacks if *obj* satisfies the sensor conditions."""

        d = pygame.Vector2(obj.pos) - self.pos
        if d.length() > self.sense_radius:
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
