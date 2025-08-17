"""Tool handling options for creating new particles."""

import pygame
from particle import Particle

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
        y += 40
        self.elasticity_field = SliderField(
            "Elastic",
            0,
            1,
            self._get_elasticity,
            self._set_elasticity,
            x,
            y,
            width,
        )

    # ---------------- drawing
    def draw_ui(self, offset: int = 0):
        """Render particle configuration sliders."""
        if not super().draw_ui(offset):
            return
        self.color_field.draw(self.sidebar.screen, offset)
        self.mass_field.draw(self.sidebar.screen, offset)
        self.radius_field.draw(self.sidebar.screen, offset)
        self.elasticity_field.draw(self.sidebar.screen, offset)

    # ---------------- event handling
    def handle_event(self, event, offset: int = 0):
        """Forward input events to particle option widgets."""
        if not super().handle_event(event, offset):
            return False
        if self.color_field.handle_event(event, offset):
            return True
        if self.mass_field.handle_event(event, offset):
            return True
        if self.radius_field.handle_event(event, offset):
            return True
        if self.elasticity_field.handle_event(event, offset):
            return True
        # left click on world area to place a particle at world position
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                world = self.sidebar.app.screen_to_world(event.pos)
                p = Particle(
                    world,
                    mass=self.sidebar.app.particle.mass,
                    color=self.sidebar.app.particle.color,
                    radius=self.sidebar.app.particle.radius,
                    elasticity=self.sidebar.app.particle.elasticity,
                    trail_length=self.sidebar.app.environment.trail_length,
                )
                self.sidebar.app.particles.append(p)
                self.sidebar.app.push_undo(lambda p=p: self.sidebar.app.remove_entities([p]))
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

    def _get_elasticity(self) -> float:
        """Return the default collision elasticity."""
        return self.app.particle.elasticity

    def _set_elasticity(self, value: float) -> None:
        """Set the default collision elasticity."""
        self.app.particle.elasticity = max(0.0, min(1.0, value))
