"""Tool handling stiffness for new springs."""

import pygame

from ..fields import SliderField
from .base import Tool


class SpringTool(Tool):
    """Handle spring stiffness options when creating new springs."""

    def __init__(self, sidebar: 'SidebarUI'):
        super().__init__(sidebar)

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.stiff_field = SliderField(
            "Stiff", 10, 1000, lambda: self.app.stiffness, self.app.set_stiffness, x, y, width
        )

    # ---------------- drawing
    def draw_ui(self):
        if not super().draw_ui():
            return
        self.stiff_field.draw(self.sidebar.screen)

    # ---------------- event handling
    def handle_event(self, event):
        if not super().handle_event(event):
            return False
        if self.sidebar.visible:
            if self.stiff_field.handle_event(event):
                return True
        return False
