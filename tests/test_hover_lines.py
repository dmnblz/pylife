import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

sys.path.append(str(Path(__file__).resolve().parents[1]))

from builder_ui.tools.inspect_tool import InspectTool
import math
from particle import Particle
from spring import Spring
from variable_particle import VariableParticle
from variable_spring import VariableSpring
from variable_bending_spring import VariableBendingSpring
from sensor_particle import SensorParticle


class DummyScreen:
    def get_width(self) -> int:
        return 800


class DummySidebar:
    WIDTH = 200
    extra_start_y = 0
    screen = DummyScreen()
    app = None


def make_tool() -> InspectTool:
    pygame.init()
    return InspectTool(DummySidebar())


def test_hover_lines_spring() -> None:
    tool = make_tool()
    p1 = Particle((0, 0))
    p2 = Particle((10, 0))
    spring = Spring(p1, p2, 10, 200)
    lines = tool.get_hover_lines(spring)
    assert any(line.startswith("S Rest") for line in lines)


def test_hover_lines_variable_spring() -> None:
    tool = make_tool()
    p1 = Particle((0, 0))
    p2 = Particle((10, 0))
    vspring = VariableSpring(p1, p2, 10, 20, 200)
    lines = tool.get_hover_lines(vspring)
    assert any(line.startswith("V Rest2") for line in lines)


def test_hover_lines_variable_particle() -> None:
    tool = make_tool()
    vparticle = VariableParticle((0, 0), radius=5)
    lines = tool.get_hover_lines(vparticle)
    assert any(line.startswith("V Drag") for line in lines)


def test_hover_lines_variable_bend() -> None:
    tool = make_tool()
    p1 = Particle((0, 0))
    p2 = Particle((10, 0))
    p3 = Particle((10, 10))
    vbend = VariableBendingSpring(p1, p2, p3, math.radians(90), math.radians(45), 200)
    lines = tool.get_hover_lines(vbend)
    assert any(line.startswith("V Ang2") for line in lines)


def test_hover_lines_sensor() -> None:
    tool = make_tool()
    sensor = SensorParticle((0, 0), sense_radius=30, half_angle=math.radians(60), radius=5)
    lines = tool.get_hover_lines(sensor)
    assert any(line.startswith("S Range") for line in lines)
    assert any(line.startswith("S HalfAng") for line in lines)
