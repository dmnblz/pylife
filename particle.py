"""Verlet-integrated point mass with per-particle drag."""

import pygame

class Particle:
    """Point mass used in the Verlet based physics simulation.

    Parameters
    ----------
    position:
        Initial particle coordinates.
    mass:
        Particle mass in arbitrary units.
    color:
        Optional RGB colour for rendering.
    radius:
        Optional drawing radius.
    tag:
        Optional label used by higher level helpers.
    drag:
        Multiplier applied to the global damping coefficient. ``1``
        represents normal drag while higher values increase resistance.
    elasticity:
        Coefficient ``e`` in the range 0–1 determining how much the
        particle bounces during collisions.
    """

    def __init__(
        self,
        position,
        mass: float = 1.0,
        color=None,
        radius=None,
        tag=None,
        drag: float = 1.0,
        elasticity: float = 1.0,
    ):
        self.pos = pygame.Vector2(position)
        self.prev_pos = self.pos.copy()
        self.acc = pygame.Vector2(0, 0)
        self.mass = mass
        self.fixed = False
        self.color = color
        self.radius = radius
        self.tag = tag
        self.drag = drag
        self.elasticity = elasticity

    def apply_force(self, force):
        if not self.fixed:
            self.acc += force / self.mass

    def integrate(self, dt, damping=0.98):
        if self.fixed:
            return
        # Verlet integration
        velocity = (self.pos - self.prev_pos) * damping
        new_pos = self.pos + velocity + self.acc * dt * dt
        self.prev_pos = self.pos.copy()
        self.pos = new_pos
        self.acc = pygame.Vector2(0, 0)
