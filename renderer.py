# renderer.py
import pygame
from pygame import gfxdraw
from builder_ui import theme

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

    def draw_background(self, play_area: pygame.Rect) -> None:
        """Fill the entire background with a solid theme color (no gradient)."""
        self.screen.fill(theme.BG_CANVAS_TOP)

    def draw_play_area(self, rect: pygame.Rect, color=(80, 80, 90)) -> None:
        """Draw the world-space playable area rectangle with rounded corners."""
        tl = self.world_to_screen((rect.left, rect.top))
        br = self.world_to_screen((rect.right, rect.bottom))
        screen_rect = pygame.Rect(int(tl.x), int(tl.y), int(br.x - tl.x), int(br.y - tl.y))
        # subtle shadow
        shadow = screen_rect.move(2, 2)
        pygame.draw.rect(self.screen, (0, 0, 0), shadow, width=2, border_radius=12)
        # frame
        pygame.draw.rect(self.screen, color, screen_rect, width=2, border_radius=12)

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

    def draw(self, particles: list, springs: list, bending_springs: list | None = None,
             hover_particle=None, hover_spring=None, hover_bend=None):
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
            color = s.get_color() if hasattr(s, "get_color") else (200, 200, 220)
            p1 = self.world_to_screen(s.p1.pos)
            p2 = self.world_to_screen(s.p2.pos)
            # thickness based on strain
            try:
                rest = float(s.rest_length)
            except Exception:
                rest = (s.p2.pos - s.p1.pos).length()
            curr = (s.p2.pos - s.p1.pos).length()
            strain = abs(curr - rest) / max(1.0, rest)
            width = max(1, min(6, int(1 + 2 * self.zoom + 3 * strain)))
            # main line only (no heavy shadow)
            pygame.draw.line(self.screen, color, p1, p2, width)

        # draw bending springs if provided
        if bending_springs:
            for bs in bending_springs:
                color = (200, 200, 0)
                self._draw_dashed_line(bs.p1.pos, bs.p2.pos, color, 3)
                self._draw_dashed_line(bs.p2.pos, bs.p3.pos, color, 3)

        # draw particles
        for p in particles:
            color = p.color if p.color else (0, 114, 255)
            base_radius = p.radius if p.radius else 10
            radius = max(1, int(base_radius * self.zoom))
            center = self.world_to_screen(p.pos)
            cx, cy = int(center.x), int(center.y)
            # no shadow
            # body with AA
            try:
                gfxdraw.filled_circle(self.screen, cx, cy, radius, color)
                gfxdraw.aacircle(self.screen, cx, cy, radius, (255, 255, 255))
            except Exception:
                pygame.draw.circle(self.screen, color, (cx, cy), radius)
            # rings for selection/hover (accent) and high-drag (distinct red)
            is_selected_or_hover = getattr(p, "selected", False) or (hover_particle is p)
            is_high_drag = getattr(p, "drag", 1.0) > 1.0
            if is_selected_or_hover:
                try:
                    gfxdraw.aacircle(self.screen, cx, cy, radius + 6, theme.ACCENT)
                    gfxdraw.aacircle(self.screen, cx, cy, radius + 7, theme.ACCENT)
                except Exception:
                    pygame.draw.circle(self.screen, theme.ACCENT, (cx, cy), radius + 7, width=2)
            if is_high_drag and not is_selected_or_hover:
                ring_color = (255, 60, 60)
                try:
                    gfxdraw.aacircle(self.screen, cx, cy, radius + 5, ring_color)
                    gfxdraw.aacircle(self.screen, cx, cy, radius + 6, ring_color)
                except Exception:
                    pygame.draw.circle(self.screen, ring_color, (cx, cy), radius + 6, width=2)

        # overlay hover highlights for springs/bends
        if hover_spring is not None:
            p1 = self.world_to_screen(hover_spring.p1.pos)
            p2 = self.world_to_screen(hover_spring.p2.pos)
            pygame.draw.line(self.screen, theme.ACCENT, p1, p2, 4)
        if hover_bend is not None:
            p1 = self.world_to_screen(hover_bend.p1.pos)
            p2 = self.world_to_screen(hover_bend.p2.pos)
            p3 = self.world_to_screen(hover_bend.p3.pos)
            pygame.draw.line(self.screen, theme.ACCENT, p1, p2, 4)
            pygame.draw.line(self.screen, theme.ACCENT, p2, p3, 4)
