import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from builder_app import BuilderApp
from particle import Particle
from sensor_particle import SensorParticle


def test_sensor_tool_links_trigger_by_drag():
    app = BuilderApp()
    target = Particle((50, 50))
    sensor = SensorParticle((100, 100))
    app.particles.extend([target, sensor])
    app.sensors.append(sensor)
    app.set_mode("sensor")
    tool = app.ui.sensor_tool
    pos_s = app.world_to_screen(sensor.pos)
    down = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (int(pos_s.x), int(pos_s.y))}
    )
    tool.handle_event(down, 0)
    pos_t = app.world_to_screen(target.pos)
    pygame.mouse.set_pos((int(pos_t.x), int(pos_t.y)))
    app._update_hover_targets()
    up = pygame.event.Event(
        pygame.MOUSEBUTTONUP, {"button": 1, "pos": (int(pos_t.x), int(pos_t.y))}
    )
    tool.handle_event(up, 0)
    assert sensor.trigger is target
    pygame.quit()


def test_inspect_tool_links_trigger_by_drag():
    app = BuilderApp()
    trigger = Particle((10, 10))
    sensor = SensorParticle((0, 0))
    app.particles.extend([trigger, sensor])
    app.sensors.append(sensor)
    app.set_mode("inspect")
    tool = app.ui.inspect_tool
    pos_s = app.world_to_screen(sensor.pos)
    evt = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (int(pos_s.x), int(pos_s.y))}
    )
    tool.handle_event(evt, 0)
    pos_t = app.world_to_screen(trigger.pos)
    motion = pygame.event.Event(
        pygame.MOUSEMOTION,
        {"pos": (int(pos_t.x), int(pos_t.y)), "rel": (0, 0), "buttons": (1, 0, 0)},
    )
    tool.handle_event(motion, 0)
    pygame.mouse.set_pos((int(pos_t.x), int(pos_t.y)))
    app._update_hover_targets()
    up = pygame.event.Event(
        pygame.MOUSEBUTTONUP, {"button": 1, "pos": (int(pos_t.x), int(pos_t.y))}
    )
    tool.handle_event(up, 0)
    assert sensor.trigger is trigger
    pygame.quit()
