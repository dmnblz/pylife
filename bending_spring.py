

# bending_spring.py
import math
import pygame
from particle import Particle

class BendingSpring:
    """
    Applies a restoring torque to maintain the angle between three particles:
    p1 - p2 - p3 (p2 is the vertex).
    """
    def __init__(self, p1: Particle, p2: Particle, p3: Particle,
                 rest_angle: float, stiffness: float):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.rest_angle = rest_angle  # in radians
        self.stiffness = stiffness

    # simple implementation
    def apply(self):
        # vectors from center p2
        v1 = self.p1.pos - self.p2.pos
        v2 = self.p3.pos - self.p2.pos
        # current angle between v1 and v2
        dot = max(-1.0, min(1.0, v1.dot(v2) / (v1.length() * v2.length())))
        theta = math.acos(dot)
        # angle deviation
        d_theta = theta - self.rest_angle
        if abs(d_theta) < 1e-6:
            return

        # compute force magnitude: F = -k * d_theta
        torque = -self.stiffness * d_theta

        # normals for v1 and v2
        # get unit vectors
        u1 = v1.normalize()
        u2 = v2.normalize()
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

    # def apply(self):
    #     v1 = self.p1.pos - self.p2.pos
    #     v2 = self.p3.pos - self.p2.pos
    #     L1, L2 = v1.length(), v2.length()
    #     if L1 == 0 or L2 == 0:
    #         return
    #
    #     # signed angle between v1 and v2
    #     cross_z = v1.x*v2.y - v1.y*v2.x
    #     dot     = max(-1.0, min(1.0, v1.dot(v2)/(L1*L2)))
    #     signed_theta = math.atan2(cross_z, dot)
    #
    #     # deviation from rest
    #     d_theta = signed_theta - self.rest_angle
    #     if abs(d_theta) < 1e-6:
    #         return
    #
    #     # torque → forces
    #     torque = -self.stiffness * d_theta
    #     u1, u2 = v1 / L1, v2 / L2
    #     # perpendicular normals
    #     n1 = pygame.Vector2(-u1.y, u1.x)
    #     n2 = pygame.Vector2(u2.y, -u2.x)
    #     f1 = n1 * torque
    #     f3 = n2 * torque
    #     f2 = -(f1 + f3)
    #
    #     self.p1.apply_force(f1)
    #     self.p3.apply_force(f3)
    #     self.p2.apply_force(f2)