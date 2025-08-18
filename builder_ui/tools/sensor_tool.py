"""Tool for placing sensor objects."""

import math
import pygame
from sensor import Sensor

from ..fields import SliderField
from .base import Tool


class SensorTool(Tool):
    """UI controls and placement logic for sensors."""

    def __init__(self, sidebar: "SidebarUI") -> None:
        super().__init__(sidebar)
        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.radius_field = SliderField(
            "Radius",
            1,
            200,
            self._get_radius,
            self._set_radius,
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

    def draw_ui(self, offset: int = 0) -> None:
        if not super().draw_ui(offset):
            return
        self.radius_field.draw(self.sidebar.screen, offset)
        self.angle_field.draw(self.sidebar.screen, offset)
        self.dir_field.draw(self.sidebar.screen, offset)

    def handle_event(self, event, offset: int = 0) -> bool:
        if not super().handle_event(event, offset):
            return False
        if self.radius_field.handle_event(event, offset):
            return True
        if self.angle_field.handle_event(event, offset):
            return True
        if self.dir_field.handle_event(event, offset):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                world = self.sidebar.app.screen_to_world(event.pos)
                forward = pygame.Vector2(1, 0).rotate(self.app.sensor.direction_deg)
                sensor = Sensor(
                    world,
                    forward=forward,
                    radius=self.app.sensor.radius,
                    half_angle=math.radians(self.app.sensor.half_angle_deg),
                )
                self.app.sensors.append(sensor)
                self.app.push_undo(lambda s=sensor: self.app.remove_entities(sensors=[s]))
                return True
        return False

    def _get_radius(self) -> float:
        return self.app.sensor.radius

    def _set_radius(self, value: float) -> None:
        self.app.sensor.radius = max(1.0, value)

    def _get_angle(self) -> float:
        return self.app.sensor.half_angle_deg

    def _set_angle(self, value: float) -> None:
        self.app.sensor.half_angle_deg = max(0.0, min(180.0, value))

    def _get_dir(self) -> float:
        return self.app.sensor.direction_deg

    def _set_dir(self, value: float) -> None:
        self.app.sensor.direction_deg = value % 360
