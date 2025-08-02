"""Tool for enabling a snapping grid and adjusting its spacing."""

import pygame

from ..fields import SliderField


class GridTool:
    """Toggle a grid overlay and adjust its spacing."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.toggle_rect = pygame.Rect(x, y, width, self.sidebar.BUTTON_HEIGHT)
        y += self.sidebar.BUTTON_HEIGHT + 12
        self.size_field = SliderField(
            "Spacing", 5, 200, lambda: self.app.grid_size, self.app.set_grid_size, x, y, width
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
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.toggle_rect)
        state = "On" if self.app.grid_enabled else "Off"
        txt = self.sidebar.font.render(f"Grid: {state}", True, (255, 255, 255))
        rect = txt.get_rect(center=self.toggle_rect.center)
        self.sidebar.screen.blit(txt, rect)
        self.size_field.draw(self.sidebar.screen)

    def draw_preview(self):
        pass

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False
        if self.sidebar.visible:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.toggle_rect.collidepoint(event.pos):
                    self.app.toggle_grid()
                    return True
            if self.size_field.handle_event(event):
                return True
        return False
