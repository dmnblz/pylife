# physics.py
import pygame
from particle import Particle
from spring import Spring
from bending_spring import BendingSpring
import random
import math

class PhysicsEngine:
    def __init__(self, particles: list[Particle], springs: list[Spring], bending_springs: list[BendingSpring]=None, gravity=(0, 0), repulsion_radius=20,
                 repulsion_strength=100, temperature=1.0, damping_coeff=1.0):
        self.particles = particles
        self.springs = springs
        self.bending_springs = bending_springs
        self.gravity = pygame.Vector2(gravity)
        self.repulsion_radius = repulsion_radius
        self.repulsion_strength = repulsion_strength
        self.temperature = temperature
        self.damping_coeff = damping_coeff

    def update(self, dt):
        # apply gravity
        for p in self.particles:
            p.apply_force(self.gravity * p.mass)

        # apply spring forces
        for s in self.springs:
            s.apply()

        if self.bending_springs:
            for bs in self.bending_springs:
                bs.apply()

        # apply repulsion forces between particles to prevent overlap
        for i, p1 in enumerate(self.particles):
            for p2 in self.particles[i+1:]:
                delta = p2.pos - p1.pos
                dist = delta.length()
                if dist > 0 and dist < self.repulsion_radius:
                    direction = delta / dist
                    force_magnitude = self.repulsion_strength * (self.repulsion_radius - dist) / self.repulsion_radius
                    force = direction * force_magnitude
                    p1.apply_force(-force)
                    p2.apply_force(force)

        # tag particles near the simulation wall
        wall_threshold = 5  # distance from the screen edge
        screen_width, screen_height = 1300, 900  # should match SCREEN_SIZE
        for q in self.particles:
            q.near_boundary = False
            if (
                q.pos.x <= wall_threshold or
                q.pos.x >= screen_width - wall_threshold or
                q.pos.y <= wall_threshold or
                q.pos.y >= screen_height - wall_threshold
            ):
                q.near_boundary = True

        # apply viscous damping and Brownian random forces
        for p in self.particles:
            if p.fixed:
                continue
            if getattr(p, "tag", "") == "high_drag":
                drag_multiplier = 30.0  # or any large factor to simulate strong adhesion
            else:
                drag_multiplier = 1.0
            # estimate velocity from Verlet history
            vel = (p.pos - p.prev_pos) / dt
            # viscous drag: F_drag = -γ·m·v
            drag = -drag_multiplier * self.damping_coeff * p.mass * vel
            p.apply_force(drag)
            # Brownian force: Gaussian noise, variance 2·γ·T·m / dt (with k_B = 1)
            sigma = math.sqrt(2 * self.damping_coeff * self.temperature * p.mass / dt)
            rand_fx = random.gauss(0, sigma)
            rand_fy = random.gauss(0, sigma)
            p.apply_force(pygame.Vector2(rand_fx, rand_fy))

        # integrate motion
        for p in self.particles:
            p.integrate(dt, damping=0.98)
        # apply wall friction
        for p in self.particles:
            if getattr(p, "near_boundary", False):
                v = p.pos - p.prev_pos
                friction_coeff = 0.7  # adjust as needed
                v *= friction_coeff
                p.prev_pos = p.pos - v
