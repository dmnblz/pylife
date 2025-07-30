"""Helper class for a flexible hook arm.

A HookArm is a small chain of particles attached to a base particle. Its
springs can extend and contract, and the tip can enter a high-drag adhesion
state. The class supports a cycling motion that repeatedly extends the arm,
activates high drag and then retracts it.
"""

import pygame
from particle import Particle
from spring import Spring


class HookArm:
    """Represent a single flexible arm with simple control flags."""

    def __init__(self, base: Particle, direction: pygame.Vector2,
                 *, segments: int = 1, spacing: float = 20,
                 stiffness: float = 500, color=(0, 150, 255),
                 high_drag_color=(255, 50, 50),
                 adhesion_mass_factor: float = 10.0):
        """Create the arm anchored at ``base`` and pointing along ``direction``.

        Parameters
        ----------
        base:
            The particle the first segment attaches to.
        direction:
            Unit vector giving the initial arm direction.
        segments:
            Number of links making up the arm.
        spacing:
            Rest length between consecutive particles.
        stiffness:
            Spring stiffness for each connection.
        color:
            Default particle colour.
        high_drag_color:
            Colour used when the tip enters the high-drag state.
        adhesion_mass_factor:
            Multiplier applied to the tip's mass while adhesion is active.
        """
        self.particles: list[Particle] = []
        self.springs: list[Spring] = []
        self.color = color
        self.high_drag_color = high_drag_color
        self.adhesion_mass_factor = adhesion_mass_factor

        direction = direction.normalize()
        prev = base
        for i in range(1, segments + 1):
            pos = base.pos + direction * spacing * i
            p = Particle(pos, mass=0.5, radius=8, color=color, tag="arm")
            self.particles.append(p)
            s = Spring(prev, p, rest_length=spacing, stiffness=stiffness)
            self.springs.append(s)
            prev = p
        self.tip = prev
        self._orig_mass = self.tip.mass
        self._set_high_drag(False)

        self.rest_lengths = [s.rest_length for s in self.springs]
        self.max_lengths = [r * 4 for r in self.rest_lengths]

        self.extend_held = False
        self.contract_held = False
        self.cycle_held = False
        self.cycle_active = False
        self.cycle_phase = 0

    def _set_high_drag(self, enabled: bool):
        if enabled:
            self.tip.tag = "high_drag"
            self.tip.color = self.high_drag_color
            self.tip.mass = self._orig_mass * self.adhesion_mass_factor
        else:
            self.tip.tag = "arm"
            self.tip.color = self.color
            self.tip.mass = self._orig_mass

    def reset_inert(self):
        """Return the arm to its rest state with adhesion disabled."""
        for i, s in enumerate(self.springs):
            s.rest_length = self.rest_lengths[i]
        self._set_high_drag(False)
        self.cycle_active = False
        self.cycle_phase = 0

    def update(self, dt: float):
        for i, s in enumerate(self.springs):
            if self.extend_held and s.rest_length < self.max_lengths[i]:
                s.rest_length += 240 * dt
            if self.contract_held and s.rest_length > self.rest_lengths[i]:
                s.rest_length -= 240 * dt

        if self.cycle_held:
            if not self.cycle_active:
                self.cycle_active = True
                self.cycle_phase = 0
            if self.cycle_phase == 0:
                done = True
                for i, s in enumerate(self.springs):
                    if s.rest_length < self.max_lengths[i]:
                        s.rest_length += 240 * dt
                        done = False
                if done:
                    for i, s in enumerate(self.springs):
                        s.rest_length = self.max_lengths[i]
                    self._set_high_drag(True)
                    self.cycle_phase = 1
            elif self.cycle_phase == 1:
                done = True
                for i, s in enumerate(self.springs):
                    if s.rest_length > self.rest_lengths[i]:
                        s.rest_length -= 240 * dt
                        done = False
                if done:
                    for i, s in enumerate(self.springs):
                        s.rest_length = self.rest_lengths[i]
                    self._set_high_drag(False)
                    # loop or finish depending on key state
                    if self.cycle_held:
                        self.cycle_phase = 0
                    else:
                        self.cycle_active = False
        else:
            if self.cycle_active:
                self.reset_inert()
