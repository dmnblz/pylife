# physics.py
"""Core physics simulation for the particle system.

This module defines :class:`PhysicsEngine` which integrates a set of
particles connected by springs.  The engine applies spring forces, viscous
damping and random Brownian motion to each particle while also handling basic
repulsion so particles do not overlap.  A simple Verlet integrator advances the
system forward in time.
"""

import pygame
from particle import Particle
from spring import Spring
from bending_spring import BendingSpring
import random
import math

class PhysicsEngine:
    """Orchestrates physics updates for a set of particles and springs.

    Parameters
    ----------
    particles:
        List of :class:`Particle` objects that will be integrated.
    springs:
        Linear springs connecting pairs of particles.
    bending_springs:
        Optional list of :class:`BendingSpring` instances providing angular
        constraints.
    gravity:
        Constant acceleration applied to each particle (x, y).
    repulsion_radius:
        Distance within which particles repel each other to avoid overlap.
    repulsion_strength:
        Magnitude of the short range repulsive force.
    temperature:
        Scales the Brownian noise applied to particles.
    damping_coeff:
        Coefficient for viscous drag and the Brownian noise variance.
    """
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
        # Updated dynamically by the app when the window resizes
        self._screen_size: tuple[int, int] | None = None
        # Optional world-space playable area used for boundary proximity
        self._play_area: pygame.Rect | None = None
        # Fixed timestep controls
        self._accumulator: float = 0.0
        self._fixed_dt: float | None = None
        self._substeps: int = 1
        self._max_catchup_steps: int = 8
        self._max_frame_dt: float = 0.1  # clamp very large frame times

    def set_fixed_timestep(
        self,
        fixed_dt: float | None,
        *,
        substeps: int = 1,
        max_catchup_steps: int = 8,
        max_frame_dt: float = 0.1,
    ) -> None:
        """Configure a fixed integration timestep with optional substeps.

        Parameters
        ----------
        fixed_dt:
            The outer fixed step in seconds. ``None`` disables fixed stepping and
            uses the variable ``dt`` passed to :meth:`update`.
        substeps:
            Number of inner solver substeps per fixed step (>= 1).
        max_catchup_steps:
            Maximum number of fixed steps processed per frame to avoid a spiral
            of death on stalls. Remaining accumulator is preserved.
        max_frame_dt:
            Clamp for the per-frame input ``dt`` used to fill the accumulator.
        """

        self._fixed_dt = fixed_dt if fixed_dt and fixed_dt > 0 else None
        self._substeps = max(1, int(substeps))
        self._max_catchup_steps = max(1, int(max_catchup_steps))
        self._max_frame_dt = max(1e-5, float(max_frame_dt))

    def set_screen_size(self, width: int, height: int) -> None:
        """Provide the current window size so boundary effects can adapt."""
        self._screen_size = (int(width), int(height))

    def set_play_area(self, rect: pygame.Rect) -> None:
        """Set the world-space playable area rectangle used for boundary effects."""
        # store a copy to avoid outside mutation surprises
        self._play_area = pygame.Rect(rect)

    def update(self, dt: float) -> None:
        """Advance the simulation by ``dt`` seconds.

        If a fixed timestep is configured via :meth:`set_fixed_timestep`, this
        method fills an internal accumulator and executes a number of fixed
        steps, each split into optional substeps. Otherwise, a single variable
        step of duration ``dt`` is executed.
        """

        if self._fixed_dt is not None:
            frame_dt = min(self._max_frame_dt, max(0.0, float(dt)))
            self._accumulator += frame_dt
            steps_done = 0
            while self._accumulator >= self._fixed_dt and steps_done < self._max_catchup_steps:
                h = self._fixed_dt / self._substeps
                for _ in range(self._substeps):
                    self._step(h)
                self._accumulator -= self._fixed_dt
                steps_done += 1
            # If we still have a lot accumulated, keep a bounded remainder
            max_remainder = self._fixed_dt * self._max_catchup_steps
            if self._accumulator > max_remainder:
                self._accumulator = max_remainder
        else:
            self._step(max(1e-6, float(dt)))

    def _step(self, dt: float) -> None:
        """Execute one physics step of duration ``dt`` (seconds)."""

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
            for p2 in self.particles[i + 1 :]:
                delta = p2.pos - p1.pos
                dist = delta.length()
                if dist > 0 and dist < self.repulsion_radius:
                    direction = delta / dist
                    force_magnitude = self.repulsion_strength * (self.repulsion_radius - dist) / self.repulsion_radius
                    force = direction * force_magnitude
                    p1.apply_force(-force)
                    p2.apply_force(force)

        # tag particles near the simulation wall (if window size is known)
        wall_threshold = 5  # distance from the boundary
        if self._play_area is not None:
            left, top, width, height = self._play_area
            right = left + width
            bottom = top + height
            for q in self.particles:
                q.near_boundary = False
                if (
                    q.pos.x <= left + wall_threshold
                    or q.pos.x >= right - wall_threshold
                    or q.pos.y <= top + wall_threshold
                    or q.pos.y >= bottom - wall_threshold
                ):
                    q.near_boundary = True
        elif self._screen_size is not None:
            screen_width, screen_height = self._screen_size
            for q in self.particles:
                q.near_boundary = False
                if (
                    q.pos.x <= wall_threshold
                    or q.pos.x >= screen_width - wall_threshold
                    or q.pos.y <= wall_threshold
                    or q.pos.y >= screen_height - wall_threshold
                ):
                    q.near_boundary = True
        else:
            # if unknown, ensure the flag is consistently absent/False
            for q in self.particles:
                q.near_boundary = False

        # apply viscous damping and Brownian random forces
        for p in self.particles:
            if p.fixed:
                continue
            drag_multiplier = getattr(p, "drag", 1.0)
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
