"""Tool handling stiffness for new springs."""

import pygame

from ..fields import SliderField
from .base import Tool


class SpringTool(Tool):
    """Handle spring stiffness options when creating new springs."""

    def __init__(self, sidebar: 'SidebarUI'):
        """Create the stiffness slider for new springs."""

        super().__init__(sidebar)

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.stiff_field = SliderField(
            "Stiff",
            10,
            1000,
            lambda: self.app.spring.stiffness,
            lambda v: setattr(self.app.spring, "stiffness", max(10, v)),
            x,
            y,
            width,
        )

    # ---------------- drawing
    def draw_ui(self, offset: int = 0):
        """Render the spring stiffness slider."""
        if not super().draw_ui(offset):
            return
        self.stiff_field.draw(self.sidebar.screen, offset)

    # ---------------- event handling
    def handle_event(self, event, offset: int = 0):
        """Forward input events to the stiffness slider."""
        if not super().handle_event(event, offset):
            return False
        if self.stiff_field.handle_event(event, offset):
            return True
        return False
