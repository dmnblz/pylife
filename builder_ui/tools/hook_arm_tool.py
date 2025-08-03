"""Tool for previewing and creating HookArm instances."""

import pygame

from ..fields import SliderField, ColorField, KeyField
from .base import Tool


class HookArmTool(Tool):
    """Preview and creation helper for :class:`HookArm` instances.

    The tool lets the user configure segment count, spacing, particle
    mass/radius, spring stiffness, cycle speed, colours, adhesion factor and
    the key used for cycling the arm.
    """

    def __init__(self, sidebar: 'SidebarUI'):
        """Setup controls for building hook arms."""

        super().__init__(sidebar)
        self.base = None
        self.direction = pygame.Vector2(1, 0)
        self.segments = 3
        self.spacing = 20.0
        self.mass = 0.5
        self.radius = 8.0
        self.stiffness = 500.0
        self.cycle_speed = 240.0
        self.color = (0, 150, 255)
        self.high_drag_color = (255, 50, 50)
        self.adhesion_factor = 10.0
        self.cycle_key = pygame.K_h
        self.dragging = False

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.seg_field = SliderField(
            "Segments", 1, 10, lambda: self.segments, self._set_segments, x, y, width
        )
        y += 40
        self.space_field = SliderField(
            "Spacing", 5, 60, lambda: self.spacing, self._set_spacing, x, y, width
        )
        y += 40
        self.mass_field = SliderField(
            "Mass", 0.1, 10.0, lambda: self.mass, self._set_mass, x, y, width
        )
        y += 40
        self.radius_field = SliderField(
            "Radius", 1, 50, lambda: self.radius, self._set_radius, x, y, width
        )
        y += 40
        self.stiff_field = SliderField(
            "Stiff", 10, 1000, lambda: self.stiffness, self._set_stiffness, x, y, width
        )
        y += 40
        self.speed_field = SliderField(
            "Speed", 50, 1000, lambda: self.cycle_speed, self._set_speed, x, y, width
        )
        y += 40
        self.color_field = ColorField("Color", lambda: self.color, self._set_color, x, y, width)
        y += 40
        self.high_field = ColorField(
            "HDrag", lambda: self.high_drag_color, self._set_high_color, x, y, width
        )
        y += 40
        self.adh_field = SliderField(
            "AdhesMF", 1, 20, lambda: self.adhesion_factor, self._set_adhesion, x, y, width
        )
        y += 40
        self.key_field = KeyField("Cycle", lambda: self.cycle_key, self._set_key, x, y, width)
        y += 40
        self.create_rect = pygame.Rect(x, y, width, self.sidebar.BUTTON_HEIGHT)

    # ---------------- value setters
    def _set_segments(self, value: float):
        """Set number of arm segments."""
        self.segments = max(1, int(value))

    def _set_spacing(self, value: float):
        """Set spacing between arm particles."""
        self.spacing = max(1, value)

    def _set_mass(self, value: float):
        """Set particle mass for the arm."""
        self.mass = max(0.1, value)

    def _set_radius(self, value: float):
        """Set particle radius for the arm."""
        self.radius = max(1, value)

    def _set_stiffness(self, value: float):
        """Set spring stiffness along the arm."""
        self.stiffness = max(10, value)

    def _set_speed(self, value: float):
        """Set cycle speed for automatic motion."""
        self.cycle_speed = max(10, value)

    def _set_color(self, color):
        """Set default arm colour."""
        self.color = color

    def _set_high_color(self, color):
        """Set colour used when high drag is active."""
        self.high_drag_color = color

    def _set_adhesion(self, value: float):
        """Set mass multiplier applied during adhesion."""
        self.adhesion_factor = max(1, value)

    def _set_key(self, value: int | None):
        """Set keyboard key used to cycle the arm."""
        self.cycle_key = value

    # ---------------- control
    def start(self):
        """Activate the tool and clear base particle."""
        super().start()
        self.base = None

    def cancel(self):
        """Deactivate the tool and stop dragging preview."""
        super().cancel()
        self.dragging = False

    # ---------------- drawing helpers
    def _preview_points(self):
        """Compute points for the arm preview."""
        if not self.base:
            return []
        if self.direction.length() == 0:
            return []
        dir_norm = self.direction.normalize()
        pts = []
        for i in range(1, self.segments + 1):
            pos = self.base.pos + dir_norm * self.spacing * i
            pts.append(self.app.snap_to_grid(pos))
        return pts

    def draw_ui(self):
        """Render hook arm configuration controls."""
        if not super().draw_ui():
            return
        self.seg_field.draw(self.sidebar.screen)
        self.space_field.draw(self.sidebar.screen)
        self.mass_field.draw(self.sidebar.screen)
        self.radius_field.draw(self.sidebar.screen)
        self.stiff_field.draw(self.sidebar.screen)
        self.speed_field.draw(self.sidebar.screen)
        self.color_field.draw(self.sidebar.screen)
        self.high_field.draw(self.sidebar.screen)
        self.adh_field.draw(self.sidebar.screen)
        self.key_field.draw(self.sidebar.screen)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.create_rect)
        txt = self.sidebar.font.render("Create", True, (255, 255, 255))
        rect = txt.get_rect(center=self.create_rect.center)
        self.sidebar.screen.blit(txt, rect)

    def draw_preview(self):
        """Draw a preview of the prospective arm."""
        if not super().draw_preview() or not self.base:
            return
        screen = self.sidebar.screen
        color = (150, 150, 150)
        last = self.base.pos
        for p in self._preview_points():
            pygame.draw.line(screen, color, last, p, 1)
            pygame.draw.circle(screen, color, (int(p.x), int(p.y)), int(self.radius), 1)
            last = p

    # ---------------- event handling
    def handle_event(self, event):
        """Manage UI interaction and base selection."""
        if not super().handle_event(event):
            return False

        if self.sidebar.visible:
            if self.seg_field.handle_event(event):
                return True
            if self.space_field.handle_event(event):
                return True
            if self.mass_field.handle_event(event):
                return True
            if self.radius_field.handle_event(event):
                return True
            if self.stiff_field.handle_event(event):
                return True
            if self.speed_field.handle_event(event):
                return True
            if self.color_field.handle_event(event):
                return True
            if self.high_field.handle_event(event):
                return True
            if self.adh_field.handle_event(event):
                return True
            if self.key_field.handle_event(event):
                return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.create_rect.collidepoint(event.pos) and self.base:
                    self.app.create_hook_arm(
                        self.base,
                        self.direction,
                        self.segments,
                        self.spacing,
                        self.mass,
                        self.radius,
                        self.stiffness,
                        self.color,
                        self.high_drag_color,
                        self.adhesion_factor,
                        self.cycle_key,
                        self.cycle_speed,
                    )
                    self.cancel()
                    self.sidebar.app.set_mode("drag")
                    return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                mouse = pygame.Vector2(event.pos)
                if not self.base:
                    if self.app.particles:
                        self.base = min(self.app.particles, key=lambda p: (p.pos - mouse).length())
                        self.dragging = True
                        self.direction = pygame.Vector2(1, 0)
                        return True
                else:
                    self.dragging = True
                    return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse = self.app.snap_to_grid(pygame.Vector2(event.pos))
            self.direction = mouse - self.base.pos
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return True

        return False
