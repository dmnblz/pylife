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
            pygame.draw.line(self.screen, (200, 200, 200), s.p1.pos, s.p2.pos, 5)
        # draw particles
        for p in particles:
            color = (255, 0, 0) if p.fixed else (0, 0, 255)
            pygame.draw.circle(self.screen, color, (int(p.pos.x), int(p.pos.y)), 10)



# import pygame
#
#
# class Renderer:
#     def __init__(self, screen):
#         self.screen = screen
#
#     def draw(self, particles, springs):
#         self.screen.fill((0, 0, 0))
#         # draw springs (skip broken)
#         for s in springs:
#             if getattr(s, "broken", False):
#                 continue
#             pygame.draw.line(
#                 self.screen,
#                 (200, 200, 200),
#                 (int(s.p1.pos.x), int(s.p1.pos.y)),
#                 (int(s.p2.pos.x), int(s.p2.pos.y)),
#                 2
#             )
#         # draw particles
#         for p in particles:
#             pygame.draw.circle(self.screen, (255, 255, 255), (int(p.pos.x), int(p.pos.y)), 5)
#         pygame.display.flip()
