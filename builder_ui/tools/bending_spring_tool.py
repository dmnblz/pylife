"""Tool for creating bending springs by selecting three particles."""

import math
import pygame

from bending_spring import BendingSpring
from ..fields import SliderField
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
        self.auto_rect = pygame.Rect(x, y, width, self.sidebar.BUTTON_HEIGHT)
        y += self.sidebar.BUTTON_HEIGHT + 12
        self.create_rect = pygame.Rect(x, y, width, self.sidebar.BUTTON_HEIGHT)

    def _set_angle(self, val: float):
        """Set the manual bend angle in degrees."""
        self.angle = max(0, val)

    def _set_stiff(self, val: float):
        """Set stiffness for the new bending spring."""
        self.stiffness = max(10, val)

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
    def draw_ui(self):
        """Render bending spring configuration controls."""
        if not super().draw_ui():
            return
        if not self.auto_angle:
            self.angle_field.draw(self.sidebar.screen)
        self.stiff_field.draw(self.sidebar.screen)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.auto_rect)
        label = "Auto" if not self.auto_angle else "Manual"
        txt = self.sidebar.font.render(label, True, (255, 255, 255))
        rect = txt.get_rect(center=self.auto_rect.center)
        self.sidebar.screen.blit(txt, rect)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.create_rect)
        txt = self.sidebar.font.render("Create", True, (255, 255, 255))
        rect = txt.get_rect(center=self.create_rect.center)
        self.sidebar.screen.blit(txt, rect)

    def draw_preview(self):
        """Highlight selected particles and preview links."""
        if not super().draw_preview():
            return
        screen = self.sidebar.screen
        color = (150, 150, 150)
        for p in self.selected:
            pygame.draw.circle(screen, color, (int(p.pos.x), int(p.pos.y)), int(p.radius) + 4, 1)
        if len(self.selected) >= 2:
            pygame.draw.line(screen, color, self.selected[0].pos, self.selected[1].pos, 1)
        if len(self.selected) == 3:
            pygame.draw.line(screen, color, self.selected[1].pos, self.selected[2].pos, 1)

    # ---------------- event handling
    def handle_event(self, event):
        """Handle field input and particle selection."""
        if not super().handle_event(event):
            return False
        if not self.auto_angle:
            if self.angle_field.handle_event(event):
                return True
        if self.stiff_field.handle_event(event):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.auto_rect.collidepoint(event.pos):
                self.auto_angle = not self.auto_angle
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.create_rect.collidepoint(event.pos) and len(self.selected) == 3:
                from math import radians
                if self.auto_angle:
                    v1 = self.selected[0].pos - self.selected[1].pos
                    v2 = self.selected[2].pos - self.selected[1].pos
                    if v1.length() == 0 or v2.length() == 0:
                        angle = 0
                    else:
                        dot = max(-1.0, min(1.0, v1.dot(v2) / (v1.length()*v2.length())))
                        angle = math.acos(dot)
                else:
                    angle = radians(self.angle)
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
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                if self.app.particles:
                    mouse = pygame.Vector2(event.pos)
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
