"""Tool for enabling a snapping grid and adjusting its spacing."""

import pygame

from ..fields import SliderField, ButtonField
from .base import Tool


class GridTool(Tool):
    """Toggle a grid overlay and adjust its spacing."""

    def __init__(self, sidebar: 'SidebarUI'):
        """Create widgets for toggling the grid and adjusting spacing."""

        super().__init__(sidebar)

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.toggle_button = ButtonField(
            lambda: f"Grid: {'On' if self.app.grid_enabled else 'Off'}",
            self.app.toggle_grid,
            x,
            y,
            width,
            active=lambda: self.app.grid_enabled,
        )
        y += self.sidebar.BUTTON_HEIGHT + 12
        self.size_field = SliderField(
            "Spacing", 5, 200, lambda: self.app.grid_size, self.app.set_grid_size, x, y, width
        )

    # ---------------- drawing
    def draw_ui(self, offset: int = 0):
        """Render the grid toggle and spacing slider."""
        if not super().draw_ui(offset):
            return
        self.toggle_button.draw(self.sidebar.screen, offset)
        self.size_field.draw(self.sidebar.screen, offset)

    # ---------------- event handling
    def handle_event(self, event, offset: int = 0):
        """Handle mouse input for grid toggling and spacing."""
        if not super().handle_event(event, offset):
            return False
        if self.toggle_button.handle_event(event, offset):
            return True
        if self.size_field.handle_event(event, offset):
            return True
        return False
