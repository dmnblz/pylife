

# bending_spring.py
import math
import pygame
from particle import Particle

class BendingSpring:
    """
    Applies a restoring torque to maintain the angle between three particles:
    p1 - p2 - p3 (p2 is the vertex).
    """

    def __init__(
        self, p1: Particle, p2: Particle, p3: Particle, rest_angle: float, stiffness: float
    ):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.rest_angle = rest_angle  # in radians
        self.stiffness = stiffness
        self.angle_factor = 0.0  # normalized deviation from rest angle

    def apply(self):
        # vectors from center p2
        v1 = self.p1.pos - self.p2.pos
        v2 = self.p3.pos - self.p2.pos

        # avoid division by zero if any arm is degenerate
        L1, L2 = v1.length(), v2.length()
        if L1 == 0 or L2 == 0:
            self.angle_factor = 0.0
            return

        # current angle between v1 and v2
        dot = max(-1.0, min(1.0, v1.dot(v2) / (L1 * L2)))
        theta = math.acos(dot)
        # angle deviation
        d_theta = theta - self.rest_angle
        self.angle_factor = (
            d_theta / self.rest_angle if abs(self.rest_angle) > 1e-6 else 0.0
        )
        if abs(d_theta) < 1e-6:
            return

        # compute force magnitude: F = -k * d_theta
        torque = -self.stiffness * d_theta

        # normals for v1 and v2
        # get unit vectors
        u1 = v1 / L1
        u2 = v2 / L2
        # perpendicular directions
        n1 = pygame.Vector2(-u1.y, u1.x)
        n2 = pygame.Vector2(u2.y, -u2.x)

        # forces applied at p1 and p3
        f1 = n1 * torque
        f3 = n2 * torque
        # apply equal and opposite at the vertex to conserve momentum
        f2 = -(f1 + f3)

        self.p1.apply_force(f1)
        self.p3.apply_force(f3)
        self.p2.apply_force(f2)

    def get_color(self):
        """Return a colour based on current angle strain."""
        # Define colour limits similar to linear springs
        max_stretch = 0.5
        max_compress = -0.3

        clamped = max(min(self.angle_factor, max_stretch), max_compress)
        if clamped > 0:
            red = 200 + int(55 * (clamped / max_stretch))
            green = 200 - int(200 * (clamped / max_stretch))
            blue = 200 - int(200 * (clamped / max_stretch))
        elif clamped < 0:
            red = 200 - int(200 * (clamped / max_compress))
            green = 200 - int(200 * (clamped / max_compress))
            blue = 200 + int(55 * (clamped / max_compress))
        else:
            red = green = blue = 200
        return (red, green, blue)
