# particle.py
import pygame

class Particle:
    """Point mass used in the Verlet based physics simulation.

    Parameters
    ----------
    position:
        Initial ``(x, y)`` coordinates.
    mass:
        Scalar mass value.
    color:
        Optional RGB tuple used when rendering.
    radius:
        Particle radius in pixels for drawing.
    tag:
        Arbitrary string label.
    orientation:
        Optional angle in radians for hinge particles.  ``None`` means the
        particle has no preferred orientation.
    """

    def __init__(self, position, mass=1.0, color=None, radius=None, tag=None, orientation=None):
        self.pos = pygame.Vector2(position)
        self.prev_pos = self.pos.copy()
        self.acc = pygame.Vector2(0, 0)
        self.mass = mass
        self.fixed = False
        self.color = color
        self.radius = radius
        self.tag = tag
        self.orientation = orientation

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
