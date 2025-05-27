# renderer.py
import pygame

class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen

    def draw(self, particles: list, springs: list):
        # draw springs
        for s in springs:
            pygame.draw.line(self.screen, (200, 200, 200), s.p1.pos, s.p2.pos, 5)
        # draw particles
        for p in particles:
            color = (255, 0, 0) if p.fixed else (0, 0, 255)
            pygame.draw.circle(self.screen, color, (int(p.pos.x), int(p.pos.y)), 10)


