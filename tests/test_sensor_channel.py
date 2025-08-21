import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
from builder_app import BuilderApp
from particle import Particle
from sensor_particle import SensorParticle
from variable_particle import VariableParticle


def test_sensor_channel_toggles_variable():
    app = BuilderApp()
    trigger = Particle((0, 0))
    vp = VariableParticle((0, 0), mode="toggle", channel=1)
    sensor = SensorParticle((0, 0), sense_radius=10, trigger=trigger, channel=1)
    app.particles.extend([trigger, vp, sensor])
    app.variable_particles.append(vp)
    app.register_variable_particle(vp)
    app.sensors.append(sensor)
    app.register_sensor(sensor)
    sensor.check(trigger)
    assert vp.active is True
    sensor.check(trigger)
    assert vp.active is False
    pygame.quit()
