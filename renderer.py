"""World renderer with camera transforms and drawing helpers."""

import math
import pygame
from pygame import gfxdraw
from builder_ui import theme
from builder_ui.fonts import get_font

class Renderer:
    """Simple helper that draws particles, springs and bending springs."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        # camera parameters
        self.offset = pygame.Vector2(0, 0)  # world coords at screen (0,0)
        self.zoom = 1.0
        # cache for expensive background composition
        self._bg_cache_size: tuple[int, int] | None = None
        self._bg_theme: str | None = None
        self._bg_surface: pygame.Surface | None = None
        self.trails_enabled: bool = False

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

    def set_trails_enabled(self, enabled: bool) -> None:
        """Show or hide particle trails."""
        self.trails_enabled = bool(enabled)

    def reset_cache(self) -> None:
        """Drop cached background so it rebuilds on next draw."""
        self._bg_cache_size = None
        self._bg_theme = None
        self._bg_surface = None

    def draw_background(self, play_area: pygame.Rect) -> None:
        """Draw a smooth vertical gradient background with a subtle vignette.

        Optimized by caching per window size.
        """
        w, h = self.screen.get_size()
        size = (w, h)
        current_theme = theme.get_theme_name()
        if (
            self._bg_cache_size != size
            or self._bg_surface is None
            or self._bg_theme != current_theme
        ):
            # rebuild cache
            bg = pygame.Surface(size)
            top = theme.BG_CANVAS_TOP
            bot = theme.BG_CANVAS_BOTTOM
            for y in range(h):
                t = y / max(h - 1, 1)
                r = int(top[0] * (1 - t) + bot[0] * t)
                g = int(top[1] * (1 - t) + bot[1] * t)
                b = int(top[2] * (1 - t) + bot[2] * t)
                pygame.draw.line(bg, (r, g, b), (0, y), (w, y))
            vignette = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.ellipse(
                vignette,
                (0, 0, 0, 140),
                (-int(w * 0.1), -int(h * 0.2), int(w * 1.2), int(h * 1.4)),
                width=0,
            )
            bg.blit(vignette, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
            self._bg_surface = bg
            self._bg_cache_size = size
            self._bg_theme = current_theme
        # blit cached background
        if self._bg_surface is not None:
            self.screen.blit(self._bg_surface, (0, 0))

    def draw_play_area(self, rect: pygame.Rect) -> None:
        """Draw the world-space playable area rectangle.

        Colors adapt to the active theme and avoid expensive alpha fills by using
        light strokes only.
        """
        tl = self.world_to_screen((rect.left, rect.top))
        br = self.world_to_screen((rect.right, rect.bottom))
        screen_rect = pygame.Rect(int(tl.x), int(tl.y), int(br.x - tl.x), int(br.y - tl.y))
        # simple inner and outer strokes only
        pygame.draw.rect(
            self.screen,
            theme.BORDER_ACTIVE,
            screen_rect,
            width=1,
            border_radius=8,
        )
        pygame.draw.rect(
            self.screen,
            theme.BORDER,
            screen_rect.inflate(2, 2),
            width=2,
            border_radius=8,
        )

    def _draw_dashed_line(self, start, end, color, width=1, dash=6):
        start = self.world_to_screen(start)
        end = self.world_to_screen(end)
        vec = end - start
        length = vec.length()
        if length == 0:
            return
        direction = vec.normalize()
        # scale dash length with zoom to keep segment count roughly constant on screen
        dash_px = max(4, int(dash * max(1.0, self.zoom)))
        step = dash_px * 2
        for i in range(0, int(length), step):
            s = start + direction * i
            e = start + direction * min(i + dash_px, length)
            pygame.draw.line(self.screen, color, s, e, width)

    def draw(
        self,
        particles: list,
        springs: list,
        bending_springs: list | None = None,
        sensors: list | None = None,
        hover_particle=None,
        hover_spring=None,
        hover_bend=None,
    ):
        """Render the simulation objects to the screen.

        Channel numbers are shown next to sensors and variable elements. When
        hovering a sensor, all objects on its channel highlight.

        Parameters
        ----------
        particles:
            Sequence of particles to draw.
        springs:
            Standard linear springs to draw.
        bending_springs:
            Optional list of ``BendingSpring`` objects which will be rendered as
            two connected segments.
        sensors:
            Optional list of :class:`sensor_particle.SensorParticle` objects
            to outline.
        """
        screen_rect = self.screen.get_rect()
        font = get_font(18)
        hover_channel = None
        if hover_particle is not None and getattr(hover_particle, "sense_radius", None) is not None:
            hover_channel = getattr(hover_particle, "channel", None)

        if self.trails_enabled:
            trail_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            for p in particles:
                trail = getattr(p, "trail", None)
                if not trail or len(trail) < 2:
                    continue
                pts = [self.world_to_screen(v) for v in trail]
                base = p.color if p.color else (0, 114, 255)
                n = len(pts)
                for i in range(1, n):
                    alpha = int(255 * i / (n - 1))
                    pygame.draw.line(trail_surf, (*base, alpha), pts[i - 1], pts[i], 2)
            self.screen.blit(trail_surf, (0, 0))

        # draw springs with simple culling
        for s in springs:
            if getattr(s, "broken", False):
                continue
            if getattr(s, "invisible", False):
                continue
            color = s.get_color() if hasattr(s, "get_color") else (200, 200, 220)
            p1 = self.world_to_screen(s.p1.pos)
            p2 = self.world_to_screen(s.p2.pos)
            try:
                rest = float(s.rest_length)
            except Exception:
                rest = (s.p2.pos - s.p1.pos).length()
            curr = (s.p2.pos - s.p1.pos).length()
            strain = abs(curr - rest) / max(1.0, rest)
            width = max(1, min(6, int(1 + 2 * self.zoom + 3 * strain)))
            seg_min_x = int(min(p1.x, p2.x)) - width
            seg_max_x = int(max(p1.x, p2.x)) + width
            seg_min_y = int(min(p1.y, p2.y)) - width
            seg_max_y = int(max(p1.y, p2.y)) + width
            if seg_max_x < 0 or seg_min_x > screen_rect.width or seg_max_y < 0 or seg_min_y > screen_rect.height:
                continue
            pygame.draw.line(self.screen, color, p1, p2, width)
            is_highlight = getattr(s, "selected", False) or (
                hover_channel is not None and getattr(s, "channel", None) == hover_channel
            )
            if is_highlight:
                pygame.draw.line(self.screen, theme.ACCENT, p1, p2, 8)
                pygame.draw.line(self.screen, (255, 255, 255), p1, p2, 2)
            ch = getattr(s, "channel", None)
            if ch is not None:
                label = font.render(str(ch), True, theme.TEXT)
                rect = label.get_rect(
                    center=((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
                )
                rect.y -= 10
                self.screen.blit(label, rect)

        # draw bending springs if provided
        if bending_springs:
            for bs in bending_springs:
                color = bs.get_color() if hasattr(bs, "get_color") else (200, 200, 0)
                self._draw_dashed_line(bs.p1.pos, bs.p2.pos, color, 3)
                self._draw_dashed_line(bs.p2.pos, bs.p3.pos, color, 3)
                a = self.world_to_screen(bs.p1.pos)
                b = self.world_to_screen(bs.p2.pos)
                c = self.world_to_screen(bs.p3.pos)
                v1 = a - b
                v2 = c - b
                l1, l2 = v1.length(), v2.length()
                if l1 and l2:
                    radius = min(l1, l2) * 0.4
                    rect = pygame.Rect(0, 0, radius * 2, radius * 2)
                    rect.center = (int(b.x), int(b.y))
                    start = math.atan2(-v1.y, v1.x)
                    angle = math.atan2(-v1.cross(v2), v1.dot(v2))
                    end = start + angle
                    if angle < 0:
                        start, end = end, start
                    start = (start + math.tau) % math.tau
                    end = (end + math.tau) % math.tau
                    pygame.draw.arc(self.screen, color, rect, start, end, 3)
                    is_highlight = getattr(bs, "selected", False) or (
                        hover_channel is not None and getattr(bs, "channel", None) == hover_channel
                    )
                    if is_highlight:
                        pygame.draw.line(self.screen, theme.ACCENT, a, b, 6)
                        pygame.draw.line(self.screen, theme.ACCENT, b, c, 6)
                        pygame.draw.line(self.screen, (255, 255, 255), a, b, 2)
                        pygame.draw.line(self.screen, (255, 255, 255), b, c, 2)
                        pygame.draw.arc(self.screen, theme.ACCENT, rect, start, end, 4)
                    ch = getattr(bs, "channel", None)
                    if ch is not None:
                        label = font.render(str(ch), True, theme.TEXT)
                        text_rect = label.get_rect(center=(int(b.x), int(b.y)))
                        text_rect.y -= int(radius) + 10
                        self.screen.blit(label, text_rect)

        if sensors:
            for s in sensors:
                center = self.world_to_screen(s.pos)
                radius = max(1, int(s.sense_radius * self.zoom))
                col = theme.ACCENT if hover_channel is not None and getattr(s, "channel", None) == hover_channel else (180, 180, 80)
                pygame.draw.circle(self.screen, col, (int(center.x), int(center.y)), radius, 1)
                if s.half_angle < math.pi:
                    start = math.atan2(-s.forward.y, s.forward.x) - s.half_angle
                    end = start + 2 * s.half_angle
                    rect = pygame.Rect(0, 0, radius * 2, radius * 2)
                    rect.center = (int(center.x), int(center.y))
                    pygame.draw.arc(self.screen, col, rect, start, end, 1)
                    p1 = center + pygame.Vector2(math.cos(start), math.sin(start)) * radius
                    p2 = center + pygame.Vector2(math.cos(end), math.sin(end)) * radius
                    pygame.draw.line(self.screen, col, center, p1, 1)
                    pygame.draw.line(self.screen, col, center, p2, 1)
                ch = getattr(s, "channel", None)
                if ch is not None:
                    label = font.render(str(ch), True, theme.TEXT)
                    rect = label.get_rect(center=(int(center.x), int(center.y)))
                    rect.y -= radius + 10
                    self.screen.blit(label, rect)

        # draw particles with culling and simplified effects at high zoom
        for p in particles:
            color = p.color if p.color else (0, 114, 255)
            base_radius = p.radius if p.radius else 10
            radius = max(1, int(base_radius * self.zoom))
            center = self.world_to_screen(p.pos)
            cx, cy = int(center.x), int(center.y)
            if cx + radius < 0 or cx - radius > screen_rect.width or cy + radius < 0 or cy - radius > screen_rect.height:
                continue
            use_aa = radius <= 20
            if use_aa:
                try:
                    gfxdraw.filled_circle(self.screen, cx, cy, radius, color)
                    gfxdraw.aacircle(self.screen, cx, cy, radius, (255, 255, 255))
                except Exception:
                    pygame.draw.circle(self.screen, color, (cx, cy), radius)
            else:
                pygame.draw.circle(self.screen, color, (cx, cy), radius)
            if radius <= 18:
                hi_r = max(1, int(radius * 0.6))
                hi_surf = pygame.Surface((hi_r * 2 + 4, hi_r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(hi_surf, (255, 255, 255, 40), (hi_r + 2, hi_r + 2), hi_r)
                self.screen.blit(hi_surf, (cx - hi_r - 2, cy - hi_r - int(radius * 0.4)))
            is_channel = hover_channel is not None and getattr(p, "channel", None) == hover_channel
            is_selected_or_hover = getattr(p, "selected", False) or (hover_particle is p) or is_channel
            is_high_drag = getattr(p, "drag", 1.0) > 1.0
            if is_selected_or_hover:
                ring_r = radius + 6
                if ring_r <= 28:
                    try:
                        gfxdraw.aacircle(self.screen, cx, cy, ring_r, theme.ACCENT)
                        gfxdraw.aacircle(self.screen, cx, cy, ring_r + 1, theme.ACCENT)
                    except Exception:
                        pygame.draw.circle(self.screen, theme.ACCENT, (cx, cy), ring_r + 1, width=2)
                else:
                    pygame.draw.circle(self.screen, theme.ACCENT, (cx, cy), ring_r + 1, width=2)
            if is_high_drag and not is_selected_or_hover:
                ring_color = (255, 60, 60)
                ring_r = radius + 6
                if ring_r <= 28:
                    try:
                        gfxdraw.aacircle(self.screen, cx, cy, ring_r - 1, ring_color)
                        gfxdraw.aacircle(self.screen, cx, cy, ring_r, ring_color)
                    except Exception:
                        pygame.draw.circle(self.screen, ring_color, (cx, cy), ring_r, width=2)
                else:
                    pygame.draw.circle(self.screen, ring_color, (cx, cy), ring_r, width=2)
            ch = getattr(p, "channel", None)
            if ch is not None:
                label = font.render(str(ch), True, theme.TEXT)
                rect = label.get_rect(center=(cx, cy))
                rect.y -= radius + 10
                self.screen.blit(label, rect)

        # overlay hover highlights for springs/bends
        if hover_spring is not None:
            p1 = self.world_to_screen(hover_spring.p1.pos)
            p2 = self.world_to_screen(hover_spring.p2.pos)
            # glow underlay then crisp accent
            pygame.draw.line(self.screen, theme.ACCENT, p1, p2, 8)
            pygame.draw.line(self.screen, (255, 255, 255), p1, p2, 2)
        if hover_bend is not None:
            p1 = self.world_to_screen(hover_bend.p1.pos)
            p2 = self.world_to_screen(hover_bend.p2.pos)
            p3 = self.world_to_screen(hover_bend.p3.pos)
            pygame.draw.line(self.screen, theme.ACCENT, p1, p2, 8)
            pygame.draw.line(self.screen, (255, 255, 255), p1, p2, 2)
            pygame.draw.line(self.screen, theme.ACCENT, p2, p3, 8)
            pygame.draw.line(self.screen, (255, 255, 255), p2, p3, 2)
            v1 = p1 - p2
            v2 = p3 - p2
            l1, l2 = v1.length(), v2.length()
            if l1 and l2:
                radius = min(l1, l2) * 0.4
                rect = pygame.Rect(0, 0, radius * 2, radius * 2)
                rect.center = (int(p2.x), int(p2.y))
                start = math.atan2(-v1.y, v1.x)
                angle = math.atan2(-v1.cross(v2), v1.dot(v2))
                end = start + angle
                if angle < 0:
                    start, end = end, start
                start = (start + math.tau) % math.tau
                end = (end + math.tau) % math.tau
                pygame.draw.arc(self.screen, theme.ACCENT, rect, start, end, 4)
