# particle.py
import pygame

class Particle:
    """Point mass used in the Verlet based physics simulation.

    ``Particle`` now tracks an orientation angle in addition to its
    translational state so that angular constraints can be implemented.
    The angle is measured in radians and integrated using the same
    Verlet style as the position variables.
    """

    def __init__(self, position, mass=1.0, color=None, radius=None, tag=None,
                 angle: float = 0.0):
        self.pos = pygame.Vector2(position)
        self.prev_pos = self.pos.copy()
        self.acc = pygame.Vector2(0, 0)
        self.mass = mass
        self.fixed = False
        self.color = color
        self.radius = radius
        self.tag = tag
        self.angle = angle
        self.prev_angle = angle
        self.ang_acc = 0.0

    def apply_force(self, force):
        if not self.fixed:
            self.acc += force / self.mass

    def apply_torque(self, torque: float):
        """Accumulate angular acceleration from a torque value."""
        if not self.fixed:
            # moment of inertia is approximated by the mass
            self.ang_acc += torque / self.mass

    def integrate(self, dt, damping=0.98):
        if self.fixed:
            return
        # Verlet integration
        velocity = (self.pos - self.prev_pos) * damping
        new_pos = self.pos + velocity + self.acc * dt * dt
        self.prev_pos = self.pos.copy()
        self.pos = new_pos
        self.acc = pygame.Vector2(0, 0)

        ang_vel = (self.angle - self.prev_angle) * damping
        new_angle = self.angle + ang_vel + self.ang_acc * dt * dt
        self.prev_angle = self.angle
        self.angle = new_angle
        self.ang_acc = 0.0
