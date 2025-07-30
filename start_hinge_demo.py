"""Simple demo showcasing particles with hinge orientation.

A central particle holds an orientation arrow. A second particle is attached
with a spring and hinge constraint. The base orientation slowly rotates so the
other particle moves around like connected by a rigid hinge.
"""

import pygame
from particle import Particle
from spring import Spring
from hinge import HingeSpring
from physics import PhysicsEngine
from renderer import Renderer

SCREEN_SIZE = (800, 600)
FPS = 60


class HingeApp:
    """Rotate the base orientation to demonstrate hinge behaviour."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        self.particles = []
        self.springs = []
        self.hinges = []
        self._create_setup()
        self.engine = PhysicsEngine(
            self.particles, self.springs, hinge_springs=self.hinges, gravity=(0, 0)
        )
        self.renderer = Renderer(self.screen)

    def _create_setup(self):
        center = pygame.Vector2(SCREEN_SIZE) / 2
        base = Particle(center, radius=12, color=(0, 200, 255), orientation=0)
        tip_pos = center + pygame.Vector2(100, 0)
        tip = Particle(tip_pos, radius=8, color=(255, 200, 0))
        self.particles.extend([base, tip])
        rest = (tip.pos - base.pos).length()
        self.springs.append(Spring(base, tip, rest, stiffness=200))
        self.hinges.append(HingeSpring(base, tip, rest_angle=0, stiffness=2))
        self.base = base

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False

            # slowly rotate the base orientation
            self.base.orientation += dt
            self.engine.update(dt)
            self.screen.fill((30, 30, 30))
            self.renderer.draw(self.particles, self.springs)
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    HingeApp().run()
