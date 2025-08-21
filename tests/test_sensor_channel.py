import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
import math
from builder_app import BuilderApp
from particle import Particle
from sensor_particle import SensorParticle
from variable_particle import VariableParticle
from variable_spring import VariableSpring
from variable_bending_spring import VariableBendingSpring
from channel import ChannelControlled


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
    app._apply_channel_signals()
    assert vp.active is True
    app._apply_channel_signals()
    assert vp.active is False
    pygame.quit()


def test_channelled_variable_respects_key():
    app = BuilderApp()
    vp = VariableParticle((0, 0), mode="toggle", key=pygame.K_a, channel=1)
    app.variable_particles.append(vp)
    app.register_variable_particle(vp)
    vp.on_keydown()
    assert vp.active is True
    app._apply_channel_signals()
    assert vp.active is True
    pygame.quit()


def test_channel_signals_update_all_types():
    app = BuilderApp()
    p1 = Particle((0, 0))
    p2 = Particle((10, 0))
    p3 = Particle((20, 0))
    vp = VariableParticle((0, 0), channel=1)
    vs = VariableSpring(p1, p2, 10, 20, 10, channel=1)
    vb = VariableBendingSpring(p1, p2, p3, math.pi / 2, math.pi / 3, 10, channel=1)
    app.particles.extend([p1, p2, p3, vp])
    app.variable_particles.append(vp)
    app.variable_springs.append(vs)
    app.variable_bending_springs.append(vb)
    app.register_variable_particle(vp)
    app.register_variable_spring(vs)
    app.register_variable_bend(vb)
    assert isinstance(vp, ChannelControlled)
    assert isinstance(vs, ChannelControlled)
    assert isinstance(vb, ChannelControlled)
    app._signal_channel(1)
    app._apply_channel_signals()
    assert vp.active is True
    assert vs.active is True
    assert vb.active is True
    app._apply_channel_signals()
    assert vp.active is False
    assert vs.active is False
    assert vb.active is False
    pygame.quit()
