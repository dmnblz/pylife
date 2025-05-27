# main.py
import pygame
import math
from particle import Particle
from spring import Spring
from physics import PhysicsEngine
from renderer import Renderer

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
        self.physics = PhysicsEngine(self.particles, self.springs, gravity=(0, 0),
                                     repulsion_radius=100, repulsion_strength=100)
        self.renderer = Renderer(self.screen)

    def _create_wall(self):
        center = pygame.Vector2(SCREEN_SIZE) / 2
        radius = 100
        segments = 100
        for i in range(segments):
            theta = (i / segments) * 2 * math.pi
            pos = center + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
            p = Particle(pos)
            self.particles.append(p)
        # connect adjacent with springs
        for i in range(segments):
            p1 = self.particles[i]
            p2 = self.particles[(i + 1) % segments]
            rest = (p2.pos - p1.pos).length()
            stiffness = 200
            self.springs.append(Spring(p1, p2, rest, stiffness=stiffness, max_force=None))
            # self.springs.append(Spring(p1, p2, rest, stiffness=stiffness, max_force=10000))

        # an optional spring
        # p1 = self.particles[0]
        # p2 = self.particles[segments//2]
        # # rest = (p2.pos - p1.pos).length()
        # rest = 100
        # stiffness = 100
        # self.springs.append(Spring(p1, p2, rest, stiffness=stiffness))

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

            # drag selected
            if self.selected:
                # move it directly to the mouse without imparting velocity
                self.selected.pos = pygame.Vector2(pygame.mouse.get_pos())
                self.selected.prev_pos = self.selected.pos.copy()

            self.physics.update(dt)
            self.screen.fill((30, 30, 30))
            self.renderer.draw(self.particles, self.springs)
            pygame.display.flip()

        pygame.quit()


if __name__ == '__main__':
    CellWallApp().run()
