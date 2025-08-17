"""Particle variant with a user-controlled drag coefficient."""

from __future__ import annotations

from particle import Particle


class VariableParticle(Particle):
    """A particle that can smoothly switch between two drag values.

    The particle behaves like a standard :class:`~particle.Particle` but
    tracks an alternate ``alt_drag`` value. When its assigned key is
    activated the particle transitions toward this drag at
    ``change_speed``. Two input modes are supported:

    ``hold``
        The key must remain pressed for the alternate drag to apply.
    ``toggle``
        Pressing the key toggles between the base and alternate drags.

    Parameters are identical to :class:`~particle.Particle` with the
    addition of ``base_drag``, ``alt_drag`` and ``change_speed``. The
    ``trail_length`` sets the maximum history stored when trails are
    enabled.
    """

    def __init__(
        self,
        position,
        mass: float = 1.0,
        color=None,
        radius: float | None = None,
        *,
        base_drag: float = 1.0,
        alt_drag: float = 100.0,
        key: int | None = None,
        mode: str = "hold",
        change_speed: float = 240.0,
        elasticity: float = 1.0,
        trail_length: int = 40,
    ):
        super().__init__(
            position,
            mass=mass,
            color=color,
            radius=radius,
            drag=base_drag,
            elasticity=elasticity,
            trail_length=trail_length,
        )
        self.base_drag = base_drag
        self.alt_drag = alt_drag
        self.key = key
        self.mode = mode
        self.change_speed = change_speed
        self.active = False

    def on_keydown(self) -> None:
        """React to a ``KEYDOWN`` event for the particle's control key."""
        if self.mode == "hold":
            self.active = True
        elif self.mode == "toggle":
            self.active = not self.active

    def on_keyup(self) -> None:
        """React to a ``KEYUP`` event for the particle's control key."""
        if self.mode == "hold":
            self.active = False

    def update(self, dt: float) -> None:
        """Move the drag value toward the active target."""
        target = self.alt_drag if self.active else self.base_drag
        if self.drag < target:
            self.drag = min(target, self.drag + self.change_speed * dt)
        elif self.drag > target:
            self.drag = max(target, self.drag - self.change_speed * dt)
