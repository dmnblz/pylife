# particle.py
import pygame

class Particle:
    """Point mass used in the Verlet based physics simulation.

    ``Particle`` can optionally track an orientation angle so that
    rotational constraints may be applied.  When ``orientation_enabled``
    is ``False`` the angular state is ignored and no torque is
    integrated.  The angle is measured in radians and, if enabled, is
    integrated using the same Verlet style as the positional variables.
    """

    def __init__(
        self,
        position,
        mass=1.0,
        color=None,
        radius=None,
        tag=None,
        *,
        angle: float = 0.0,
        orientation_enabled: bool = False,
    ):
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
        self.orientation_enabled = orientation_enabled

    def apply_force(self, force):
        if not self.fixed:
            self.acc += force / self.mass

    def apply_torque(self, torque: float):
        """Accumulate angular acceleration from a torque value."""
        if not self.fixed and self.orientation_enabled:
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

        if self.orientation_enabled:
            ang_vel = (self.angle - self.prev_angle) * damping
            new_angle = self.angle + ang_vel + self.ang_acc * dt * dt
            self.prev_angle = self.angle
            self.angle = new_angle
            self.ang_acc = 0.0
        else:
            self.prev_angle = self.angle
            self.ang_acc = 0.0
