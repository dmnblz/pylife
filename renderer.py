# renderer.py
import pygame
import math

class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen

    def draw(self, particles: list, springs: list):
        # draw springs
        for s in springs:
            if getattr(s, "broken", False):
                continue
            if getattr(s, "invisible", False):
                continue
                
            # Use the spring's color based on stretch/compression if available
            if hasattr(s, "get_color"):
                color = s.get_color()
            else:
                color = (200, 200, 200)  # Default gray for backward compatibility
                
            pygame.draw.line(self.screen, color, s.p1.pos, s.p2.pos, 5)

        # draw particles
        for p in particles:
            # color = (255, 0, 0) if p.fixed else (0, 0, 255)
            color = p.color if p.color else (0, 0, 255)
            radius = p.radius if p.radius else 10
            pygame.draw.circle(self.screen, color, (int(p.pos.x), int(p.pos.y)), radius=radius)
            if getattr(p, "tag", "") == "high_drag":
                pygame.draw.circle(
                    self.screen,
                    (255, 50, 50),
                    (int(p.pos.x), int(p.pos.y)),
                    radius + 4,
                    width=2,
                )

            if getattr(p, "orientation", None) is not None:
                angle = p.orientation
                arrow_len = radius + 15
                end = pygame.Vector2(
                    p.pos.x + arrow_len * math.cos(angle),
                    p.pos.y + arrow_len * math.sin(angle),
                )
                pygame.draw.line(
                    self.screen, (255, 255, 255), p.pos, end, width=2
                )
                head_len = 6
                head_angle = math.radians(20)
                left = end + pygame.Vector2(
                    -head_len * math.cos(angle - head_angle),
                    -head_len * math.sin(angle - head_angle),
                )
                right = end + pygame.Vector2(
                    -head_len * math.cos(angle + head_angle),
                    -head_len * math.sin(angle + head_angle),
                )
                pygame.draw.polygon(
                    self.screen,
                    (255, 255, 255),
                    [end, left, right]
                )
