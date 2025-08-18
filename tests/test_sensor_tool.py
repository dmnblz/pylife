import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from builder_app import BuilderApp
from sensor_particle import SensorParticle


def test_sensor_tool_creates_sensor():
    app = BuilderApp()
    app.set_mode("sensor")
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (100, 100)})
    app.ui.sensor_tool.handle_event(event, 0)
    assert len(app.sensors) == 1
    s = app.sensors[0]
    assert isinstance(s, SensorParticle)
    assert s in app.particles
    assert s.sense_radius == app.sensor.radius
    pygame.quit()
