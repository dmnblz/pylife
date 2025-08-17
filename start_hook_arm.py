"""Demo of four flexible hook arms around a circular cell.

Hold **W**, **A**, **S** or **D** to cycle the matching arm through an
extend/adhere/contract loop.  Releasing the key returns the arm to its
rest state with adhesion disabled.  Keys **E**, **Q** and **H** still
extend, contract or toggle adhesion on all arms simultaneously.

High-drag particles draw with a red outline so adhesion is visible.
Drag particles with the left mouse button.
"""

import pygame

from particle import Particle
from physics import PhysicsEngine
from renderer import Renderer
from builder_ui import theme
from structures import create_wall
from hook_arm import HookArm

SCREEN_SIZE = (1300, 900)
FPS = 120


class HookArmApp:
    """Interactive demo of multiple hook arms attached to a cell wall."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.particles: list[Particle] = []
        self.springs = []
        self.selected = None

        center = pygame.Vector2(SCREEN_SIZE) / 2
        wall_particles, wall_springs = create_wall(center, radius=100, segments=40,
                                                   tag="cell", stiffness=2000)
        self.particles.extend(wall_particles)
        self.springs.extend(wall_springs)

        # Create four arms around the cell at 90-degree intervals
        idx = [0, 10, 20, 30]
        self.arms: list[HookArm] = []
        for i in idx:
            base = wall_particles[i]
            direction = (base.pos - center).normalize()
            arm = HookArm(base, direction)
            self.arms.append(arm)
            self.particles.extend(arm.particles)
            self.springs.extend(arm.springs)

        max_r = max((p.radius for p in self.particles), default=0)
        self.physics = PhysicsEngine(
            self.particles,
            self.springs,
            gravity=(0, 0),
            repulsion_radius=30,
            repulsion_strength=1000,
            temperature=0,
            damping_coeff=1,
            collision_bucket_size=max_r * 2,
        )
        # Fixed timestep keeps arms stable at variable frame times
        self.physics.set_fixed_timestep(1.0 / FPS, substeps=2)
        self.renderer = Renderer(self.screen)

        self.clamp_to_window = True

        # map keys to individual arms for cycling
        self.cycle_keys = {
            pygame.K_w: self.arms[0],
            pygame.K_a: self.arms[1],
            pygame.K_s: self.arms[2],
            pygame.K_d: self.arms[3],
        }

    def run(self):
        running = True
        # inform physics of current window size
        self.physics.set_screen_size(*self.screen.get_size())

        while running:
            dt = self.clock.tick(FPS) / 1000
            for e in pygame.event.get():
                if e.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                    self.renderer.screen = self.screen
                    self.physics.set_screen_size(e.w, e.h)
                    continue
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
                        for arm in self.arms:
                            arm.extend_held = True
                    elif e.key == pygame.K_q:
                        for arm in self.arms:
                            arm.contract_held = True
                    elif e.key == pygame.K_h:
                        for arm in self.arms:
                            arm._set_high_drag(arm.tip.drag <= arm._orig_drag)
                    elif e.key in self.cycle_keys:
                        self.cycle_keys[e.key].cycle_held = True
                elif e.type == pygame.KEYUP:
                    if e.key == pygame.K_e:
                        for arm in self.arms:
                            arm.extend_held = False
                    elif e.key == pygame.K_q:
                        for arm in self.arms:
                            arm.contract_held = False
                    elif e.key in self.cycle_keys:
                        arm = self.cycle_keys[e.key]
                        arm.cycle_held = False
                        arm.reset_inert()

            if self.selected:
                self.selected.pos = pygame.Vector2(pygame.mouse.get_pos())
                self.selected.prev_pos = self.selected.pos.copy()

            for arm in self.arms:
                arm.update(dt)

            self.physics.update(dt)

            if self.clamp_to_window:
                W, H = self.screen.get_size()
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

            # themed background
            self.renderer.draw_background(pygame.Rect(0, 0, *self.screen.get_size()))
            self.renderer.draw(self.particles, self.springs)
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    HookArmApp().run()
