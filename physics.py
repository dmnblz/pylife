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
    integration_damping:
        Velocity scaling factor applied during Verlet integration.
    collisions_enabled:
        If ``True`` (default) resolve overlapping particles after integration.
    collision_elasticity:
        Base coefficient ``e`` (0–1) controlling bounce when resolving
        collisions. The value is multiplied by the ``elasticity`` of each
        particle involved.
    collision_bucket_size:
        Size of the spatial-hash cells used for collision detection. ``None``
        chooses twice the maximum particle radius each step.
    """
    def __init__(
        self,
        particles: list[Particle],
        springs: list[Spring],
        bending_springs: list[BendingSpring] = None,
        gravity=(0, 0),
        repulsion_radius=20,
        repulsion_strength=100,
        temperature=1.0,
        damping_coeff=1.0,
        integration_damping: float = 0.98,
        collisions_enabled: bool = True,
        collision_elasticity: float = 1.0,
        collision_bucket_size: float | None = None,
    ):
        self.particles = particles
        self.springs = springs
        self.bending_springs = bending_springs
        self.gravity = pygame.Vector2(gravity)
        self.repulsion_radius = repulsion_radius
        self.repulsion_strength = repulsion_strength
        self.temperature = temperature
        self.damping_coeff = damping_coeff
        self.integration_damping = integration_damping
        self.collisions_enabled = bool(collisions_enabled)
        self.collision_elasticity = float(collision_elasticity)
        self.collision_bucket_size = (
            float(collision_bucket_size)
            if collision_bucket_size and collision_bucket_size > 0
            else None
        )
        self.trails_enabled: bool = False
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
        # Neighbor search (spatial hash) for repulsion
        self._use_spatial_hash: bool = True
        self._repulsion_rebuild_interval_steps: int = 1
        self._repulsion_steps_since_rebuild: int = 0
        self._repulsion_buckets: dict[tuple[int, int], list[int]] = {}
        self._repulsion_bucket_size: float = max(1e-6, float(self.repulsion_radius))
        self._last_repulsion_radius: float = float(self.repulsion_radius)
        # Spatial hash reused by collisions when repulsion builds it
        self._collision_buckets: dict[tuple[int, int], list[int]] = {}
        self._collision_bucket_size: float = 0.0
        # time delta of the most recent integration step
        self._last_dt: float = 1.0

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
        # record step duration for energy calculations
        self._last_dt = max(1e-8, float(dt))

        # apply gravity
        for p in self.particles:
            p.apply_force(self.gravity * p.mass)

        # apply spring forces
        for s in self.springs:
            s.apply()

        if self.bending_springs:
            for bs in self.bending_springs:
                bs.apply()

        # apply repulsion forces using neighbor search
        self._apply_repulsion()

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
            p.integrate(dt, damping=self.integration_damping)
        # resolve direct particle collisions
        self._resolve_collisions()
        # apply wall friction
        for p in self.particles:
            if getattr(p, "near_boundary", False):
                v = p.pos - p.prev_pos
                friction_coeff = 0.7  # adjust as needed
                v *= friction_coeff
                p.prev_pos = p.pos - v
        if self.trails_enabled:
            for p in self.particles:
                p.trail.append(p.pos.copy())

    def configure_neighbor_search(self, *, enabled: bool = True, rebuild_interval_steps: int = 1) -> None:
        """Enable/disable spatial-hash neighbor search for repulsion and set rebuild cadence.

        Parameters
        ----------
        enabled:
            If ``True`` (default) use a uniform grid spatial hash to find neighbors.
        rebuild_interval_steps:
            Rebuild the spatial hash every N integration steps (default 1 = each step).
        """
        self._use_spatial_hash = bool(enabled)
        self._repulsion_rebuild_interval_steps = max(1, int(rebuild_interval_steps))
        self._repulsion_steps_since_rebuild = 0
        self._repulsion_buckets.clear()
        self._collision_buckets.clear()

    def _get_collision_bucket_size(self) -> float:
        """Return the spatial-hash cell size for collisions."""
        if self.collision_bucket_size and self.collision_bucket_size > 0:
            return max(1e-6, float(self.collision_bucket_size))
        max_r = 0.0
        for p in self.particles:
            r = getattr(p, "radius", 0) or 0
            if r > max_r:
                max_r = r
        return max(1e-6, 2 * max_r)

    def _build_repulsion_buckets(self) -> None:
        bs = max(self._get_collision_bucket_size(), float(self.repulsion_radius))
        self._repulsion_bucket_size = bs
        self._last_repulsion_radius = float(self.repulsion_radius)
        buckets: dict[tuple[int, int], list[int]] = {}
        for i, p in enumerate(self.particles):
            cx = int(math.floor(p.pos.x / bs))
            cy = int(math.floor(p.pos.y / bs))
            buckets.setdefault((cx, cy), []).append(i)
        self._repulsion_buckets = buckets
        self._collision_buckets = buckets
        self._collision_bucket_size = bs

    def _build_collision_buckets(self) -> None:
        bs = self._get_collision_bucket_size()
        buckets: dict[tuple[int, int], list[int]] = {}
        for i, p in enumerate(self.particles):
            cx = int(math.floor(p.pos.x / bs))
            cy = int(math.floor(p.pos.y / bs))
            buckets.setdefault((cx, cy), []).append(i)
        self._collision_buckets = buckets
        self._collision_bucket_size = bs

    def _apply_repulsion(self) -> None:
        """Push particles apart when they come within the repulsion radius."""

        if self.repulsion_radius <= 0 or self.repulsion_strength == 0 or len(self.particles) < 2:
            self._collision_buckets.clear()
            return

        radius = self.repulsion_radius
        inv_radius = 1.0 / radius
        radius_sq = radius * radius

        if not self._use_spatial_hash:
            self._collision_buckets.clear()
            for i, p1 in enumerate(self.particles):
                for j in range(i + 1, len(self.particles)):
                    p2 = self.particles[j]
                    delta = p2.pos - p1.pos
                    dist_sq = delta.length_squared()
                    if 0 < dist_sq < radius_sq:
                        dist = math.sqrt(dist_sq)
                        direction = delta / dist
                        force_magnitude = self.repulsion_strength * (radius - dist) * inv_radius
                        force = direction * force_magnitude
                        p1.apply_force(-force)
                        p2.apply_force(force)
            return

        # Rebuild buckets if needed (radius changed or interval elapsed)
        if (
            not self._repulsion_buckets
            or self._repulsion_steps_since_rebuild % self._repulsion_rebuild_interval_steps == 0
            or self._last_repulsion_radius != float(self.repulsion_radius)
        ):
            self._build_repulsion_buckets()
            self._repulsion_steps_since_rebuild = 0
        else:
            self._repulsion_steps_since_rebuild += 1

        bs = self._repulsion_bucket_size
        buckets = self._repulsion_buckets
        neighbor_offsets = (
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),  (0, 0),  (0, 1),
            (1, -1),  (1, 0),  (1, 1),
        )

        for i, p1 in enumerate(self.particles):
            cx = int(math.floor(p1.pos.x / bs))
            cy = int(math.floor(p1.pos.y / bs))
            for dx, dy in neighbor_offsets:
                cell = (cx + dx, cy + dy)
                lst = buckets.get(cell)
                if not lst:
                    continue
                for j in lst:
                    if j <= i:
                        continue
                    p2 = self.particles[j]
                    delta = p2.pos - p1.pos
                    dist_sq = delta.length_squared()
                    if 0 < dist_sq < radius_sq:
                        dist = math.sqrt(dist_sq)
                        direction = delta / dist
                        force_magnitude = self.repulsion_strength * (radius - dist) * inv_radius
                        force = direction * force_magnitude
                        p1.apply_force(-force)
                        p2.apply_force(force)

    def _resolve_collisions(self) -> None:
        """Separate overlapping particles and apply optional bounce.

        Each particle may define an ``elasticity`` coefficient that scales
        the engine-wide ``collision_elasticity``.
        """

        if not self.collisions_enabled or len(self.particles) < 2:
            return

        base_e = max(0.0, float(self.collision_elasticity))

        if self._use_spatial_hash:
            if not self._collision_buckets:
                self._build_collision_buckets()
            bs = self._collision_bucket_size
            buckets = self._collision_buckets
            neighbor_offsets = (
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1),  (0, 0),  (0, 1),
                (1, -1),  (1, 0),  (1, 1),
            )
            for i, p1 in enumerate(self.particles):
                cx = int(math.floor(p1.pos.x / bs))
                cy = int(math.floor(p1.pos.y / bs))
                for dx, dy in neighbor_offsets:
                    lst = buckets.get((cx + dx, cy + dy))
                    if not lst:
                        continue
                    for j in lst:
                        if j <= i:
                            continue
                        p2 = self.particles[j]
                        r1 = getattr(p1, "radius", 0) or 0
                        r2 = getattr(p2, "radius", 0) or 0
                        if r1 <= 0 and r2 <= 0:
                            continue
                        delta = p2.pos - p1.pos
                        min_dist = r1 + r2
                        if min_dist <= 0:
                            continue
                        dist_sq = delta.length_squared()
                        if dist_sq >= min_dist * min_dist:
                            continue
                        dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.0
                        if dist == 0:
                            delta = pygame.Vector2(1, 0)
                            dist = 1.0
                        n = delta / dist
                        overlap = min_dist - dist
                        self._separate_and_bounce(p1, p2, n, overlap, base_e)
        else:
            for i in range(len(self.particles)):
                p1 = self.particles[i]
                for j in range(i + 1, len(self.particles)):
                    p2 = self.particles[j]
                    r1 = getattr(p1, "radius", 0) or 0
                    r2 = getattr(p2, "radius", 0) or 0
                    if r1 <= 0 and r2 <= 0:
                        continue
                    delta = p2.pos - p1.pos
                    min_dist = r1 + r2
                    if min_dist <= 0:
                        continue
                    dist_sq = delta.length_squared()
                    if dist_sq >= min_dist * min_dist:
                        continue
                    dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.0
                    if dist == 0:
                        delta = pygame.Vector2(1, 0)
                        dist = 1.0
                    n = delta / dist
                    overlap = min_dist - dist
                    self._separate_and_bounce(p1, p2, n, overlap, base_e)

    def _separate_and_bounce(
        self,
        p1: Particle,
        p2: Particle,
        n: pygame.Vector2,
        overlap: float,
        base_e: float,
    ) -> None:
        """Resolve overlap between ``p1`` and ``p2`` and apply bounce."""
        if p1.fixed and p2.fixed:
            return
        elif p1.fixed:
            move2 = n * overlap
            p2.pos += move2
            p2.prev_pos += move2
        elif p2.fixed:
            move1 = -n * overlap
            p1.pos += move1
            p1.prev_pos += move1
        else:
            total_mass = p1.mass + p2.mass
            move1 = -n * overlap * (p2.mass / total_mass)
            move2 = n * overlap * (p1.mass / total_mass)
            p1.pos += move1
            p2.pos += move2
            p1.prev_pos += move1
            p2.prev_pos += move2

        e_pair = base_e * min(getattr(p1, "elasticity", 1.0), getattr(p2, "elasticity", 1.0))
        if e_pair <= 0:
            return

        v1 = p1.pos - p1.prev_pos
        v2 = p2.pos - p2.prev_pos
        rel = v1 - v2
        rel_norm = rel.dot(n)
        if rel_norm <= 0:
            return
        inv1 = 0.0 if p1.fixed else 1.0 / p1.mass
        inv2 = 0.0 if p2.fixed else 1.0 / p2.mass
        denom = inv1 + inv2
        if denom == 0:
            return
        j_imp = (1 + e_pair) * rel_norm / denom
        if not p1.fixed:
            v1 -= j_imp * inv1 * n
            p1.prev_pos = p1.pos - v1
        if not p2.fixed:
            v2 += j_imp * inv2 * n
            p2.prev_pos = p2.pos - v2

    def total_energy(self) -> float:
        """Return total kinetic and spring potential energy."""

        dt = self._last_dt if self._last_dt > 0 else 1.0
        inv_dt = 1.0 / dt
        kinetic = 0.0
        for p in self.particles:
            vel = (p.pos - p.prev_pos) * inv_dt
            kinetic += 0.5 * p.mass * vel.length_squared()
        potential = 0.0
        for s in self.springs:
            potential += s.potential_energy()
        return kinetic + potential
