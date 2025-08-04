"""Demo of a triangular wall using springs and bending constraints.

Keys D/F/G shorten selected springs while B/N/M toggle drag on
corresponding particles. Other controls match those in ``start.py``.
"""

import pygame
import math
import random

from particle import Particle
from physics import PhysicsEngine
from renderer import Renderer
from spring import Spring
from bending_spring import BendingSpring
from structures import create_bending_wall

# SCREEN_SIZE = (1300, 900)
SCREEN_SIZE = (1800, 1200)
FPS = 120


class CellWallApp:
    """Drag with the mouse and use D/F/G or B/N/M for spring and drag tweaks."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        self.particles = []
        self.springs = []
        self.bending_springs = []
        self.selected = None

        center = pygame.Vector2(SCREEN_SIZE) / 2

        # Create the wall
        wall1_particles, wall1_springs, wall1_bending_springs = create_bending_wall(
            center,
            radius=100,
            # segments=3,
            segments=3,
            tag="spring1",
            color=(255, 0, 0),
            # stiffness=2000,
            stiffness=200,
            # bending_stiffness=50000
            bending_stiffness=5000
        )

        for p in wall1_particles:
            p.mass = 1
            # p.tag = "wall"  # Important for friction

        self.particles.extend(wall1_particles)
        self.springs.extend(wall1_springs)
        self.bending_springs.extend(wall1_bending_springs)

        self.physics = PhysicsEngine(
            self.particles,
            self.springs,
            self.bending_springs,
            # gravity=(0, 2500),
            gravity=(0, 0),
            repulsion_radius=30,
            repulsion_strength=10000,
            temperature=0,
            damping_coeff=1
        )

        self.renderer = Renderer(self.screen)

        self.clamp_to_window = True
        self.bouncy_clamp = False
        self.periodic_boundary = False

    def run(self):
        key_held = {'d': False, 'f': False, 'g': False}
        spring_keys = {'d': 0, 'f': 1, 'g': 2}
        drag_held = {'b': False, 'n': False, 'm': False}
        drag_keys = {'b': 0, 'n': 1, 'm': 2}
        original_rest_lengths = [spring.rest_length for spring in self.springs]

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
                    if e.key == pygame.K_d:
                        key_held['d'] = True
                    elif e.key == pygame.K_f:
                        key_held['f'] = True
                    elif e.key == pygame.K_g:
                        key_held['g'] = True
                    elif e.key == pygame.K_k:
                        for spring in self.springs:
                            spring.stiffness = max(spring.stiffness - 50, 0)
                        print(f"Spring Stiffness: {spring.stiffness}")
                    elif e.key == pygame.K_l:
                        for spring in self.springs:
                            spring.stiffness += 50
                        print(f"Spring Stiffness: {spring.stiffness}")
                    elif e.key == pygame.K_b:
                        drag_held['b'] = True
                    elif e.key == pygame.K_n:
                        drag_held['n'] = True
                    elif e.key == pygame.K_m:
                        drag_held['m'] = True
                    # elif e.key == pygame.K_n:
                    #     self.physics.temperature = max(self.physics.temperature - 50, 0)
                    #     print(f"Temperature: {self.physics.temperature}")
                    # elif e.key == pygame.K_m:
                    #     self.physics.temperature += 50
                    #     print(f"Temperature: {self.physics.temperature}")
                    elif e.key == pygame.K_o:
                        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
                        p = Particle(mouse_pos, mass=0.1, color=(0, 255, 0), radius=5)
                        p.tag = "loose"
                        self.particles.append(p)
                    elif e.key == pygame.K_p:
                        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
                        for _ in range(10):
                            p = Particle(mouse_pos, mass=0.1, color=(0, 255, 0), radius=5)
                            p.tag = "loose"
                            self.particles.append(p)
                    elif e.key == pygame.K_q:
                        for p in self.particles:
                            if p.tag == "loose":
                                p.fixed = True
                    elif e.key == pygame.K_w:
                        for p in self.particles:
                            if p.tag == "loose":
                                p.fixed = False

                elif e.type == pygame.KEYUP:
                    if e.key == pygame.K_d:
                        key_held['d'] = False
                    elif e.key == pygame.K_f:
                        key_held['f'] = False
                    elif e.key == pygame.K_g:
                        key_held['g'] = False
                    elif e.key == pygame.K_b:
                        drag_held['b'] = False
                    elif e.key == pygame.K_n:
                        drag_held['n'] = False
                    elif e.key == pygame.K_m:
                        drag_held['m'] = False

            for key, index in spring_keys.items():
                if index < len(self.springs):
                    if key_held[key]:
                        self.springs[index].rest_length = max(self.springs[index].rest_length - 10, 30)
                    else:
                        self.springs[index].rest_length = original_rest_lengths[index]

            for key, index in drag_keys.items():
                if index < len(self.particles):
                    if drag_held[key]:
                        self.particles[index].drag = 100.0
                    else:
                        self.particles[index].drag = 1.0

            if self.selected:
                self.selected.pos = pygame.Vector2(pygame.mouse.get_pos())
                self.selected.prev_pos = self.selected.pos.copy()

            self.physics.update(dt)

            # Clamp particles to window
            W, H = SCREEN_SIZE
            if self.clamp_to_window:
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


if __name__ == '__main__':
    CellWallApp().run()