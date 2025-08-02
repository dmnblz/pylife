"""Tool handling options for creating new particles."""

import pygame

from ..fields import SliderField, ColorField


class ParticleTool:
    """Handle options for creating new particles."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False

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

    # ---------------- control
    def start(self):
        self.active = True

    def cancel(self):
        self.active = False

    # ---------------- drawing
    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        self.color_field.draw(self.sidebar.screen)
        self.mass_field.draw(self.sidebar.screen)
        self.radius_field.draw(self.sidebar.screen)

    def draw_preview(self):
        pass

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False
        if self.sidebar.visible:
            if self.color_field.handle_event(event):
                return True
            if self.mass_field.handle_event(event):
                return True
            if self.radius_field.handle_event(event):
                return True
        return False
