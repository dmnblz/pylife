import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import math
import pygame
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from builder_app import BuilderApp
from sensor_particle import SensorParticle


def test_inspect_tool_edits_sensor() -> None:
    app = BuilderApp()
    sensor = SensorParticle((0, 0), sense_radius=20, half_angle=math.radians(30))
    app.particles.append(sensor)
    app.sensors.append(sensor)
    app.set_mode("inspect")

    pos = app.world_to_screen(sensor.pos)
    event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (int(pos.x), int(pos.y))}
    )
    app.ui.inspect_tool.handle_event(event, 0)
    assert app.ui.inspect_tool.particle is sensor

    app.ui.inspect_tool._set_sense_radius(80)
    app.ui.inspect_tool._set_sense_angle(90)
    app.ui.inspect_tool._set_sense_dir(45)

    assert sensor.sense_radius == 80
    assert math.isclose(sensor.half_angle, math.radians(90))
    direction = math.degrees(math.atan2(sensor.forward.y, sensor.forward.x)) % 360
    assert round(direction) == 45
    pygame.quit()

