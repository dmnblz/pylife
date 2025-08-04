"""Tool configuring new :class:`variable_particle.VariableParticle` instances."""

from ..fields import SliderField, ColorField, KeyField, ButtonField
from .base import Tool


class VariableParticleTool(Tool):
    """Expose parameters for variable particles in the sidebar."""

    def __init__(self, sidebar: 'SidebarUI'):
        """Create sliders and fields for variable particle properties."""
        super().__init__(sidebar)
        self.mode = "hold"
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
        self.drag_field = SliderField(
            "Drag",
            1,
            500,
            lambda: self.app.vparticle.alt_drag,
            lambda v: setattr(self.app.vparticle, "alt_drag", max(1, v)),
            x,
            y,
            width,
        )
        y += 40
        self.speed_field = SliderField(
            "Speed",
            50,
            1000,
            lambda: self.app.vparticle.speed,
            lambda v: setattr(self.app.vparticle, "speed", max(10, v)),
            x,
            y,
            width,
        )
        y += 40
        self.key_field = KeyField(
            "Key",
            lambda: self.app.vparticle.key,
            lambda k: setattr(self.app.vparticle, "key", k),
            x,
            y,
            width,
        )
        y += 40
        self.mode_button = ButtonField(
            lambda: f"Mode: {self.app.vparticle.mode}",
            self._toggle_mode,
            x,
            y,
            width,
            active=lambda: self.app.vparticle.mode == "toggle",
        )

    def _toggle_mode(self) -> None:
        """Switch the default variable particle between hold and toggle."""
        self.app.vparticle.mode = (
            "toggle" if self.app.vparticle.mode == "hold" else "hold"
        )

    # -------- value helpers for Particle params reused
    def _get_color(self):
        return self.app.particle.color

    def _set_color(self, color):
        self.app.particle.color = color

    def _get_mass(self):
        return self.app.particle.mass

    def _set_mass(self, value):
        self.app.particle.mass = max(0.1, value)

    def _get_radius(self):
        return self.app.particle.radius

    def _set_radius(self, value):
        self.app.particle.radius = max(1, int(value))

    # -------- drawing
    def draw_ui(self, offset: int = 0):
        if not super().draw_ui(offset):
            return
        self.color_field.draw(self.sidebar.screen, offset)
        self.mass_field.draw(self.sidebar.screen, offset)
        self.radius_field.draw(self.sidebar.screen, offset)
        self.drag_field.draw(self.sidebar.screen, offset)
        self.speed_field.draw(self.sidebar.screen, offset)
        self.key_field.draw(self.sidebar.screen, offset)
        self.mode_button.draw(self.sidebar.screen, offset)

    # -------- events
    def handle_event(self, event, offset: int = 0):
        if not super().handle_event(event, offset):
            return False
        if self.color_field.handle_event(event, offset):
            return True
        if self.mass_field.handle_event(event, offset):
            return True
        if self.radius_field.handle_event(event, offset):
            return True
        if self.drag_field.handle_event(event, offset):
            return True
        if self.speed_field.handle_event(event, offset):
            return True
        if self.key_field.handle_event(event, offset):
            return True
        if self.mode_button.handle_event(event, offset):
            return True
        return False
