"""Demo of a cell with a flexible hook arm.

Controls:
    - Hold **E** to extend the arm.
    - Hold **Q** to retract it.
    - Press **H** to toggle adhesion (high drag) on the tip.
    - Press **C** to run a full extend/adhere/contract cycle.

When a particle is in high-drag mode it is drawn in red so the adhesion
state is visible. Drag particles with the left mouse button.
"""

import pygame
import math

from particle import Particle
from physics import PhysicsEngine
from renderer import Renderer
from spring import Spring
from structures import create_wall

SCREEN_SIZE = (1300, 900)
FPS = 120


class HookArmApp:
    """Interactive demo of a single hook arm attached to a circular cell."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        self.particles: list[Particle] = []
        self.springs: list[Spring] = []
        self.arm_springs: list[Spring] = []
        self.selected = None

        self.arm_color = (0, 150, 255)
        self.high_drag_color = (255, 50, 50)

        center = pygame.Vector2(SCREEN_SIZE) / 2
        wall_particles, wall_springs = create_wall(center, radius=100, segments=40,
                                                   tag="cell", stiffness=2000)
        self.particles.extend(wall_particles)
        self.springs.extend(wall_springs)

        # build a small chain as the hook arm
        base = wall_particles[0]
        arm_segments = 1
        spacing = 50
        prev = base
        for i in range(1, arm_segments + 1):
            pos = base.pos + pygame.Vector2(spacing * i, 0)
            p = Particle(pos, mass=0.5, radius=8, color=self.arm_color, tag="arm")
            self.particles.append(p)
            s = Spring(prev, p, rest_length=spacing, stiffness=500)
            self.springs.append(s)
            self.arm_springs.append(s)
            prev = p
        self.arm_tip = prev
        self._set_high_drag(False)

        self.arm_rest_lengths = [s.rest_length for s in self.arm_springs]
        self.arm_max = [rest * 4 for rest in self.arm_rest_lengths]

        self.physics = PhysicsEngine(
            self.particles,
            self.springs,
            gravity=(0, 0),
            repulsion_radius=30,
            repulsion_strength=1000,
            temperature=0,
            damping_coeff=1,
        )
        self.renderer = Renderer(self.screen)

        self.clamp_to_window = True
        self.extend_held = False
        self.contract_held = False
        self.cycle_active = False
        self.cycle_phase = 0

    def _set_high_drag(self, enabled: bool):
        """Enable or disable high-drag mode on the arm tip."""
        if enabled:
            self.arm_tip.tag = "high_drag"
            self.arm_tip.color = self.high_drag_color
        else:
            self.arm_tip.tag = "arm"
            self.arm_tip.color = self.arm_color

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    mouse = pygame.Vector2(e.pos)
                    self.selected = min(self.particles, key=lambda p: (p.pos - mouse).length())
                    self.selected.fixed = True
                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    if self.selected:
                        self.selected.fixed = False
                    self.selected = None
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_e:
                        self.extend_held = True
                    elif e.key == pygame.K_q:
                        self.contract_held = True
                    elif e.key == pygame.K_h:
                        self._set_high_drag(getattr(self.arm_tip, "tag", "") != "high_drag")
                    elif e.key == pygame.K_c:
                        if not self.cycle_active:
                            self.cycle_active = True
                            self.cycle_phase = 0
                            self.extend_held = False
                            self.contract_held = False
                elif e.type == pygame.KEYUP:
                    if e.key == pygame.K_e:
                        self.extend_held = False
                    elif e.key == pygame.K_q:
                        self.contract_held = False

            if self.selected:
                self.selected.pos = pygame.Vector2(pygame.mouse.get_pos())
                self.selected.prev_pos = self.selected.pos.copy()

            for i, s in enumerate(self.arm_springs):
                if self.extend_held and s.rest_length < self.arm_max[i]:
                    s.rest_length += 120 * dt
                if self.contract_held and s.rest_length > self.arm_rest_lengths[i]:
                    s.rest_length -= 120 * dt

            if self.cycle_active:
                if self.cycle_phase == 0:
                    done = True
                    for i, s in enumerate(self.arm_springs):
                        if s.rest_length < self.arm_max[i]:
                            s.rest_length += 120 * dt
                            done = False
                    if done:
                        for i, s in enumerate(self.arm_springs):
                            s.rest_length = self.arm_max[i]
                        self._set_high_drag(True)
                        self.cycle_phase = 1
                elif self.cycle_phase == 1:
                    done = True
                    for i, s in enumerate(self.arm_springs):
                        if s.rest_length > self.arm_rest_lengths[i]:
                            s.rest_length -= 120 * dt
                            done = False
                    if done:
                        for i, s in enumerate(self.arm_springs):
                            s.rest_length = self.arm_rest_lengths[i]
                        self._set_high_drag(False)
                        self.cycle_active = False

            self.physics.update(dt)

            if self.clamp_to_window:
                W, H = SCREEN_SIZE
                for p in self.particles:
                    if p.pos.x < 0:
                        p.pos.x = 0
                        p.prev_pos.x = p.pos.x
                    elif p.pos.x > W:
                        p.pos.x = W
                        p.prev_pos.x = p.pos.x
                    if p.pos.y < 0:
                        p.pos.y = 0
                        p.prev_pos.y = p.pos.y
                    elif p.pos.y > H:
                        p.pos.y = H
                        p.prev_pos.y = p.pos.y

            self.screen.fill((30, 30, 30))
            self.renderer.draw(self.particles, self.springs)
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    HookArmApp().run()
