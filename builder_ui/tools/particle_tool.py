"""Tool handling options for creating new particles."""

import pygame

from ..fields import SliderField, ColorField
from .base import Tool


class ParticleTool(Tool):
    """Handle options for creating new particles."""

    def __init__(self, sidebar: 'SidebarUI'):
        super().__init__(sidebar)

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.color_field = ColorField(
            "Color", lambda: self.app.color, self.app.set_color, x, y, width
        )
        y += 40
        self.mass_field = SliderField(
            "Mass", 0.1, 10.0, lambda: self.app.mass, self.app.set_mass, x, y, width
        )
        y += 40
        self.radius_field = SliderField(
            "Radius", 1, 50, lambda: self.app.radius, self.app.set_radius, x, y, width
        )

    # ---------------- drawing
    def draw_ui(self):
        if not super().draw_ui():
            return
        self.color_field.draw(self.sidebar.screen)
        self.mass_field.draw(self.sidebar.screen)
        self.radius_field.draw(self.sidebar.screen)

    # ---------------- event handling
    def handle_event(self, event):
        if not super().handle_event(event):
            return False
        if self.sidebar.visible:
            if self.color_field.handle_event(event):
                return True
            if self.mass_field.handle_event(event):
                return True
            if self.radius_field.handle_event(event):
                return True
        return False
