"""Tool exposing global simulation options such as gravity and damping."""

import pygame
from collections import deque

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
        self.vel_damp_field = SliderField(
            "Vel Damp",
            0,
            1,
            lambda: self.app.environment.integration_damping,
            self._set_integration_damping,
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
        y += 40
        self.coll_field = SliderField(
            "Collide",
            0,
            1,
            lambda: 1 if self.app.environment.collisions else 0,
            self._set_collisions,
            x,
            y,
            width,
        )
        y += 40
        self.trail_toggle_field = SliderField(
            "Trail",
            0,
            1,
            lambda: 1 if self.app.environment.trails_enabled else 0,
            self._set_trails_enabled,
            x,
            y,
            width,
        )
        y += 40
        self.trail_len_field = SliderField(
            "TrailLen",
            1,
            200,
            lambda: self.app.environment.trail_length,
            self._set_trail_length,
            x,
            y,
            width,
        )
        y += 40
        self.play_w_field = SliderField(
            "Field W",
            200,
            6000,
            lambda: float(self.app.environment.play_width),
            self._set_play_width,
            x,
            y,
            width,
        )
        y += 40
        self.play_h_field = SliderField(
            "Field H",
            200,
            6000,
            lambda: float(self.app.environment.play_height),
            self._set_play_height,
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

    def _set_integration_damping(self, value: float):
        """Adjust velocity damping applied during integration."""
        val = max(0, min(1, value))
        self.app.environment.integration_damping = val
        self.app.physics.integration_damping = val

    def _set_temperature(self, value: float):
        """Set Brownian motion intensity."""
        val = max(0, value)
        self.app.environment.temperature = val
        self.app.physics.temperature = val

    def _set_collisions(self, value: float):
        """Enable or disable particle collisions."""
        enabled = value >= 0.5
        self.app.environment.collisions = enabled
        self.app.physics.collisions_enabled = enabled

    def _set_trails_enabled(self, value: float) -> None:
        """Toggle recording and rendering of particle trails."""
        enabled = value >= 0.5
        self.app.environment.trails_enabled = enabled
        self.app.physics.trails_enabled = enabled
        self.app.renderer.set_trails_enabled(enabled)
        if not enabled:
            for p in self.app.particles:
                p.trail.clear()

    def _set_trail_length(self, value: float) -> None:
        """Adjust the maximum stored points per particle trail."""
        length = max(1, int(value))
        self.app.environment.trail_length = length
        for p in self.app.particles:
            p.trail = deque(p.trail, maxlen=length)

    def _set_play_width(self, value: float) -> None:
        """Update play area width and notify physics/renderer."""
        w = int(max(50, min(6000, value)))
        self.app.environment.play_width = w
        # keep left at 0; adjust rect size only
        self.app.play_area.width = w
        self.app.physics.set_play_area(self.app.play_area)

    def _set_play_height(self, value: float) -> None:
        """Update play area height and notify physics/renderer."""
        h = int(max(50, min(6000, value)))
        self.app.environment.play_height = h
        self.app.play_area.height = h
        self.app.physics.set_play_area(self.app.play_area)

    # ---------------- drawing
    def draw_ui(self, offset: int = 0):
        """Render sliders for environment parameters."""
        if not super().draw_ui(offset):
            return
        self.gx_field.draw(self.sidebar.screen, offset)
        self.gy_field.draw(self.sidebar.screen, offset)
        self.rep_rad_field.draw(self.sidebar.screen, offset)
        self.rep_str_field.draw(self.sidebar.screen, offset)
        self.damp_field.draw(self.sidebar.screen, offset)
        self.vel_damp_field.draw(self.sidebar.screen, offset)
        self.temp_field.draw(self.sidebar.screen, offset)
        self.coll_field.draw(self.sidebar.screen, offset)
        self.trail_toggle_field.draw(self.sidebar.screen, offset)
        self.trail_len_field.draw(self.sidebar.screen, offset)
        self.play_w_field.draw(self.sidebar.screen, offset)
        self.play_h_field.draw(self.sidebar.screen, offset)

    # ---------------- event handling
    def handle_event(self, event, offset: int = 0):
        """Forward events to environment sliders."""
        if not super().handle_event(event, offset):
            return False
        if self.gx_field.handle_event(event, offset):
            return True
        if self.gy_field.handle_event(event, offset):
            return True
        if self.rep_rad_field.handle_event(event, offset):
            return True
        if self.rep_str_field.handle_event(event, offset):
            return True
        if self.damp_field.handle_event(event, offset):
            return True
        if self.vel_damp_field.handle_event(event, offset):
            return True
        if self.temp_field.handle_event(event, offset):
            return True
        if self.coll_field.handle_event(event, offset):
            return True
        if self.trail_toggle_field.handle_event(event, offset):
            return True
        if self.trail_len_field.handle_event(event, offset):
            return True
        if self.play_w_field.handle_event(event, offset):
            return True
        if self.play_h_field.handle_event(event, offset):
            return True
        return False
