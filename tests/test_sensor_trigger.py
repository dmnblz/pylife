import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from builder_app import BuilderApp
from particle import Particle
from sensor_particle import SensorParticle


def test_sensor_tool_sets_trigger():
    app = BuilderApp()
    target = Particle((50, 50))
    app.particles.append(target)
    app.set_mode("sensor")
    tool = app.ui.sensor_tool
    tool._start_choose_trigger()
    select_evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (50, 50)})
    tool.handle_event(select_evt, 0)
    place_evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (100, 100)})
    tool.handle_event(place_evt, 0)
    sensor = app.sensors[0]
    assert sensor.trigger is target
    pygame.quit()


def test_inspect_tool_sets_trigger():
    app = BuilderApp()
    trigger = Particle((10, 10))
    sensor = SensorParticle((0, 0))
    app.particles.extend([trigger, sensor])
    app.sensors.append(sensor)
    app.set_mode("inspect")
    pos = app.world_to_screen(sensor.pos)
    evt = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (int(pos.x), int(pos.y))})
    app.ui.inspect_tool.handle_event(evt, 0)
    app.ui.inspect_tool._start_choose_trigger()
    pos_t = app.world_to_screen(trigger.pos)
    evt2 = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (int(pos_t.x), int(pos_t.y))})
    app.ui.inspect_tool.handle_event(evt2, 0)
    assert sensor.trigger is trigger
    pygame.quit()
