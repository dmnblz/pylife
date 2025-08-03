"""Tool configuring new :class:`variable_spring.VariableSpring` instances."""

import pygame

from ..fields import SliderField, KeyField
from .base import Tool


class VariableSpringTool(Tool):
    """Expose parameters for variable springs in the sidebar."""

    def __init__(self, sidebar: 'SidebarUI'):
        """Create sliders and fields for variable spring properties."""
        super().__init__(sidebar)
        self.mode = "hold"
        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.stiff_field = SliderField(
            "Stiff",
            10,
            1000,
            lambda: self.app.vspring.stiffness,
            lambda v: setattr(self.app.vspring, "stiffness", max(10, v)),
            x,
            y,
            width,
        )
        y += 40
        self.alt_field = SliderField(
            "Factor",
            0.2,
            5.0,
            lambda: self.app.vspring.alt_factor,
            lambda v: setattr(self.app.vspring, "alt_factor", max(0.01, v)),
            x,
            y,
            width,
        )
        y += 40
        self.speed_field = SliderField(
            "Speed",
            50,
            1000,
            lambda: self.app.vspring.speed,
            lambda v: setattr(self.app.vspring, "speed", max(10, v)),
            x,
            y,
            width,
        )
        y += 40
        self.key_field = KeyField(
            "Key",
            lambda: self.app.vspring.key,
            lambda k: setattr(self.app.vspring, "key", k),
            x,
            y,
            width,
        )
        y += 40
        self.mode_rect = pygame.Rect(x, y, width, self.sidebar.BUTTON_HEIGHT)

    def draw_ui(self):
        """Render the slider and key fields."""
        if not super().draw_ui():
            return
        self.stiff_field.draw(self.sidebar.screen)
        self.alt_field.draw(self.sidebar.screen)
        self.speed_field.draw(self.sidebar.screen)
        self.key_field.draw(self.sidebar.screen)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.mode_rect)
        txt = self.sidebar.font.render(f"Mode: {self.app.vspring.mode}", True, (255, 255, 255))
        rect = txt.get_rect(center=self.mode_rect.center)
        self.sidebar.screen.blit(txt, rect)

    def handle_event(self, event):
        """Forward events to sliders and handle mode toggling."""
        if not super().handle_event(event):
            return False
        if self.stiff_field.handle_event(event):
            return True
        if self.alt_field.handle_event(event):
            return True
        if self.speed_field.handle_event(event):
            return True
        if self.key_field.handle_event(event):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.mode_rect.collidepoint(event.pos):
                self.app.vspring.mode = "toggle" if self.app.vspring.mode == "hold" else "hold"
                return True
        return False
