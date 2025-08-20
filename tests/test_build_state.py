import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from builder_app import BuilderApp
from variable_particle import VariableParticle
from sensor_particle import SensorParticle


def test_build_state_handles_variable_and_sensor() -> None:
    app = BuilderApp()
    vp = VariableParticle((0, 0))
    sp = SensorParticle((1, 1))
    app.particles = [vp, sp]
    app.variable_particles = [vp]
    app.sensors = [sp]
    state = app._build_state()
    types = [p.get("type") for p in state["particles"]]
    assert "variable" in types
    assert "sensor" in types
    pygame.quit()
