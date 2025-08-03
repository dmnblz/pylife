"""Tool for enabling a snapping grid and adjusting its spacing."""

import pygame

from ..fields import SliderField
from .base import Tool


class GridTool(Tool):
    """Toggle a grid overlay and adjust its spacing."""

    def __init__(self, sidebar: 'SidebarUI'):
        """Create widgets for toggling the grid and adjusting spacing."""

        super().__init__(sidebar)

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.toggle_rect = pygame.Rect(x, y, width, self.sidebar.BUTTON_HEIGHT)
        y += self.sidebar.BUTTON_HEIGHT + 12
        self.size_field = SliderField(
            "Spacing", 5, 200, lambda: self.app.grid_size, self.app.set_grid_size, x, y, width
        )

    # ---------------- drawing
    def draw_ui(self):
        """Render the grid toggle and spacing slider."""
        if not super().draw_ui():
            return
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.toggle_rect)
        state = "On" if self.app.grid_enabled else "Off"
        txt = self.sidebar.font.render(f"Grid: {state}", True, (255, 255, 255))
        rect = txt.get_rect(center=self.toggle_rect.center)
        self.sidebar.screen.blit(txt, rect)
        self.size_field.draw(self.sidebar.screen)

    # ---------------- event handling
    def handle_event(self, event):
        """Handle mouse input for grid toggling and spacing."""
        if not super().handle_event(event):
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.toggle_rect.collidepoint(event.pos):
                self.app.toggle_grid()
                return True
        if self.size_field.handle_event(event):
            return True
        return False
