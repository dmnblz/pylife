# renderer.py
import pygame

class Renderer:
    """Simple helper that draws particles, springs and bending springs."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen

    def _draw_dashed_line(self, start, end, color, width=1, dash=6):
        start = pygame.Vector2(start)
        end = pygame.Vector2(end)
        vec = end - start
        length = vec.length()
        if length == 0:
            return
        direction = vec.normalize()
        for i in range(0, int(length), dash * 2):
            s = start + direction * i
            e = start + direction * min(i + dash, length)
            pygame.draw.line(self.screen, color, s, e, width)

    def draw(self, particles: list, springs: list, bending_springs: list | None = None):
        """Render the simulation objects to the screen.

        Parameters
        ----------
        particles:
            Sequence of particles to draw.
        springs:
            Standard linear springs to draw.
        bending_springs:
            Optional list of ``BendingSpring`` objects which will be rendered as
            two connected segments.
        """
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

        # draw bending springs if provided
        if bending_springs:
            for bs in bending_springs:
                color = (200, 200, 0)
                self._draw_dashed_line(bs.p1.pos, bs.p2.pos, color, 3)
                self._draw_dashed_line(bs.p2.pos, bs.p3.pos, color, 3)

        # draw particles
        for p in particles:
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
