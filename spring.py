# spring.py
import pygame
from particle import Particle

class Spring:
    def __init__(self, p1: Particle, p2: Particle, rest_length: float, stiffness: float):
        self.p1 = p1
        self.p2 = p2
        self.rest_length = rest_length
        self.stiffness = stiffness

    def apply(self):
        delta = self.p2.pos - self.p1.pos
        dist = delta.length()
        if dist == 0:
            return
        # Hooke's law force
        diff = (dist - self.rest_length) / dist
        force = delta * (self.stiffness * diff * 0.5)
        self.p1.apply_force(force)
        self.p2.apply_force(-force)

    def potential_energy(self):
        return 0.5 * self.stiffness * ((self.p2.pos - self.p1.pos).length() - self.rest_length) ** 2