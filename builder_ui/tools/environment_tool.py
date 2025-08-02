"""Tool exposing global simulation options such as gravity and damping."""

import pygame

from ..fields import SliderField


class EnvironmentTool:
    """Expose global simulation options such as gravity and temperature."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.gx_field = SliderField(
            "Grav X", -2000, 2000,
            lambda: self.app.physics.gravity.x,
            self.app.set_gravity_x,
            x, y, width,
        )
        y += 40
        self.gy_field = SliderField(
            "Grav Y", -2000, 2000,
            lambda: self.app.physics.gravity.y,
            self.app.set_gravity_y,
            x, y, width,
        )
        y += 40
        self.rep_rad_field = SliderField(
            "Rep Rad", 0, 200,
            lambda: self.app.physics.repulsion_radius,
            self.app.set_repulsion_radius,
            x, y, width,
        )
        y += 40
        self.rep_str_field = SliderField(
            "Rep Str", 0, 10000,
            lambda: self.app.physics.repulsion_strength,
            self.app.set_repulsion_strength,
            x, y, width,
        )
        y += 40
        self.damp_field = SliderField(
            "Damp", 0, 5,
            lambda: self.app.physics.damping_coeff,
            self.app.set_damping,
            x, y, width,
        )
        y += 40
        self.temp_field = SliderField(
            "Temp", 0, 1000,
            lambda: self.app.physics.temperature,
            self.app.set_temperature,
            x, y, width,
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
        self.gx_field.draw(self.sidebar.screen)
        self.gy_field.draw(self.sidebar.screen)
        self.rep_rad_field.draw(self.sidebar.screen)
        self.rep_str_field.draw(self.sidebar.screen)
        self.damp_field.draw(self.sidebar.screen)
        self.temp_field.draw(self.sidebar.screen)

    def draw_preview(self):
        pass

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False
        if self.sidebar.visible:
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
