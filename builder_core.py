from __future__ import annotations

"""Shared scene construction helpers used by the GUI and CLI builders.

The :class:`SceneBuilder` class collects particle lists and offers a small
API for adding or removing entities, adjusting environment parameters and
serialising the scene to JSON.  It contains the non-graphical logic extracted
from :mod:`start_create` so that the command line interface can operate on the
same data structures as the interactive pygame application.
"""

import math
from typing import Callable, Iterable

import pygame

from particle import Particle
from variable_particle import VariableParticle
from spring import Spring
from variable_spring import VariableSpring
from bending_spring import BendingSpring
from physics import PhysicsEngine
from hook_arm import HookArm
from structures import create_rod as structure_create_rod
import builder_io


class SceneBuilder:
    """Maintain particles, springs and environment settings.

    The class can be used headlessly by the command line interface or embedded
    into the pygame GUI.  It tracks created objects, supports undo operations
    and knows how to serialise the current state.
    """

    def __init__(self, *, with_physics: bool = True) -> None:
        self.particles: list[Particle] = []
        self.springs: list[Spring] = []
        self.variable_springs: list[VariableSpring] = []
        self.variable_particles: list[VariableParticle] = []
        self.bending_springs: list[BendingSpring] = []
        self.arms: list[HookArm] = []
        self.cycle_keys: dict[int, list[HookArm]] = {}
        self.vspring_keys: dict[int, list[VariableSpring]] = {}
        self.vparticle_keys: dict[int, list[VariableParticle]] = {}
        self.history: list[Callable[[], None]] = []

        # environment settings
        self.gravity = pygame.Vector2(0, 0)
        self.repulsion_radius = 20.0
        self.repulsion_strength = 100.0
        self.temperature = 0.0
        self.damping_coeff = 1.0
        self.grid_enabled = False
        self.grid_size = 40.0
        self.paused = False

        if with_physics:
            self.physics = PhysicsEngine(
                self.particles,
                self.springs,
                self.bending_springs,
                gravity=self.gravity,
                repulsion_radius=self.repulsion_radius,
                repulsion_strength=self.repulsion_strength,
                temperature=self.temperature,
                damping_coeff=self.damping_coeff,
            )
        else:  # pragma: no cover - simple attribute assignment
            self.physics = None

    # ------------------------------------------------------------------ grid helpers
    def snap_to_grid(self, vec: pygame.Vector2) -> pygame.Vector2:
        """Return ``vec`` snapped to the nearest grid point if enabled."""
        if not self.grid_enabled:
            return vec
        x = round(vec.x / self.grid_size) * self.grid_size
        y = round(vec.y / self.grid_size) * self.grid_size
        if x == vec.x and y == vec.y:
            return vec
        return pygame.Vector2(x, y)

    def set_grid(self, enabled: bool, size: float | None = None) -> None:
        """Enable or disable grid snapping and optionally set its spacing."""
        self.grid_enabled = enabled
        if size is not None:
            self.grid_size = max(1.0, float(size))

    # ------------------------------------------------------------------ undo support
    def push_undo(self, action: Callable[[], None]) -> None:
        """Record *action* so it can undo the most recent change."""
        self.history.append(action)

    def undo(self) -> None:
        """Undo the last recorded change if possible."""
        if self.history:
            self.history.pop()()

    # ------------------------------------------------------------------ environment
    def set_gravity(self, x: float, y: float) -> None:
        """Update the gravity vector."""
        self.gravity = pygame.Vector2(x, y)
        if self.physics:
            self.physics.gravity = self.gravity

    def set_damping(self, value: float) -> None:
        """Set the global damping coefficient."""
        self.damping_coeff = float(value)
        if self.physics:
            self.physics.damping_coeff = self.damping_coeff

    def set_repulsion(self, radius: float, strength: float) -> None:
        """Configure short range particle repulsion."""
        self.repulsion_radius = float(radius)
        self.repulsion_strength = float(strength)
        if self.physics:
            self.physics.repulsion_radius = self.repulsion_radius
            self.physics.repulsion_strength = self.repulsion_strength

    def set_temperature(self, value: float) -> None:
        """Set the simulation temperature."""
        self.temperature = float(value)
        if self.physics:
            self.physics.temperature = self.temperature

    # ------------------------------------------------------------------ registration helpers
    def register_variable_spring(self, spring: VariableSpring) -> None:
        """Register ``spring`` under its control key if any."""
        if spring.key is not None:
            self.vspring_keys.setdefault(spring.key, []).append(spring)

    def update_vspring_key(self, spring: VariableSpring, key: int | None) -> None:
        """Update the key mapping for ``spring``."""
        old = spring.key
        if old is not None:
            lst = self.vspring_keys.get(old, [])
            if spring in lst:
                lst.remove(spring)
            if not lst and old in self.vspring_keys:
                del self.vspring_keys[old]
        spring.key = key
        if key is not None:
            self.vspring_keys.setdefault(key, []).append(spring)

    def register_variable_particle(self, part: VariableParticle) -> None:
        """Register ``part`` under its control key if any."""
        if part.key is not None:
            self.vparticle_keys.setdefault(part.key, []).append(part)

    def update_vparticle_key(self, part: VariableParticle, key: int | None) -> None:
        """Update the key mapping for ``part``."""
        old = part.key
        if old is not None:
            lst = self.vparticle_keys.get(old, [])
            if part in lst:
                lst.remove(part)
            if not lst and old in self.vparticle_keys:
                del self.vparticle_keys[old]
        part.key = key
        if key is not None:
            self.vparticle_keys.setdefault(key, []).append(part)

    # ------------------------------------------------------------------ entity management
    def remove_entities(
        self,
        particles: Iterable[Particle] = (),
        springs: Iterable[Spring] = (),
        bends: Iterable[BendingSpring] = (),
        arms: Iterable[HookArm] = (),
    ) -> None:
        """Remove collections of objects from the simulation."""
        parts_set = set(particles)
        springs_set = set(springs)
        bends_set = set(bends)
        arms_set = set(arms)

        for arm in list(self.arms):
            if arm in arms_set or any(p in parts_set for p in arm.particles):
                self._remove_arm(arm)
                parts_set.difference_update(arm.particles)
                springs_set.difference_update(arm.springs)

        if parts_set or springs_set:
            for s in list(self.springs):
                if s in springs_set or s.p1 in parts_set or s.p2 in parts_set:
                    self.springs.remove(s)
                    if isinstance(s, VariableSpring):
                        if s in self.variable_springs:
                            self.variable_springs.remove(s)
                        if s.key is not None and s.key in self.vspring_keys:
                            lst = self.vspring_keys[s.key]
                            if s in lst:
                                lst.remove(s)
                            if not lst:
                                del self.vspring_keys[s.key]
            for p in parts_set:
                if p in self.particles:
                    self.particles.remove(p)
                if isinstance(p, VariableParticle):
                    if p in self.variable_particles:
                        self.variable_particles.remove(p)
                    if p.key is not None and p.key in self.vparticle_keys:
                        lst = self.vparticle_keys[p.key]
                        if p in lst:
                            lst.remove(p)
                        if not lst:
                            del self.vparticle_keys[p.key]

        if bends_set:
            for b in list(self.bending_springs):
                if b in bends_set or b.p1 in parts_set or b.p2 in parts_set or b.p3 in parts_set:
                    self.bending_springs.remove(b)

    def _remove_arm(self, arm: HookArm) -> None:
        if arm in self.arms:
            self.arms.remove(arm)
        if arm.cycle_key is not None and arm.cycle_key in self.cycle_keys:
            lst = self.cycle_keys[arm.cycle_key]
            if arm in lst:
                lst.remove(arm)
            if not lst:
                del self.cycle_keys[arm.cycle_key]
        for p in arm.particles:
            if p in self.particles:
                self.particles.remove(p)
        for s in arm.springs:
            if s in self.springs:
                self.springs.remove(s)

    def _restore_particle(self, p: Particle, springs: list[Spring]) -> None:
        """Reinsert ``p`` and any associated ``springs``."""
        self.particles.append(p)
        self.springs.extend(springs)
        for s in springs:
            if isinstance(s, VariableSpring):
                self.variable_springs.append(s)
                self.register_variable_spring(s)
        if isinstance(p, VariableParticle):
            self.variable_particles.append(p)
            self.register_variable_particle(p)

    def _restore_spring(self, s: Spring) -> None:
        """Reinsert ``s`` into the simulation."""
        self.springs.append(s)
        if isinstance(s, VariableSpring):
            self.variable_springs.append(s)
            self.register_variable_spring(s)

    # ------------------------------------------------------------------ creation helpers
    def add_particle(
        self,
        pos: tuple[float, float],
        *,
        mass: float = 1.0,
        radius: float = 5.0,
        color: tuple[int, int, int] | None = None,
        drag: float = 1.0,
    ) -> Particle:
        """Create and return a new :class:`Particle`."""
        p = Particle(self.snap_to_grid(pygame.Vector2(pos)), mass=mass, radius=radius, color=color, drag=drag)
        p.prev_pos = p.pos.copy()
        self.particles.append(p)
        self.push_undo(lambda p=p: self.remove_entities([p]))
        return p

    def add_variable_particle(
        self,
        pos: tuple[float, float],
        *,
        mass: float = 1.0,
        radius: float = 5.0,
        color: tuple[int, int, int] | None = None,
        base_drag: float = 1.0,
        alt_drag: float = 100.0,
        key: int | None = None,
        mode: str = "hold",
        change_speed: float = 240.0,
    ) -> VariableParticle:
        """Create and return a new :class:`VariableParticle`."""
        p = VariableParticle(
            self.snap_to_grid(pygame.Vector2(pos)),
            mass=mass,
            radius=radius,
            color=color,
            base_drag=base_drag,
            alt_drag=alt_drag,
            key=key,
            mode=mode,
            change_speed=change_speed,
        )
        p.prev_pos = p.pos.copy()
        self.particles.append(p)
        self.variable_particles.append(p)
        self.register_variable_particle(p)
        self.push_undo(lambda p=p: self.remove_entities([p]))
        return p

    def add_spring(
        self,
        p1_index: int,
        p2_index: int,
        *,
        rest_length: float | None = None,
        stiffness: float = 200.0,
        max_force: float | None = None,
        invisible: bool = False,
    ) -> Spring:
        """Create a linear spring between two particles."""
        p1 = self.particles[p1_index]
        p2 = self.particles[p2_index]
        if rest_length is None:
            rest_length = (p2.pos - p1.pos).length()
        s = Spring(p1, p2, rest_length, stiffness=stiffness, max_force=max_force, invisible=invisible)
        self.springs.append(s)
        self.push_undo(lambda s=s: self.remove_entities(springs=[s]))
        return s

    def add_variable_spring(
        self,
        p1_index: int,
        p2_index: int,
        *,
        rest_length: float,
        alt_rest_length: float,
        stiffness: float = 200.0,
        key: int | None = None,
        mode: str = "hold",
        change_speed: float = 240.0,
        max_force: float | None = None,
        invisible: bool = False,
    ) -> VariableSpring:
        """Create a :class:`VariableSpring` between two particles."""
        p1 = self.particles[p1_index]
        p2 = self.particles[p2_index]
        s = VariableSpring(
            p1,
            p2,
            rest_length,
            alt_rest_length,
            stiffness,
            key=key,
            mode=mode,
            change_speed=change_speed,
            max_force=max_force,
            invisible=invisible,
        )
        self.springs.append(s)
        self.variable_springs.append(s)
        self.register_variable_spring(s)
        self.push_undo(lambda s=s: self.remove_entities(springs=[s]))
        return s

    def add_bending_spring(
        self,
        p1_index: int,
        p2_index: int,
        p3_index: int,
        *,
        angle: float,
        stiffness: float = 100.0,
    ) -> BendingSpring:
        """Create a :class:`BendingSpring` defined by three particles."""
        p1 = self.particles[p1_index]
        p2 = self.particles[p2_index]
        p3 = self.particles[p3_index]
        bs = BendingSpring(p1, p2, p3, angle, stiffness)
        self.bending_springs.append(bs)
        self.push_undo(lambda bs=bs: self.remove_entities(bends=[bs]))
        return bs

    def create_circle(
        self,
        center: pygame.Vector2,
        radius: float,
        segments: int,
        stiffness: float,
        add_bending: bool,
        bend_stiffness: float,
        *,
        mass: float = 1.0,
        color: tuple[int, int, int] | None = None,
        particle_radius: float = 5.0,
    ) -> None:
        """Spawn a ring of particles with optional bending springs."""
        center = self.snap_to_grid(center)
        particles: list[Particle] = []
        springs: list[Spring] = []
        for i in range(segments):
            theta = (i / segments) * 2 * math.pi
            pos = center + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
            pos = self.snap_to_grid(pos)
            p = Particle(pos, mass=mass, color=color, radius=particle_radius)
            particles.append(p)
        for i in range(segments):
            p1 = particles[i]
            p2 = particles[(i + 1) % segments]
            rest = (p2.pos - p1.pos).length()
            springs.append(Spring(p1, p2, rest_length=rest, stiffness=stiffness))
        bends: list[BendingSpring] = []
        if add_bending:
            for i in range(segments):
                p1 = particles[i - 1]
                p2 = particles[i]
                p3 = particles[(i + 1) % segments]
                v1 = p1.pos - p2.pos
                v2 = p3.pos - p2.pos
                if v1.length() == 0 or v2.length() == 0:
                    angle = 0.0
                else:
                    dot = max(-1.0, min(1.0, v1.normalize().dot(v2.normalize())))
                    angle = math.acos(dot)
                bends.append(BendingSpring(p1, p2, p3, angle, bend_stiffness))
            self.bending_springs.extend(bends)
        self.particles.extend(particles)
        self.springs.extend(springs)
        self.push_undo(
            lambda parts=particles, sprs=springs, bends=bends: self.remove_entities(parts, sprs, bends)
        )

    def create_rod(
        self,
        center: pygame.Vector2,
        radius: float,
        length: float,
        segments: int,
        include_cytoskeleton: bool,
        include_skeleton: bool,
        skeleton_count: int,
        stiffness: float,
        add_bending: bool,
        bend_stiffness: float,
        *,
        mass: float = 1.0,
        color: tuple[int, int, int] | None = None,
        particle_radius: float = 5.0,
    ) -> None:
        """Create a capsule-shaped rod with optional bending springs."""
        center = self.snap_to_grid(center)
        particles, springs = structure_create_rod(
            center,
            radius=radius,
            length=length,
            segments=segments,
            stiffness=stiffness,
            max_force=None,
            color=color,
            include_cytoskeleton=include_cytoskeleton,
            cyto_stiffness=stiffness,
            include_skeleton=include_skeleton,
            skeleton_count=skeleton_count,
            skeleton_stiffness=stiffness,
        )
        for p in particles:
            p.mass = mass
            p.radius = particle_radius
            p.color = color
            p.pos = self.snap_to_grid(p.pos)
            p.prev_pos = p.pos.copy()
        self.particles.extend(particles)
        self.springs.extend(springs)
        bends: list[BendingSpring] = []
        if add_bending:
            perimeter = particles[:segments]
            for i in range(len(perimeter)):
                p1 = perimeter[i - 1]
                p2 = perimeter[i]
                p3 = perimeter[(i + 1) % len(perimeter)]
                v1 = p1.pos - p2.pos
                v2 = p3.pos - p2.pos
                if v1.length() == 0 or v2.length() == 0:
                    angle = 0.0
                else:
                    dot = max(-1.0, min(1.0, v1.normalize().dot(v2.normalize())))
                    angle = math.acos(dot)
                bends.append(BendingSpring(p1, p2, p3, angle, bend_stiffness))
            self.bending_springs.extend(bends)
        self.push_undo(
            lambda parts=particles, sprs=springs, bends=bends: self.remove_entities(parts, sprs, bends)
        )

    def create_hook_arm(
        self,
        base: Particle,
        direction: pygame.Vector2,
        segments: int,
        spacing: float,
        mass: float,
        radius: float,
        stiffness: float,
        color,
        high_drag_color,
        adhesion_factor: float,
        cycle_key: int | None,
        cycle_speed: float,
    ) -> None:
        """Attach a :class:`HookArm` to ``base`` and register its key."""
        arm = HookArm(
            base,
            direction if direction.length() > 0 else pygame.Vector2(1, 0),
            segments=segments,
            spacing=spacing,
            stiffness=stiffness,
            color=color,
            high_drag_color=high_drag_color,
            adhesion_mass_factor=adhesion_factor,
            mass=mass,
            radius=radius,
            cycle_speed=cycle_speed,
        )
        arm.cycle_key = cycle_key
        if cycle_key is not None:
            self.cycle_keys.setdefault(cycle_key, []).append(arm)
        for p in arm.particles:
            p.pos = self.snap_to_grid(p.pos)
            p.prev_pos = p.pos.copy()
        self.arms.append(arm)
        self.particles.extend(arm.particles)
        self.springs.extend(arm.springs)
        self.push_undo(lambda arm=arm: self.remove_entities(arms=[arm]))

    # ------------------------------------------------------------------ serialisation
    def _build_springs(self) -> list[dict]:
        data: list[dict] = []
        for s in self.springs:
            sd = {
                "p1": self.particles.index(s.p1),
                "p2": self.particles.index(s.p2),
                "rest": s.rest_length,
                "stiff": s.stiffness,
                "max": s.max_force,
                "invis": s.invisible,
            }
            if isinstance(s, VariableSpring):
                sd.update(
                    {
                        "type": "variable",
                        "rest": s.base_rest_length,
                        "alt": s.alt_rest_length,
                        "speed": s.change_speed,
                        "key": s.key,
                        "mode": s.mode,
                        "active": s.active,
                        "curr": s.rest_length,
                    }
                )
            data.append(sd)
        return data

    def build_state(self) -> dict:
        """Return a serialisable representation of the scene."""
        return {
            "particles": [
                {
                    "pos": [p.pos.x, p.pos.y],
                    "prev": [p.prev_pos.x, p.prev_pos.y],
                    "mass": p.mass,
                    "radius": p.radius,
                    "color": list(p.color) if p.color else None,
                    "tag": p.tag,
                    "fixed": p.fixed,
                    "drag": p.drag,
                    **(
                        {
                            "type": "variable",
                            "base": p.base_drag,
                            "alt": p.alt_drag,
                            "speed": p.change_speed,
                            "key": p.key,
                            "mode": p.mode,
                            "active": p.active,
                            "curr": p.drag,
                        }
                        if isinstance(p, VariableParticle)
                        else {}
                    ),
                }
                for p in self.particles
            ],
            "springs": self._build_springs(),
            "bending": [
                {
                    "p1": self.particles.index(bs.p1),
                    "p2": self.particles.index(bs.p2),
                    "p3": self.particles.index(bs.p3),
                    "angle": bs.rest_angle,
                    "stiff": bs.stiffness,
                }
                for bs in self.bending_springs
            ],
            "arms": [
                {
                    "particles": [self.particles.index(p) for p in arm.particles],
                    "springs": [self.springs.index(s) for s in arm.springs],
                    "rest_lengths": arm.rest_lengths,
                    "max_lengths": arm.max_lengths,
                    "cycle_speed": arm.cycle_speed,
                    "color": list(arm.color),
                    "high_color": list(arm.high_drag_color),
                    "adhesion": arm.adhesion_mass_factor,
                    "orig_mass": arm._orig_mass,
                    "adhesion_drag": arm.adhesion_drag,
                    "orig_drag": arm._orig_drag,
                    "cycle_key": arm.cycle_key,
                }
                for arm in self.arms
            ],
            "physics": {
                "gravity": [self.gravity.x, self.gravity.y],
                "repulsion_radius": self.repulsion_radius,
                "repulsion_strength": self.repulsion_strength,
                "temperature": self.temperature,
                "damping_coeff": self.damping_coeff,
            },
        }

    def apply_state(self, data: dict) -> None:
        """Rebuild the scene from a serialised *data* structure."""
        self.particles = []
        self.variable_particles = []
        self.vparticle_keys = {}
        for pd in data.get("particles", []):
            if pd.get("type") == "variable":
                p = VariableParticle(
                    pd["pos"],
                    mass=pd.get("mass", 1.0),
                    color=tuple(pd["color"]) if pd.get("color") else None,
                    radius=pd.get("radius"),
                    base_drag=pd.get("base", 1.0),
                    alt_drag=pd.get("alt", 100.0),
                    key=pd.get("key"),
                    mode=pd.get("mode", "hold"),
                    change_speed=pd.get("speed", 240.0),
                )
                p.active = pd.get("active", False)
                p.drag = pd.get("curr", p.base_drag)
                self.variable_particles.append(p)
                self.register_variable_particle(p)
            else:
                p = Particle(
                    pd["pos"],
                    mass=pd.get("mass", 1.0),
                    color=tuple(pd["color"]) if pd.get("color") else None,
                    radius=pd.get("radius"),
                    tag=pd.get("tag"),
                    drag=pd.get("drag", 1.0),
                )
            p.prev_pos = pygame.Vector2(pd.get("prev", pd["pos"]))
            p.fixed = pd.get("fixed", False)
            self.particles.append(p)

        self.springs = []
        self.variable_springs = []
        self.vspring_keys = {}
        for sd in data.get("springs", []):
            if sd.get("type") == "variable":
                s = VariableSpring(
                    self.particles[sd["p1"]],
                    self.particles[sd["p2"]],
                    sd.get("rest", 0),
                    sd.get("alt", 0),
                    sd.get("stiff", 200.0),
                    key=sd.get("key"),
                    mode=sd.get("mode", "hold"),
                    change_speed=sd.get("speed", 240.0),
                    max_force=sd.get("max"),
                    invisible=sd.get("invis", False),
                )
                s.active = sd.get("active", False)
                s.rest_length = sd.get("curr", s.base_rest_length)
                self.springs.append(s)
                self.variable_springs.append(s)
                self.register_variable_spring(s)
            else:
                s = Spring(
                    self.particles[sd["p1"]],
                    self.particles[sd["p2"]],
                    sd.get("rest", 0),
                    stiffness=sd.get("stiff", 200.0),
                    max_force=sd.get("max"),
                    invisible=sd.get("invis", False),
                )
                self.springs.append(s)

        self.bending_springs = []
        for bd in data.get("bending", []):
            bs = BendingSpring(
                self.particles[bd["p1"]],
                self.particles[bd["p2"]],
                self.particles[bd["p3"]],
                bd.get("angle", 0),
                bd.get("stiff", 0),
            )
            self.bending_springs.append(bs)

        self.arms = []
        self.cycle_keys = {}
        for ad in data.get("arms", []):
            arm = HookArm.__new__(HookArm)
            arm.particles = [self.particles[i] for i in ad["particles"]]
            arm.springs = [self.springs[i] for i in ad["springs"]]
            arm.color = tuple(ad["color"])
            arm.high_drag_color = tuple(ad["high_color"])
            arm.adhesion_mass_factor = ad.get("adhesion", 10.0)
            arm.adhesion_drag = ad.get("adhesion_drag", 100.0)
            arm.cycle_speed = ad.get("cycle_speed", 240.0)
            arm.rest_lengths = ad.get("rest_lengths", [s.rest_length for s in arm.springs])
            arm.max_lengths = ad.get("max_lengths", [r * 4 for r in arm.rest_lengths])
            arm.tip = arm.particles[-1]
            arm._orig_mass = ad.get("orig_mass", arm.tip.mass)
            arm._orig_drag = ad.get("orig_drag", arm.tip.drag)
            arm.extend_held = False
            arm.contract_held = False
            arm.cycle_held = False
            arm.cycle_active = False
            arm.cycle_phase = 0
            arm.cycle_key = ad.get("cycle_key")
            if arm.cycle_key is not None:
                self.cycle_keys.setdefault(arm.cycle_key, []).append(arm)
            arm._set_high_drag(False)
            self.arms.append(arm)

        phys = data.get("physics", {})
        self.set_gravity(*phys.get("gravity", [0, 0]))
        self.set_repulsion(
            phys.get("repulsion_radius", 20),
            phys.get("repulsion_strength", 100),
        )
        self.set_temperature(phys.get("temperature", 0))
        self.set_damping(phys.get("damping_coeff", 1))
        if self.physics:
            self.physics.particles = self.particles
            self.physics.springs = self.springs
            self.physics.bending_springs = self.bending_springs

    def save(self, path: str) -> None:
        """Serialise the current state to ``path``."""
        builder_io.save_state(path, self.build_state())

    def load(self, path: str) -> None:
        """Load scene state from ``path``."""
        data = builder_io.load_state(path)
        self.apply_state(data)

    # ------------------------------------------------------------------ simulation
    def run(self, steps: int = 1, dt: float = 1 / 60) -> None:
        """Advance the simulation for ``steps`` iterations."""
        if not self.physics or self.paused:
            return
        for _ in range(steps):
            if self.paused:
                break
            self.physics.update(dt)
            for arm in self.arms:
                arm.update(dt)
            for s in self.variable_springs:
                s.update(dt)
            for p in self.variable_particles:
                p.update(dt)

    def stop(self) -> None:
        """Pause the simulation."""
        self.paused = True

