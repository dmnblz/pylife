# hinge.py
"""Orientation constraint for particles acting like rigid hinges.

This module defines :class:`HingeSpring` which keeps the angle between
an oriented particle and another particle constant.  The hinge does not
have its own rotational inertia; instead equal and opposite forces are
applied to the two connected particles.
"""

import math
import pygame
from particle import Particle


class HingeSpring:
    """Constrain the angle between two particles around a hinge."""

    def __init__(self, base: Particle, other: Particle, rest_angle: float, stiffness: float):
        self.base = base
        self.other = other
        self.rest_angle = rest_angle
        self.stiffness = stiffness

    def apply(self):
        if self.base.orientation is None:
            return
        v = self.other.pos - self.base.pos
        length = v.length()
        if length == 0:
            return
        dir_v = v / length
        target = pygame.Vector2(
            math.cos(self.base.orientation + self.rest_angle),
            math.sin(self.base.orientation + self.rest_angle),
        )
        dot = max(-1.0, min(1.0, target.dot(dir_v)))
        cross_z = target.x * dir_v.y - target.y * dir_v.x
        d_theta = math.atan2(cross_z, dot)
        if abs(d_theta) < 1e-6:
            return
        torque = -self.stiffness * d_theta
        normal = pygame.Vector2(-dir_v.y, dir_v.x)
        force = normal * torque
        self.other.apply_force(force)
        self.base.apply_force(-force)
