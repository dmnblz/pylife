# renderer.py
import pygame

class Renderer:
    """Simple helper that draws particles, springs and bending springs."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        # camera parameters
        self.offset = pygame.Vector2(0, 0)  # world coords at screen (0,0)
        self.zoom = 1.0

    # ---------------- camera helpers -----------------------------------------
    def set_camera(self, offset: pygame.Vector2 | tuple[float, float], zoom: float) -> None:
        self.offset = pygame.Vector2(offset)
        self.zoom = max(0.01, float(zoom))

    def world_to_screen(self, v: pygame.Vector2 | tuple[float, float]) -> pygame.Vector2:
        p = pygame.Vector2(v)
        return (p - self.offset) * self.zoom

    def screen_to_world(self, v: pygame.Vector2 | tuple[float, float]) -> pygame.Vector2:
        p = pygame.Vector2(v)
        return p / self.zoom + self.offset

    def draw_play_area(self, rect: pygame.Rect, color=(80, 80, 80)) -> None:
        """Draw the world-space playable area rectangle."""
        tl = self.world_to_screen((rect.left, rect.top))
        tr = self.world_to_screen((rect.right, rect.top))
        br = self.world_to_screen((rect.right, rect.bottom))
        bl = self.world_to_screen((rect.left, rect.bottom))
        pygame.draw.lines(self.screen, color, True, [tl, tr, br, bl], 2)

    def _draw_dashed_line(self, start, end, color, width=1, dash=6):
        start = self.world_to_screen(start)
        end = self.world_to_screen(end)
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
            p1 = self.world_to_screen(s.p1.pos)
            p2 = self.world_to_screen(s.p2.pos)
            pygame.draw.line(self.screen, color, p1, p2, max(1, int(3)))

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
            center = self.world_to_screen(p.pos)
            pygame.draw.circle(self.screen, color, (int(center.x), int(center.y)), radius=max(1, int(radius * self.zoom)))
            if getattr(p, "drag", 1.0) > 1.0:
                pygame.draw.circle(
                    self.screen,
                    (255, 50, 50),
                    (int(center.x), int(center.y)),
                    max(1, int(radius * self.zoom) + 4),
                    width=2,
                )
