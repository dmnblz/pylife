"""Tests for the :mod:`sensor` module."""

import math

import pygame

from sensor_particle import SensorParticle


class Dummy:
    def __init__(self, pos, tag=None):
        self.pos = pygame.Vector2(pos)
        self.tag = tag


def test_triggers_on_tag():
    sensor = SensorParticle((0, 0), sense_radius=10, tags={"enemy"})
    seen = []
    sensor.add_callback(lambda s, o: seen.append(o))
    enemy = Dummy((5, 0), "enemy")
    sensor.check(enemy)
    assert seen == [enemy]


def test_wedge_filters_direction():
    sensor = SensorParticle((0, 0), forward=(1, 0), sense_radius=10, half_angle=math.pi / 4)
    seen = []
    sensor.add_callback(lambda s, o: seen.append(o))
    inside = Dummy((5, 1))
    outside = Dummy((-5, 0))
    sensor.check(inside)
    sensor.check(outside)
    assert seen == [inside]
