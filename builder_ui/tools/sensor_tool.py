"""Tool for placing sensor particles."""

import math
import pygame

from sensor_particle import SensorParticle

from ..fields import SliderField, ButtonField
from .particle_tool import ParticleTool
from .base import Tool


class SensorTool(ParticleTool):
    """Particle tool with additional sensor configuration."""

    def __init__(self, sidebar: "SidebarUI") -> None:
        super().__init__(sidebar)
        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y + 160
        self.range_field = SliderField(
            "Range",
            1,
            200,
            self._get_range,
            self._set_range,
            x,
            y,
            width,
        )
        y += 40
        self.angle_field = SliderField(
            "HalfAng",
            0,
            180,
            self._get_angle,
            self._set_angle,
            x,
            y,
            width,
        )
        y += 40
        self.dir_field = SliderField(
            "Direction",
            0,
            360,
            self._get_dir,
            self._set_dir,
            x,
            y,
            width,
        )
        y += 40
        self.channel_field = SliderField(
            "Channel",
            0,
            9,
            self._get_channel,
            self._set_channel,
            x,
            y,
            width,
        )
        y += 40
        self.trigger_btn = ButtonField(
            lambda: f"Trigger: {self._trigger_label()}",
            self._start_choose_trigger,
            x,
            y,
            width,
        )
        self.await_trigger = False

    def draw_ui(self, offset: int = 0) -> None:
        """Render sensor configuration sliders."""
        if not Tool.draw_ui(self, offset):
            return
        ParticleTool.draw_ui(self, offset)
        self.range_field.draw(self.sidebar.screen, offset)
        self.angle_field.draw(self.sidebar.screen, offset)
        self.dir_field.draw(self.sidebar.screen, offset)
        self.channel_field.draw(self.sidebar.screen, offset)
        self.trigger_btn.draw(self.sidebar.screen, offset)

    def handle_event(self, event, offset: int = 0) -> bool:
        if not Tool.handle_event(self, event, offset):
            return False
        if self.color_field.handle_event(event, offset):
            return True
        if self.mass_field.handle_event(event, offset):
            return True
        if self.radius_field.handle_event(event, offset):
            return True
        if self.elasticity_field.handle_event(event, offset):
            return True
        if self.range_field.handle_event(event, offset):
            return True
        if self.angle_field.handle_event(event, offset):
            return True
        if self.dir_field.handle_event(event, offset):
            return True
        if self.channel_field.handle_event(event, offset):
            return True
        if self.trigger_btn.handle_event(event, offset):
            return True
        if self.await_trigger and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                if self.app.particles:
                    mouse = self.sidebar.app.screen_to_world(event.pos)
                    p = min(self.app.particles, key=lambda q: (q.pos - mouse).length())
                    self.app.sensor.trigger = p
            self.await_trigger = False
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                world = self.sidebar.app.screen_to_world(event.pos)
                forward = pygame.Vector2(1, 0).rotate(self.app.sensor.direction_deg)
                sensor = SensorParticle(
                    world,
                    forward=forward,
                    sense_radius=self.app.sensor.sense_radius,
                    half_angle=math.radians(self.app.sensor.half_angle_deg),
                    channel=self.app.sensor.channel,
                    mass=self.app.sensor.mass,
                    color=self.app.sensor.color,
                    radius=self.app.sensor.particle_radius,
                    elasticity=self.app.sensor.elasticity,
                    trail_length=self.app.environment.trail_length,
                    trigger=self.app.sensor.trigger,
                )
                if sensor.trigger:
                    sensor.add_callback(lambda s, o: print("Sensor triggered"))
                self.app.particles.append(sensor)
                self.app.sensors.append(sensor)
                self.app.register_sensor(sensor)
                self.app.push_undo(
                    lambda s=sensor: self.app.remove_entities([s], sensors=[s])
                )
                return True
        return False

    def _get_range(self) -> float:
        return self.app.sensor.sense_radius

    def _set_range(self, value: float) -> None:
        self.app.sensor.sense_radius = max(1.0, value)

    def _get_angle(self) -> float:
        return self.app.sensor.half_angle_deg

    def _set_angle(self, value: float) -> None:
        self.app.sensor.half_angle_deg = max(0.0, min(180.0, value))

    def _get_dir(self) -> float:
        return self.app.sensor.direction_deg

    def _set_dir(self, value: float) -> None:
        self.app.sensor.direction_deg = value % 360

    def _get_channel(self) -> float:
        return float(self.app.sensor.channel or 0)

    def _set_channel(self, value: float) -> None:
        self.app.sensor.channel = int(value)

    def _trigger_label(self) -> str:
        t = self.app.sensor.trigger
        if t and t in self.app.particles:
            return str(self.app.particles.index(t))
        return "-"

    def _start_choose_trigger(self) -> None:
        self.await_trigger = True

    # override particle parameter accessors to use sensor defaults

    def _get_color(self) -> tuple[int, int, int]:
        return self.app.sensor.color

    def _set_color(self, color: tuple[int, int, int]) -> None:
        self.app.sensor.color = color

    def _get_mass(self) -> float:
        return self.app.sensor.mass

    def _set_mass(self, value: float) -> None:
        self.app.sensor.mass = max(0.1, value)

    def _get_radius(self) -> float:
        return self.app.sensor.particle_radius

    def _set_radius(self, value: float) -> None:
        self.app.sensor.particle_radius = max(1, int(value))

    def _get_elasticity(self) -> float:
        return self.app.sensor.elasticity

    def _set_elasticity(self, value: float) -> None:
        self.app.sensor.elasticity = max(0.0, min(1.0, value))
