"""Tool for inspecting and editing existing particles, springs and bends."""

import math
import pygame

from ..fields import SliderField, ColorField
from .base import Tool


class InspectTool(Tool):
    """Select a particle or spring and edit its properties from the sidebar."""

    def __init__(self, sidebar: 'SidebarUI'):
        super().__init__(sidebar)
        self.particle = None
        self.spring = None
        self.bend = None

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.color_field = ColorField(
            "P Color", lambda: self._get_color(), self._set_color, x, y, width
        )
        y += 40
        self.mass_field = SliderField(
            "P Mass", 0.1, 10.0, lambda: self._get_mass(), self._set_mass, x, y, width
        )
        y += 40
        self.radius_field = SliderField(
            "P Radius", 1, 50, lambda: self._get_radius(), self._set_radius, x, y, width
        )
        y += 40
        self.rest_field = SliderField(
            "S Rest", 1, 400, lambda: self._get_rest(), self._set_rest, x, y, width
        )
        y += 40
        self.stiff_field = SliderField(
            "S Stiff", 10, 1000, lambda: self._get_stiff(), self._set_stiff, x, y, width
        )
        y += 40
        self.max_field = SliderField(
            "S MaxF", 0, 2000, lambda: self._get_max(), self._set_max, x, y, width
        )
        y += 40
        self.bangle_field = SliderField(
            "B Ang", 0, 180, lambda: self._get_bangle(), self._set_bangle, x, y, width
        )
        y += 40
        self.bstiff_field = SliderField(
            "B Stiff", 10, 1000, lambda: self._get_bstiff(), self._set_bstiff, x, y, width
        )
        y += 40
        self.invis_rect = pygame.Rect(x, y, width, self.sidebar.BUTTON_HEIGHT)

    # ---------------- helpers
    def _get_color(self):
        return self.particle.color if self.particle else (255, 255, 255)

    def _set_color(self, color):
        if self.particle:
            self.particle.color = color

    def _get_mass(self):
        return self.particle.mass if self.particle else 0

    def _set_mass(self, value: float):
        if self.particle:
            self.particle.mass = max(0.1, value)

    def _get_radius(self):
        return self.particle.radius if self.particle else 0

    def _set_radius(self, value: float):
        if self.particle:
            self.particle.radius = max(1, int(value))

    def _get_rest(self):
        return self.spring.rest_length if self.spring else 0

    def _set_rest(self, value: float):
        if self.spring:
            self.spring.rest_length = max(1, value)

    def _get_stiff(self):
        return self.spring.stiffness if self.spring else 0

    def _set_stiff(self, value: float):
        if self.spring:
            self.spring.stiffness = max(10, value)

    def _get_bangle(self):
        return math.degrees(self.bend.rest_angle) if self.bend else 0

    def _set_bangle(self, value: float):
        if self.bend:
            self.bend.rest_angle = math.radians(max(0, value))

    def _get_bstiff(self):
        return self.bend.stiffness if self.bend else 0

    def _set_bstiff(self, value: float):
        if self.bend:
            self.bend.stiffness = max(10, value)

    def _get_max(self):
        if not self.spring:
            return 0
        return self.spring.max_force if self.spring.max_force is not None else 0

    def _set_max(self, value: float):
        if self.spring:
            self.spring.max_force = None if value == 0 else value

    def _toggle_invisible(self):
        if self.spring:
            self.spring.invisible = not self.spring.invisible

    # ---------------- control
    def start(self):
        super().start()
        self.particle = None
        self.spring = None
        self.bend = None

    def cancel(self):
        super().cancel()
        self.particle = None
        self.spring = None
        self.bend = None

    def draw_ui(self):
        if not super().draw_ui():
            return
        if self.particle:
            self.color_field.draw(self.sidebar.screen)
            self.mass_field.draw(self.sidebar.screen)
            self.radius_field.draw(self.sidebar.screen)
        elif self.spring:
            self.rest_field.draw(self.sidebar.screen)
            self.stiff_field.draw(self.sidebar.screen)
            self.max_field.draw(self.sidebar.screen)
            pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.invis_rect)
            txt = self.sidebar.font.render(
                "Hide" if not self.spring.invisible else "Show", True, (255, 255, 255)
            )
            rect = txt.get_rect(center=self.invis_rect.center)
            self.sidebar.screen.blit(txt, rect)
        elif self.bend:
            self.bangle_field.draw(self.sidebar.screen)
            self.bstiff_field.draw(self.sidebar.screen)

    def draw_preview(self):
        if not super().draw_preview():
            return
        if self.particle:
            pygame.draw.circle(
                self.sidebar.screen,
                (255, 255, 0),
                (int(self.particle.pos.x), int(self.particle.pos.y)),
                int(self.particle.radius) + 4,
                2,
            )
        elif self.spring:
            pygame.draw.line(
                self.sidebar.screen,
                (255, 255, 0),
                self.spring.p1.pos,
                self.spring.p2.pos,
                3,
            )
        elif self.bend:
            pygame.draw.line(
                self.sidebar.screen,
                (255, 255, 0),
                self.bend.p1.pos,
                self.bend.p2.pos,
                3,
            )
            pygame.draw.line(
                self.sidebar.screen,
                (255, 255, 0),
                self.bend.p2.pos,
                self.bend.p3.pos,
                3,
            )

    # ---------------- event handling
    def handle_event(self, event):
        if not super().handle_event(event):
            return False

        if self.sidebar.visible:
            if self.particle:
                if self.color_field.handle_event(event):
                    return True
                if self.mass_field.handle_event(event):
                    return True
                if self.radius_field.handle_event(event):
                    return True
            elif self.spring:
                if self.rest_field.handle_event(event):
                    return True
                if self.stiff_field.handle_event(event):
                    return True
                if self.max_field.handle_event(event):
                    return True
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.invis_rect.collidepoint(event.pos):
                    self._toggle_invisible()
                    return True
            elif self.bend:
                if self.bangle_field.handle_event(event):
                    return True
                if self.bstiff_field.handle_event(event):
                    return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                mouse = pygame.Vector2(event.pos)
                dist_p = float("inf")
                dist_s = float("inf")
                dist_b = float("inf")
                nearest_p = None
                nearest_s = None
                nearest_b = None
                if self.app.particles:
                    nearest_p = min(self.app.particles, key=lambda p: (p.pos - mouse).length())
                    dist_p = (nearest_p.pos - mouse).length()
                if self.app.springs:
                    def seg_dist(s):
                        a = s.p1.pos
                        b = s.p2.pos
                        d = b - a
                        if d.length_squared() == 0:
                            return (mouse - a).length()
                        t = max(0, min(1, (mouse - a).dot(d) / d.length_squared()))
                        proj = a + d * t
                        return (mouse - proj).length()
                    nearest_s = min(self.app.springs, key=seg_dist)
                    dist_s = seg_dist(nearest_s)
                if self.app.bending_springs:
                    def seg_dist_b(bs):
                        def seg(a, b):
                            d = b - a
                            if d.length_squared() == 0:
                                return (mouse - a).length()
                            t = max(0, min(1, (mouse - a).dot(d) / d.length_squared()))
                            proj = a + d * t
                            return (mouse - proj).length()
                        return min(seg(bs.p1.pos, bs.p2.pos), seg(bs.p2.pos, bs.p3.pos))
                    nearest_b = min(self.app.bending_springs, key=seg_dist_b)
                    dist_b = seg_dist_b(nearest_b)
                if dist_p <= dist_s and dist_p <= dist_b:
                    if nearest_p is not None:
                        self.particle = nearest_p
                        self.spring = None
                        self.bend = None
                        return True
                elif dist_s <= dist_b:
                    if nearest_s is not None:
                        self.spring = nearest_s
                        self.particle = None
                        self.bend = None
                        return True
                else:
                    if nearest_b is not None:
                        self.bend = nearest_b
                        self.particle = None
                        self.spring = None
                        return True

        return False
