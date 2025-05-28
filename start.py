# main.py
import math
import random

import pygame

from particle import Particle
from physics import PhysicsEngine
from renderer import Renderer
from spring import Spring

SCREEN_SIZE = (800, 600)
FPS = 60


class CellWallApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        self.particles = []
        self.springs = []
        self.selected = None

        self._create_wall()
        # self._create_wall(radius=10, segments=10)
        # self._loose_particles(count=40)
        self.physics = PhysicsEngine(self.particles, self.springs, gravity=(0, 0),
                                     repulsion_radius=100, repulsion_strength=100,
                                     # repulsion_radius=150, repulsion_strength=100,
                                     # repulsion_radius=30, repulsion_strength=1000,
                                     temperature=500, damping_coeff=1)
        self.renderer = Renderer(self.screen)
        self.clamp_to_window = True
        self.bouncy_clamp = False
        self.periodic_boundary = False

    def _create_wall(self, radius=100, segments=100):
        particle_counter = len(self.particles)
        center = pygame.Vector2(SCREEN_SIZE) / 2
        for i in range(segments):
            theta = (i / segments) * 2 * math.pi
            pos = center + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
            p = Particle(pos, color=(round(i / segments * 255), 0, 255 - round(i / segments * 255)))
            self.particles.append(p)
        # connect adjacent with springs
        for i in range(segments):
            p1 = self.particles[particle_counter + i]
            p2 = self.particles[(particle_counter + i + 1) % (segments + particle_counter)]
            rest = (p2.pos - p1.pos).length()
            stiffness = 200
            # if i % 10 == 0:
            #     stiffness = 50
            # else:
            #     stiffness = 200
            self.springs.append(Spring(p1, p2, rest, stiffness=stiffness, max_force=None))
            # self.springs.append(Spring(p1, p2, rest, stiffness=stiffness, max_force=10000))

        # an optional spring
        # p1 = self.particles[0]
        # p2 = self.particles[segments//2]
        # rest = (p2.pos - p1.pos).length()
        # rest = 100
        # stiffness = 100
        # self.springs.append(Spring(p1, p2, rest, stiffness=stiffness))

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
