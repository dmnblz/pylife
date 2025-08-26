"""Scene management: entities and safe add/remove/restore helpers.

The Scene centralises mutating operations over the entity lists so the
builder can delegate without duplicating logic.
"""
from __future__ import annotations

from typing import Iterable

from particle import Particle
from spring import Spring
from variable_spring import VariableSpring
from bending_spring import BendingSpring
from variable_bending_spring import VariableBendingSpring
from variable_particle import VariableParticle
from sensor_particle import SensorParticle
from hook_arm import HookArm


class Scene:
    def __init__(self, app: "BuilderApp") -> None:
        self.app = app

    # removals ----------------------------------------------------------
    def remove_entities(
        self,
        particles: Iterable[Particle] = (),
        springs: Iterable[Spring] = (),
        bends: Iterable[BendingSpring] = (),
        arms: Iterable[HookArm] = (),
        sensors: Iterable[SensorParticle] = (),
    ) -> None:
        a = self.app
        parts_set = set(particles)
        springs_set = set(springs)
        bends_set = set(bends)
        arms_set = set(arms)
        sensors_set = set(sensors)
        parts_set.update(sensors_set)

        # remove arms explicitly passed or those referencing removed particles
        for arm in list(a.arms):
            if arm in arms_set or any(p in parts_set for p in arm.particles):
                self._remove_arm(arm)
                parts_set.difference_update(arm.particles)
                springs_set.difference_update(arm.springs)

        # remove springs either passed explicitly or attached to removed particles
        if parts_set or springs_set:
            for s in list(a.springs):
                if s in springs_set or s.p1 in parts_set or s.p2 in parts_set:
                    a.springs.remove(s)
                    if isinstance(s, VariableSpring):
                        if s in a.variable_springs:
                            a.variable_springs.remove(s)
                        if s.key is not None and s.key in a.vspring_keys:
                            lst = a.vspring_keys[s.key]
                            if s in lst:
                                lst.remove(s)
                            if not lst:
                                del a.vspring_keys[s.key]
                        a.update_channel(s, None)

        # remove bending springs tied to removed particles or specified directly
        if parts_set or bends_set:
            new_bends = []
            for bs in a.bending_springs:
                if (
                    bs not in bends_set
                    and bs.p1 not in parts_set
                    and bs.p2 not in parts_set
                    and bs.p3 not in parts_set
                ):
                    new_bends.append(bs)
                else:
                    if isinstance(bs, VariableBendingSpring):
                        if bs in a.variable_bending_springs:
                            a.variable_bending_springs.remove(bs)
                        if bs.key is not None and bs.key in a.vbend_keys:
                            lst = a.vbend_keys[bs.key]
                            if bs in lst:
                                lst.remove(bs)
                            if not lst:
                                del a.vbend_keys[bs.key]
                        a.update_channel(bs, None)
            a.bending_springs[:] = new_bends

        if sensors_set:
            for s in list(a.sensors):
                if s in sensors_set:
                    a.sensors.remove(s)

        # finally drop particles themselves
        for p in parts_set:
            if p in a.particles:
                a.particles.remove(p)
            if isinstance(p, VariableParticle) and p in a.variable_particles:
                a.variable_particles.remove(p)
                if p.key is not None and p.key in a.vparticle_keys:
                    lst = a.vparticle_keys[p.key]
                    if p in lst:
                        lst.remove(p)
                    if not lst:
                        del a.vparticle_keys[p.key]
                a.update_channel(p, None)

    def _remove_arm(self, arm: HookArm) -> None:
        a = self.app
        if arm in a.arms:
            a.arms.remove(arm)
        for key, arms in list(a.cycle_keys.items()):
            if arm in arms:
                arms.remove(arm)
                if not arms:
                    del a.cycle_keys[key]
        for s in arm.springs:
            if s in a.springs:
                a.springs.remove(s)
        for p in arm.particles:
            if p in a.particles:
                a.particles.remove(p)

    def _remove_bending(self, bend: BendingSpring) -> None:
        a = self.app
        if bend in a.bending_springs:
            a.bending_springs.remove(bend)
        if bend in a.selected_bends:
            a.selected_bends.remove(bend)
        if isinstance(bend, VariableBendingSpring):
            if bend in a.variable_bending_springs:
                a.variable_bending_springs.remove(bend)
            if bend.key is not None and bend.key in a.vbend_keys:
                lst = a.vbend_keys[bend.key]
                if bend in lst:
                    lst.remove(bend)
                if not lst:
                    del a.vbend_keys[bend.key]
        a.physics.bending_springs = a.bending_springs

    # restore -----------------------------------------------------------
    def restore_particle(self, p: Particle, springs: list[Spring]) -> None:
        a = self.app
        a.particles.append(p)
        a.springs.extend(springs)
        for s in springs:
            if isinstance(s, VariableSpring):
                a.variable_springs.append(s)
                a.register_variable_spring(s)
        if isinstance(p, VariableParticle):
            a.variable_particles.append(p)
            a.register_variable_particle(p)
        if isinstance(p, SensorParticle):
            a.sensors.append(p)
            a.register_sensor(p)

    def restore_spring(self, s: Spring) -> None:
        a = self.app
        a.springs.append(s)
        if isinstance(s, VariableSpring):
            a.variable_springs.append(s)
            a.register_variable_spring(s)

    def restore_entities(
        self,
        particles: list[Particle],
        springs: list[Spring],
        bends: list[BendingSpring] | None = None,
    ) -> None:
        a = self.app
        a.particles.extend(particles)
        a.springs.extend(springs)
        if bends:
            a.bending_springs.extend(bends)
            for b in bends:
                if isinstance(b, VariableBendingSpring):
                    a.variable_bending_springs.append(b)
                    a.register_variable_bend(b)
        for p in particles:
            if isinstance(p, VariableParticle):
                a.variable_particles.append(p)
                a.register_variable_particle(p)
        for s in springs:
            if isinstance(s, VariableSpring):
                a.variable_springs.append(s)
                a.register_variable_spring(s)

