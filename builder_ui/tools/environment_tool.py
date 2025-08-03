"""Tool exposing global simulation options such as gravity and damping."""

import pygame

from ..fields import SliderField
from .base import Tool


class EnvironmentTool(Tool):
    """Expose global simulation options such as gravity and temperature."""

    def __init__(self, sidebar: 'SidebarUI'):
        """Build sliders for global simulation parameters."""

        super().__init__(sidebar)

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.gx_field = SliderField(
            "Grav X",
            -2000,
            2000,
            lambda: self.app.environment.gravity.x,
            self._set_gravity_x,
            x,
            y,
            width,
        )
        y += 40
        self.gy_field = SliderField(
            "Grav Y",
            -2000,
            2000,
            lambda: self.app.environment.gravity.y,
            self._set_gravity_y,
            x,
            y,
            width,
        )
        y += 40
        self.rep_rad_field = SliderField(
            "Rep Rad",
            0,
            200,
            lambda: self.app.environment.repulsion_radius,
            self._set_repulsion_radius,
            x,
            y,
            width,
        )
        y += 40
        self.rep_str_field = SliderField(
            "Rep Str",
            0,
            10000,
            lambda: self.app.environment.repulsion_strength,
            self._set_repulsion_strength,
            x,
            y,
            width,
        )
        y += 40
        self.damp_field = SliderField(
            "Damp",
            0,
            5,
            lambda: self.app.environment.damping,
            self._set_damping,
            x,
            y,
            width,
        )
        y += 40
        self.temp_field = SliderField(
            "Temp",
            0,
            1000,
            lambda: self.app.environment.temperature,
            self._set_temperature,
            x,
            y,
            width,
        )

    # ---------------- value setters
    def _set_gravity_x(self, value: float):
        """Set horizontal gravity component."""
        self.app.environment.gravity.x = value
        self.app.physics.gravity.x = value

    def _set_gravity_y(self, value: float):
        """Set vertical gravity component."""
        self.app.environment.gravity.y = value
        self.app.physics.gravity.y = value

    def _set_repulsion_radius(self, value: float):
        """Update radius for particle repulsion."""
        val = max(0, value)
        self.app.environment.repulsion_radius = val
        self.app.physics.repulsion_radius = val

    def _set_repulsion_strength(self, value: float):
        """Update magnitude of particle repulsion."""
        val = max(0, value)
        self.app.environment.repulsion_strength = val
        self.app.physics.repulsion_strength = val

    def _set_damping(self, value: float):
        """Adjust global viscous damping."""
        val = max(0, value)
        self.app.environment.damping = val
        self.app.physics.damping_coeff = val

    def _set_temperature(self, value: float):
        """Set Brownian motion intensity."""
        val = max(0, value)
        self.app.environment.temperature = val
        self.app.physics.temperature = val

    # ---------------- drawing
    def draw_ui(self):
        """Render sliders for environment parameters."""
        if not super().draw_ui():
            return
        self.gx_field.draw(self.sidebar.screen)
        self.gy_field.draw(self.sidebar.screen)
        self.rep_rad_field.draw(self.sidebar.screen)
        self.rep_str_field.draw(self.sidebar.screen)
        self.damp_field.draw(self.sidebar.screen)
        self.temp_field.draw(self.sidebar.screen)

    # ---------------- event handling
    def handle_event(self, event):
        """Forward events to environment sliders."""
        if not super().handle_event(event):
            return False
        if self.gx_field.handle_event(event):
            return True
        if self.gy_field.handle_event(event):
            return True
        if self.rep_rad_field.handle_event(event):
            return True
        if self.rep_str_field.handle_event(event):
            return True
        if self.damp_field.handle_event(event):
            return True
        if self.temp_field.handle_event(event):
            return True
        return False
