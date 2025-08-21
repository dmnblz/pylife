import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from builder_app import BuilderApp
from particle import Particle
from variable_particle import VariableParticle


def test_convert_particle_sets_activation_flags() -> None:
    app = BuilderApp()
    p = Particle((0, 0))
    app.particles.append(p)
    tool = app.ui.inspect_tool
    tool.particle = p
    tool._convert_particle()
    assert isinstance(p, VariableParticle)
    assert hasattr(p, "key_active")
    assert hasattr(p, "channel_active")
    p.set_channel_active(True)
    assert p.active
    pygame.quit()
