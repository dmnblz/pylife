"""Tool handling stiffness for new springs."""

import pygame

from ..fields import SliderField


class SpringTool:
    """Handle spring stiffness options when creating new springs."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.stiff_field = SliderField(
            "Stiff", 10, 1000, lambda: self.app.stiffness, self.app.set_stiffness, x, y, width
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
        self.stiff_field.draw(self.sidebar.screen)

    def draw_preview(self):
        pass

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False
        if self.sidebar.visible:
            if self.stiff_field.handle_event(event):
                return True
        return False
