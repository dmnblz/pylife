import os
import sys
import math
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.append(str(Path(__file__).resolve().parents[1]))

from particle import Particle
from bending_spring import BendingSpring


def _make_bend(rest_deg: float, current_deg: float) -> BendingSpring:
    p2 = Particle((0, 0))
    p1 = Particle((1, 0))
    p3 = Particle((math.cos(math.radians(current_deg)), math.sin(math.radians(current_deg))))
    bs = BendingSpring(p1, p2, p3, math.radians(rest_deg), 10)
    bs.apply()
    return bs


def test_bending_color_rest() -> None:
    bs = _make_bend(90, 90)
    assert bs.get_color() == (200, 200, 200)


def test_bending_color_stretched() -> None:
    bs = _make_bend(90, 120)
    r, g, b = bs.get_color()
    assert r > g and r > b


def test_bending_color_compressed() -> None:
    bs = _make_bend(90, 60)
    r, g, b = bs.get_color()
    assert b > r and b > g
