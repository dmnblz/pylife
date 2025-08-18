"""Tests for grid snapping when creating particles."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from builder_app import BuilderApp


def make_app() -> BuilderApp:
    app = BuilderApp()
    app.grid_enabled = True
    app.grid_size = 40
    app.camera_offset = pygame.Vector2(100, 50)
    app.renderer.set_camera(app.camera_offset, app.camera_zoom)
    return app


def test_particle_snap_to_grid_with_camera_offset() -> None:
    app = make_app()
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (15, 25), "button": 1})
    app.handle_particle_event(event)
    assert app.particles[-1].pos == pygame.Vector2(120, 80)


def test_variable_particle_snap_to_grid_with_camera_offset() -> None:
    app = make_app()
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (15, 25), "button": 1})
    app.handle_variable_particle_event(event)
    assert app.particles[-1].pos == pygame.Vector2(120, 80)


def test_particle_snap_with_negative_world_coords() -> None:
    app = make_app()
    app.camera_offset = pygame.Vector2(-90, -10)
    app.renderer.set_camera(app.camera_offset, app.camera_zoom)
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (15, 25), "button": 1})
    app.handle_particle_event(event)
    assert app.particles[-1].pos == pygame.Vector2(-80, 0)

