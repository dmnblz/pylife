# renderer.py
import pygame

class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen

    def draw(self, particles: list, springs: list):
        # draw springs
        for s in springs:
            if getattr(s, "broken", False):
                continue
            if s.invisible:
                continue
            pygame.draw.line(self.screen, (200, 200, 200), s.p1.pos, s.p2.pos, 5)

        # draw particles
        for p in particles:
            # color = (255, 0, 0) if p.fixed else (0, 0, 255)
            color = p.color if p.color else (0, 0, 255)
            radius = p.radius if p.radius else 10
            pygame.draw.circle(self.screen, color, (int(p.pos.x), int(p.pos.y)), radius=radius)
