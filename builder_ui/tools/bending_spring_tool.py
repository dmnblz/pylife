"""Tool for creating bending springs by selecting three particles."""

import math
import pygame
from .. import theme

from bending_spring import BendingSpring
from ..fields import SliderField, ButtonField
from .base import Tool


class BendingSpringTool(Tool):
    """Create a bending spring by choosing three particles."""

    def __init__(self, sidebar: 'SidebarUI'):
        """Configure fields for creating bending springs."""

        super().__init__(sidebar)
        self.angle = 90.0
        self.stiffness = 200.0
        self.auto_angle = False
        self.selected: list = []

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.angle_field = SliderField(
            "Angle", 0, 180, lambda: self.angle, self._set_angle, x, y, width
        )
        y += 40
        self.stiff_field = SliderField(
            "Stiff", 10, 1000, lambda: self.stiffness, self._set_stiff, x, y, width
        )
        y += 40
        self.auto_button = ButtonField(
            lambda: "Manual" if self.auto_angle else "Auto",
            self._toggle_auto,
            x,
            y,
            width,
            active=lambda: self.auto_angle,
        )
        y += self.sidebar.BUTTON_HEIGHT + 12
        self.create_button = ButtonField("Create", self._create, x, y, width)

    def _set_angle(self, val: float):
        """Set the manual bend angle in degrees."""
        self.angle = max(0, val)

    def _set_stiff(self, val: float):
        """Set stiffness for the new bending spring."""
        self.stiffness = max(10, val)

    def _toggle_auto(self) -> None:
        """Switch between automatic and manual angle modes."""
        self.auto_angle = not self.auto_angle

    def _create(self) -> None:
        """Create the bending spring if three particles are selected."""
        if len(self.selected) != 3:
            return
        if self.auto_angle:
            v1 = self.selected[0].pos - self.selected[1].pos
            v2 = self.selected[2].pos - self.selected[1].pos
            if v1.length() == 0 or v2.length() == 0:
                angle = 0
            else:
                dot = max(-1.0, min(1.0, v1.dot(v2) / (v1.length() * v2.length())))
                angle = math.acos(dot)
        else:
            angle = math.radians(self.angle)
        bs = BendingSpring(
            self.selected[0],
            self.selected[1],
            self.selected[2],
            angle,
            self.stiffness,
        )
        self.app.bending_springs.append(bs)
        self.app.push_undo(lambda bs=bs: self.app._remove_bending(bs))
        self.cancel()
        self.sidebar.app.set_mode("drag")

    # ---------------- control
    def start(self):
        """Activate the tool and clear previous selections."""
        super().start()
        self.auto_angle = False
        self.selected.clear()

    def cancel(self):
        """Deactivate the tool and forget current selections."""
        super().cancel()
        self.selected.clear()

    # ---------------- drawing
    def draw_ui(self, offset: int = 0):
        """Render bending spring configuration controls."""
        if not super().draw_ui(offset):
            return
        if not self.auto_angle:
            self.angle_field.draw(self.sidebar.screen, offset)
        self.stiff_field.draw(self.sidebar.screen, offset)
        self.auto_button.draw(self.sidebar.screen, offset)
        self.create_button.draw(self.sidebar.screen, offset)

    def draw_preview(self):
        """Highlight selected particles and preview links with accent styling."""
        if not super().draw_preview():
            return
        screen = self.sidebar.screen
        # draw selected particles with accent glow + AA rings
        for p in self.selected:
            c = self.app.world_to_screen(p.pos)
            cx, cy = int(c.x), int(c.y)
            base_r = (p.radius or 10)
            rr = max(1, int(base_r * self.app.camera_zoom))
            # halo
            glow_r = rr + 10
            glow_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*theme.ACCENT, 70), (glow_r + 2, glow_r + 2), glow_r)
            screen.blit(glow_surf, (cx - glow_r - 2, cy - glow_r - 2))
            # rings
            try:
                import pygame.gfxdraw as gfx
                gfx.aacircle(screen, cx, cy, rr + 6, theme.ACCENT)
                gfx.aacircle(screen, cx, cy, rr + 7, theme.ACCENT)
            except Exception:
                pygame.draw.circle(screen, theme.ACCENT, (cx, cy), rr + 7, 2)

        # accent lines between selected points (match renderer hover style)
        if len(self.selected) >= 2:
            p1 = self.app.world_to_screen(self.selected[0].pos)
            p2 = self.app.world_to_screen(self.selected[1].pos)
            pygame.draw.line(screen, theme.ACCENT, p1, p2, 8)
            pygame.draw.line(screen, (255, 255, 255), p1, p2, 2)
        if len(self.selected) == 3:
            p2 = self.app.world_to_screen(self.selected[1].pos)
            p3 = self.app.world_to_screen(self.selected[2].pos)
            pygame.draw.line(screen, theme.ACCENT, p2, p3, 8)
            pygame.draw.line(screen, (255, 255, 255), p2, p3, 2)
            p1 = self.app.world_to_screen(self.selected[0].pos)
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
                pygame.draw.arc(screen, theme.ACCENT, rect, start, end, 3)

    # ---------------- event handling
    def handle_event(self, event, offset: int = 0):
        """Handle field input and particle selection."""
        if not super().handle_event(event, offset):
            return False
        if not self.auto_angle:
            if self.angle_field.handle_event(event, offset):
                return True
        if self.stiff_field.handle_event(event, offset):
            return True
        if self.auto_button.handle_event(event, offset):
            return True
        if self.create_button.handle_event(event, offset):
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                if self.app.particles:
                    mouse = self.app.screen_to_world(event.pos)
                    particle = min(self.app.particles, key=lambda p: (p.pos - mouse).length())
                    if particle not in self.selected:
                        if len(self.selected) < 3:
                            self.selected.append(particle)
                        else:
                            self.selected.pop(0)
                            self.selected.append(particle)
                    return True

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.selected.clear()
            return True

        return False
