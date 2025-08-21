"""Spring variant with a second rest length controlled by a key press."""

from __future__ import annotations

import pygame
from spring import Spring
from channel import ChannelControlled


class VariableSpring(Spring, ChannelControlled):
    """A spring that can smoothly switch between two rest lengths.

    The spring behaves like a regular :class:`~spring.Spring` but tracks a
    second ``alt_rest_length``.  When its assigned key is activated the spring
    transitions toward this alternate rest length at ``change_speed``.  Two
    input modes are supported:

    ``hold``
        The key must be held down for the alternate length to be active.
    ``toggle``
        Pressing the key toggles between the normal and alternate lengths.
    """

    def __init__(
        self,
        p1,
        p2,
        rest_length: float,
        alt_rest_length: float,
        stiffness: float,
        *,
        key: int | None = None,
        mode: str = "hold",
        change_speed: float = 240.0,
        channel: int | None = None,
        max_force: float | None = None,
        invisible: bool = False,
    ):
        """Create a variable spring between ``p1`` and ``p2``.

        Parameters
        ----------
        p1, p2:
            Particles connected by the spring.
        rest_length:
            Default rest length of the spring.
        alt_rest_length:
            Rest length when the spring is activated.
        stiffness:
            Hooke's law stiffness coefficient.
        key:
            Keyboard key that activates the alternate length. ``None`` disables
            key control.
        mode:
            ``"hold"`` for a hold‑to‑activate behaviour or ``"toggle"`` for
            press‑to‑toggle.
        change_speed:
            Rate at which the spring moves toward the target rest length in
            pixels per second.
        max_force:
            Optional break force threshold.
        invisible:
            If ``True`` the spring will not be rendered.
        """

        super().__init__(p1, p2, rest_length, stiffness, max_force, invisible)
        self.base_rest_length = rest_length
        self.alt_rest_length = alt_rest_length
        self.key = key
        self.mode = mode
        self.change_speed = change_speed
        self.key_active = False
        self.channel_active = False
        self.active = False
        self.channel: int | None = channel

    def on_keydown(self):
        """Handle a ``KEYDOWN`` event for the spring's control key."""
        if self.mode == "hold":
            self.key_active = True
        elif self.mode == "toggle":
            self.key_active = not self.key_active
        self.active = self.key_active or self.channel_active

    def on_keyup(self):
        """Handle a ``KEYUP`` event for the spring's control key."""
        if self.mode == "hold":
            self.key_active = False
        self.active = self.key_active or self.channel_active

    def update(self, dt: float):
        """Move the rest length toward the active target at ``change_speed``."""
        target = self.alt_rest_length if self.active else self.base_rest_length
        if self.rest_length < target:
            self.rest_length = min(target, self.rest_length + self.change_speed * dt)
        elif self.rest_length > target:
            self.rest_length = max(target, self.rest_length - self.change_speed * dt)

    def set_channel_active(self, state: bool) -> None:
        """Update the channel-driven activation state."""
        self.channel_active = state
        self.active = self.key_active or self.channel_active

    # --- helpers used by the inspector
    def set_base_rest_length(self, value: float) -> None:
        """Set the default rest length of the spring."""
        self.base_rest_length = max(1, value)
        if not self.active:
            self.rest_length = self.base_rest_length

    def set_alt_rest_length(self, value: float) -> None:
        """Set the alternate rest length activated by the key."""
        self.alt_rest_length = max(1, value)
        if self.active:
            self.rest_length = self.alt_rest_length
