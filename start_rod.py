# main.py
import math
import random

import pygame

from particle import Particle
from physics import PhysicsEngine
from renderer import Renderer
from spring import Spring
from structures import create_wall, create_wall_rod, create_rod

# SCREEN_SIZE = (800, 600)
# SCREEN_SIZE = (800 * 2, 600 * 2)
# SCREEN_SIZE = (1500, 900)
SCREEN_SIZE = (1300, 900)
FPS = 60
# FPS = 120


class CellWallApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        self.particles = []
        self.springs = []
        self.selected = None

        center = pygame.Vector2(SCREEN_SIZE) / 2
        loc1 = center - pygame.Vector2((0, -300))
        loc2 = center - pygame.Vector2((0, 300))
        # wall1_particles, wall1_springs = create_wall_rod(loc1, radius=100, segments=200, tag="spring1",
        #                                                  stiffness=2000, max_force=None)
        # wall2_particles, wall2_springs = create_wall_rod(loc2, radius=100, segments=100, tag="spring1",
        #                                                  stiffness=2000, max_force=None)
        wall2_particles, wall2_springs = create_rod(center, radius=100, length=300, segments=50, tag="spring1",
                                                    stiffness=200, max_force=None,
                                                    include_cytoskeleton=True, cyto_stiffness=200)
        self.particles.extend(wall2_particles)
        self.springs.extend(wall2_springs)
        # self._loose_particles(count=40)

        self.physics = PhysicsEngine(self.particles, self.springs, gravity=(0, 0),
                                     # repulsion_radius=100, repulsion_strength=100,
                                     # repulsion_radius=100, repulsion_strength=1000,
                                     # repulsion_radius=150, repulsion_strength=100,
                                     repulsion_radius=30, repulsion_strength=1000,
                                     # repulsion_radius=30, repulsion_strength=10000,
                                     # repulsion_radius=0, repulsion_strength=10000,
                                     temperature=0, damping_coeff=1)
                                     # temperature=0, damping_coeff=1)
                                     # temperature=0, damping_coeff=0)
        self.renderer = Renderer(self.screen)
        self.clamp_to_window = True
        self.bouncy_clamp = False
        self.periodic_boundary = False

    def _loose_particles(self, count=20):
        """Add `count` free-floating particles randomly inside the cell wall."""
        # center and radius must match the wall
        center = pygame.Vector2(SCREEN_SIZE) / 2
        radius = 100 * 0.9  # slightly inside the wall
        for i in range(count):
            theta = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, radius)
            pos = center + pygame.Vector2(math.cos(theta), math.sin(theta)) * r
            # p = Particle(pos, mass=0.1, color=(255 - i * 5, i * 5, 0), radius=5)
            p = Particle(pos, mass=0.1, color=(0, 255, 0), radius=5)
            p.tag = "loose"
            self.particles.append(p)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    # select nearest particle
                    mouse = pygame.Vector2(e.pos)
                    self.selected = min(self.particles, key=lambda p: (p.pos - mouse).length())
                    self.selected.fixed = True
                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    if self.selected:
                        self.selected.fixed = False
                    self.selected = None
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_o:
                    # spawn a new loose particle at the mouse position
                    mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
                    p = Particle(mouse_pos, mass=0.1, color=(0, 255, 0), radius=5)
                    p.tag = "loose"
                    self.particles.append(p)
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_p:
                    # spawn a new loose particle at the mouse position
                    mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
                    for _ in range(10):
                        p = Particle(mouse_pos, mass=0.1, color=(0, 255, 0), radius=5)
                        # p = Particle(mouse_pos, mass=0.1, color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), radius=5)
                        p.tag = "loose"
                        self.particles.append(p)
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_k:
                    for spring in self.springs:
                        spring.stiffness = max(spring.stiffness - 50, 0)
                    print(f"Spring Stiffnes: {spring.stiffness}")
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_l:
                    for spring in self.springs:
                        spring.stiffness = spring.stiffness + 50
                    print(f"Spring Stiffnes: {spring.stiffness}")

                elif e.type == pygame.KEYDOWN and e.key == pygame.K_n:
                    self.physics.temperature = max(self.physics.temperature - 50, 0)
                    print(f"Temperature: {self.physics.temperature}")
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_m:
                    self.physics.temperature += 50
                    print(f"Temperature: {self.physics.temperature}")

                elif e.type == pygame.KEYDOWN and e.key == pygame.K_q:
                    # delete all loose particles
                    for p in self.particles:
                        if p.tag == "loose":
                            p.fixed = True
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_w:
                    # delete all loose particles
                    for p in self.particles:
                        if p.tag == "loose":
                            p.fixed = False

            # drag selected
            if self.selected:
                # move it directly to the mouse without imparting velocity
                self.selected.pos = pygame.Vector2(pygame.mouse.get_pos())
                self.selected.prev_pos = self.selected.pos.copy()

            self.physics.update(dt)
            # handle window boundaries
            W, H = SCREEN_SIZE
            if self.periodic_boundary:
                # wrap-around
                for p in self.particles:
                    p.pos.x %= W
                    p.pos.y %= H
                    p.prev_pos.x %= W
                    p.prev_pos.y %= H
            elif self.clamp_to_window:
                if self.bouncy_clamp:
                    # existing reflective code...
                    for p in self.particles:
                        v = p.pos - p.prev_pos
                        if p.pos.x < 0 or p.pos.x > W:
                            p.pos.x = max(0, min(p.pos.x, W))
                            p.prev_pos.x = p.pos.x + (-v.x)
                        if p.pos.y < 0 or p.pos.y > H:
                            p.pos.y = max(0, min(p.pos.y, H))
                            p.prev_pos.y = p.pos.y + (-v.y)
                else:
                    # existing simple clamp
                    for p in self.particles:
                        if p.pos.x < 0:
                            p.pos.x = 0;
                            p.prev_pos.x = p.pos.x
                        elif p.pos.x > W:
                            p.pos.x = W;
                            p.prev_pos.x = p.pos.x
                        if p.pos.y < 0:
                            p.pos.y = 0;
                            p.prev_pos.y = p.pos.y
                        elif p.pos.y > H:
                            p.pos.y = H;
                            p.prev_pos.y = p.pos.y

            self.screen.fill((30, 30, 30))
            self.renderer.draw(self.particles, self.springs)
            pygame.display.flip()

        pygame.quit()


if __name__ == '__main__':
    CellWallApp().run()
