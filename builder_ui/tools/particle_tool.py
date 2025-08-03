"""Tool handling options for creating new particles."""

import pygame

from ..fields import SliderField, ColorField
from .base import Tool


class ParticleTool(Tool):
    """Handle options for creating new particles."""

    def __init__(self, sidebar: 'SidebarUI'):
        """Initialise sliders controlling new particle properties."""

        super().__init__(sidebar)

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.color_field = ColorField(
            "Color",
            self._get_color,
            self._set_color,
            x,
            y,
            width,
        )
        y += 40
        self.mass_field = SliderField(
            "Mass",
            0.1,
            10.0,
            self._get_mass,
            self._set_mass,
            x,
            y,
            width,
        )
        y += 40
        self.radius_field = SliderField(
            "Radius",
            1,
            50,
            self._get_radius,
            self._set_radius,
            x,
            y,
            width,
        )

    # ---------------- drawing
    def draw_ui(self):
        """Render particle configuration sliders."""
        if not super().draw_ui():
            return
        self.color_field.draw(self.sidebar.screen)
        self.mass_field.draw(self.sidebar.screen)
        self.radius_field.draw(self.sidebar.screen)

    # ---------------- event handling
    def handle_event(self, event):
        """Forward input events to particle option widgets."""
        if not super().handle_event(event):
            return False
        if self.color_field.handle_event(event):
            return True
        if self.mass_field.handle_event(event):
            return True
        if self.radius_field.handle_event(event):
            return True
        return False

    # ---------------- value helpers
    def _get_color(self) -> tuple[int, int, int]:
        """Return the default particle colour."""
        return self.app.particle.color

    def _set_color(self, color: tuple[int, int, int]) -> None:
        """Update the default particle colour."""
        self.app.particle.color = color

    def _get_mass(self) -> float:
        """Return the default particle mass."""
        return self.app.particle.mass

    def _set_mass(self, value: float) -> None:
        """Set the default particle mass."""
        self.app.particle.mass = max(0.1, value)

    def _get_radius(self) -> float:
        """Return the default particle radius."""
        return self.app.particle.radius

    def _set_radius(self, value: float) -> None:
        """Set the default particle radius."""
        self.app.particle.radius = max(1, int(value))
