"""Bending spring variant with a second rest angle controlled by a key press."""

from __future__ import annotations

import math

from bending_spring import BendingSpring
from channel import ChannelControlled


class VariableBendingSpring(BendingSpring, ChannelControlled):
    """A bending spring that can smoothly switch between two angles.

    The bend behaves like a regular :class:`~bending_spring.BendingSpring` but
    tracks an alternate ``alt_angle``. When its assigned key is activated the
    rest angle transitions toward this alternate value at ``change_speed``.
    Two input modes are supported:

    ``hold``
        The key must be held down for the alternate angle to be active.
    ``toggle``
        Pressing the key toggles between the normal and alternate angles.
    """

    def __init__(
        self,
        p1,
        p2,
        p3,
        angle: float,
        alt_angle: float,
        stiffness: float,
        *,
        key: int | None = None,
        mode: str = "hold",
        change_speed: float = math.radians(240.0),
        channel: int | None = None,
    ):
        """Create a variable bending spring for the particle trio.

        Parameters
        ----------
        p1, p2, p3:
            Particles forming the bend, with ``p2`` as the vertex.
        angle:
            Default rest angle in radians.
        alt_angle:
            Rest angle when the bend is activated.
        stiffness:
            Resistance to deviation from the rest angle.
        key:
            Keyboard key that activates the alternate angle. ``None`` disables
            key control.
        mode:
            ``"hold"`` for hold‑to‑activate behaviour or ``"toggle"`` for
            press‑to‑toggle.
        change_speed:
            Rate in **radians per second** at which the bend moves toward the
            target angle.
        """

        super().__init__(p1, p2, p3, angle, stiffness)
        self.base_angle = angle
        self.alt_angle = alt_angle
        self.key = key
        self.mode = mode
        self.change_speed = change_speed
        self.key_active = False
        self.channel_active = False
        self.active = False
        self.channel: int | None = channel

    def on_keydown(self) -> None:
        """Handle a ``KEYDOWN`` event for the bend's control key."""
        if self.mode == "hold":
            self.key_active = True
        elif self.mode == "toggle":
            self.key_active = not self.key_active
        self.active = self.key_active or self.channel_active

    def on_keyup(self) -> None:
        """Handle a ``KEYUP`` event for the bend's control key."""
        if self.mode == "hold":
            self.key_active = False
        self.active = self.key_active or self.channel_active

    def update(self, dt: float) -> None:
        """Move the rest angle toward the active target at ``change_speed``."""
        target = self.alt_angle if self.active else self.base_angle
        if self.rest_angle < target:
            self.rest_angle = min(target, self.rest_angle + self.change_speed * dt)
        elif self.rest_angle > target:
            self.rest_angle = max(target, self.rest_angle - self.change_speed * dt)

    def set_channel_active(self, state: bool) -> None:
        """Update the channel-driven activation state."""
        self.channel_active = state
        self.active = self.key_active or self.channel_active

    def set_base_angle(self, value: float) -> None:
        """Set the default rest angle (radians)."""
        self.base_angle = max(0.0, value)
        if not self.active:
            self.rest_angle = self.base_angle

    def set_alt_angle(self, value: float) -> None:
        """Set the alternate rest angle (radians)."""
        self.alt_angle = max(0.0, value)
        if self.active:
            self.rest_angle = self.alt_angle
