"""Tool for previewing and creating circular particle arrangements."""

import math
import pygame

from ..fields import SliderField, ButtonField
from .base import Tool


class CircleTool(Tool):
    """Handle circle preview creation with sliders and dragging."""

    def __init__(self, sidebar: 'SidebarUI'):
        """Configure sliders and defaults for circle creation."""

        super().__init__(sidebar)
        self.center = None
        self.radius = 50.0
        self.segments = 8
        self.dragging = False
        self.stiffness = 200.0
        self.bend_stiffness = 200.0
        self.include_bend = False

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.radius_field = SliderField(
            "C Radius", 5, 400, lambda: self.radius, self._set_radius, x, y, width
        )
        y += 40
        self.segments_field = SliderField(
            "Segments", 3, 60, lambda: self.segments, self._set_segments, x, y, width
        )
        y += 40
        self.stiff_field = SliderField(
            "Stiff", 10, 1000, lambda: self.stiffness, self._set_stiff, x, y, width
        )
        y += 40
        self.bend_button = ButtonField(
            lambda: "Bend: On" if self.include_bend else "Bend: Off",
            self._toggle_bend,
            x,
            y,
            width,
            active=lambda: self.include_bend,
        )
        y += self.sidebar.BUTTON_HEIGHT + 4
        self.bstiff_field = SliderField(
            "BStiff", 10, 1000, lambda: self.bend_stiffness, self._set_bstiff, x, y, width
        )
        y += 40
        self.create_button = ButtonField("Create", self._create, x, y, width)

    # ---------------- value setters
    def _set_radius(self, value: float):
        """Update preview radius."""
        self.radius = max(1, value)

    def _set_segments(self, value: float):
        """Set number of circle segments."""
        self.segments = max(3, int(value))

    def _set_stiff(self, value: float):
        """Set spring stiffness for new circles."""
        self.stiffness = max(10, value)

    def _set_bstiff(self, value: float):
        """Set bending spring stiffness."""
        self.bend_stiffness = max(10, value)

    def _toggle_bend(self) -> None:
        """Toggle inclusion of bending springs in the new circle."""
        self.include_bend = not self.include_bend

    def _create(self) -> None:
        """Spawn the configured circle if a center was set."""
        if not self.center:
            return
        self.app.create_circle(
            self.center,
            self.radius,
            self.segments,
            self.stiffness,
            self.include_bend,
            self.bend_stiffness,
        )
        self.cancel()
        self.sidebar.app.set_mode("drag")

    # ---------------- control
    def start(self):
        """Begin circle placement and reset parameters."""
        super().start()
        self.center = None
        self.stiffness = self.app.spring.stiffness
        self.bend_stiffness = self.app.spring.stiffness
        self.include_bend = False

    def cancel(self):
        """Abort circle creation."""
        super().cancel()
        self.dragging = False

    def draw_ui(self, offset: int = 0):
        """Render circle creation controls."""
        if not super().draw_ui(offset):
            return
        self.radius_field.draw(self.sidebar.screen, offset)
        self.segments_field.draw(self.sidebar.screen, offset)
        self.stiff_field.draw(self.sidebar.screen, offset)
        self.bend_button.draw(self.sidebar.screen, offset)
        if self.include_bend:
            self.bstiff_field.draw(self.sidebar.screen, offset)
        self.create_button.draw(self.sidebar.screen, offset)

    def draw_preview(self):
        """Draw a circle preview at the current mouse position."""
        if not super().draw_preview() or self.center is None:
            return
        screen = self.sidebar.screen
        color = (150, 150, 150)
        center = self.app.snap_to_grid(self.center)
        pygame.draw.circle(screen, color, (int(center.x), int(center.y)), int(self.radius), 1)
        for i in range(self.segments):
            theta1 = (i / self.segments) * 2 * math.pi
            theta2 = ((i + 1) % self.segments) / self.segments * 2 * math.pi
            p1 = self.app.snap_to_grid(
                self.center + pygame.Vector2(math.cos(theta1), math.sin(theta1)) * self.radius
            )
            p2 = self.app.snap_to_grid(
                self.center + pygame.Vector2(math.cos(theta2), math.sin(theta2)) * self.radius
            )
            pygame.draw.line(screen, color, p1, p2, 1)
            pygame.draw.circle(
                screen,
                color,
                (int(p1.x), int(p1.y)),
                self.app.particle.radius,
                1,
            )

    # ---------------- event handling
    def handle_event(self, event, offset: int = 0):
        """Handle mouse input for circle placement and UI controls."""
        if not super().handle_event(event, offset):
            return False

        if self.radius_field.handle_event(event, offset):
            return True
        if self.segments_field.handle_event(event, offset):
            return True
        if self.stiff_field.handle_event(event, offset):
            return True
        if self.include_bend and self.bstiff_field.handle_event(event, offset):
            return True
        if self.bend_button.handle_event(event, offset):
            return True
        if self.create_button.handle_event(event, offset):
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # click in world area to set center
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                self.center = self.app.snap_to_grid(pygame.Vector2(event.pos))
                self.dragging = True
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse = self.app.snap_to_grid(pygame.Vector2(event.pos))
            self.radius = (mouse - self.center).length()
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return True

        return False
