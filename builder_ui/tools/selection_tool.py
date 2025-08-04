"""Tool for rectangular selection and batch operations."""

from __future__ import annotations

import pygame

import builder_io
from ..fields import ButtonField
from .base import Tool


class SelectionTool(Tool):
    """Select particles, springs and bends within a rectangle.

    The tool lets the user drag out a rectangle to capture entities and then
    perform batch actions such as deletion, parameter application, copy &
    paste or saving/loading substructures.  Selected particles can also be
    moved as a group by dragging them with the mouse.
    """

    def __init__(self, sidebar: "SidebarUI") -> None:
        super().__init__(sidebar)
        self.start_pos: pygame.Vector2 | None = None
        self.rect: pygame.Rect | None = None
        self.dragging_rect = False
        self.dragging_sel = False
        self.move_prev: pygame.Vector2 | None = None

        self.selected_particles: list = []
        self.selected_springs: list = []
        self.selected_bends: list = []
        self.clipboard: dict | None = None

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y
        self.apply_p_btn = ButtonField("Apply P Params", self.apply_particle_params, x, y, width)
        y += 40
        self.apply_s_btn = ButtonField("Apply S Params", self.apply_spring_params, x, y, width)
        y += 40
        self.delete_btn = ButtonField("Delete Sel", self.delete_selection, x, y, width)
        y += 40
        self.copy_btn = ButtonField("Copy", self.copy_selection, x, y, width)
        y += 40
        self.paste_btn = ButtonField("Paste", self.paste_clipboard, x, y, width)
        y += 40
        self.save_btn = ButtonField("Save Sel", self.save_selection, x, y, width)
        y += 40
        self.load_btn = ButtonField("Load Struct", self.load_structure, x, y, width)

    # ------------------------------------------------------------------ utilities
    def clear_selection(self) -> None:
        """Remove any currently selected entities."""
        self.selected_particles = []
        self.selected_springs = []
        self.selected_bends = []
        self.rect = None

    def _compute_selection(self) -> None:
        """Populate selection lists based on ``self.rect``."""
        if not self.rect:
            return
        rect = self.rect
        app = self.app
        self.selected_particles = [p for p in app.particles if rect.collidepoint(p.pos)]
        self.selected_springs = [
            s for s in app.springs if rect.collidepoint(((s.p1.pos + s.p2.pos) * 0.5))
        ]
        self.selected_bends = [
            b
            for b in app.bending_springs
            if rect.collidepoint(((b.p1.pos + b.p2.pos + b.p3.pos) / 3))
        ]

    # ------------------------------------------------------------------ actions
    def delete_selection(self) -> None:
        """Remove all currently selected entities from the scene."""
        if self.selected_particles or self.selected_springs or self.selected_bends:
            self.app.remove_entities(
                self.selected_particles, self.selected_springs, self.selected_bends
            )
            self.clear_selection()

    def apply_particle_params(self) -> None:
        """Apply current particle parameters to the selection."""
        params = self.app.particle
        for p in self.selected_particles:
            p.mass = params.mass
            p.radius = params.radius
            p.color = params.color

    def apply_spring_params(self) -> None:
        """Apply current spring parameters to the selection."""
        stiff = self.app.spring.stiffness
        for s in self.selected_springs:
            s.stiffness = stiff

    def copy_selection(self) -> None:
        """Store the current selection in an internal clipboard."""
        if self.selected_particles:
            self.clipboard = self.app._build_state(
                self.selected_particles, self.selected_springs, self.selected_bends
            )

    def paste_clipboard(self) -> None:
        """Insert a previously copied structure at the mouse position."""
        if not self.clipboard:
            return
        mouse = pygame.Vector2(pygame.mouse.get_pos())
        parts = self.clipboard.get("particles", [])
        if parts:
            min_x = min(p["pos"][0] for p in parts)
            min_y = min(p["pos"][1] for p in parts)
            offset = mouse - pygame.Vector2(min_x, min_y)
        else:
            offset = pygame.Vector2()
        self.app._apply_substate(self.clipboard, offset)

    def save_selection(self) -> None:
        """Prompt for a file and persist the current selection."""
        if self.selected_particles:
            state = self.app._build_state(
                self.selected_particles, self.selected_springs, self.selected_bends
            )
            builder_io.save_state_dialog(state)

    def load_structure(self) -> None:
        """Append a structure loaded from disk at the mouse position."""
        data = builder_io.load_state_dialog()
        if data:
            mouse = pygame.Vector2(pygame.mouse.get_pos())
            parts = data.get("particles", [])
            if parts:
                min_x = min(p["pos"][0] for p in parts)
                min_y = min(p["pos"][1] for p in parts)
                offset = mouse - pygame.Vector2(min_x, min_y)
            else:
                offset = pygame.Vector2()
            self.app._apply_substate(data, offset)

    # ------------------------------------------------------------------ drawing
    def draw_ui(self, offset: int = 0) -> bool:
        if not super().draw_ui(offset):
            return False
        self.apply_p_btn.draw(self.sidebar.screen, offset)
        self.apply_s_btn.draw(self.sidebar.screen, offset)
        self.delete_btn.draw(self.sidebar.screen, offset)
        self.copy_btn.draw(self.sidebar.screen, offset)
        self.paste_btn.draw(self.sidebar.screen, offset)
        self.save_btn.draw(self.sidebar.screen, offset)
        self.load_btn.draw(self.sidebar.screen, offset)
        return True

    def draw_preview(self) -> bool:
        if not super().draw_preview():
            return False
        if self.rect and self.dragging_rect:
            pygame.draw.rect(self.sidebar.screen, (200, 200, 200), self.rect, 1)
        for p in self.selected_particles:
            pygame.draw.circle(
                self.sidebar.screen,
                (0, 255, 0),
                (int(p.pos.x), int(p.pos.y)),
                p.radius + 4,
                2,
            )
        for s in self.selected_springs:
            pygame.draw.line(
                self.sidebar.screen,
                (0, 255, 0),
                s.p1.pos,
                s.p2.pos,
                3,
            )
        for b in self.selected_bends:
            pygame.draw.line(
                self.sidebar.screen,
                (255, 255, 0),
                b.p1.pos,
                b.p2.pos,
                3,
            )
            pygame.draw.line(
                self.sidebar.screen,
                (255, 255, 0),
                b.p2.pos,
                b.p3.pos,
                3,
            )
        return True

    # ------------------------------------------------------------------ event handling
    def handle_event(self, event, offset: int = 0):
        if not super().handle_event(event, offset):
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect and self.rect.collidepoint(event.pos):
                self.dragging_sel = True
                self.move_prev = pygame.Vector2(event.pos)
            else:
                self.start_pos = pygame.Vector2(event.pos)
                self.rect = pygame.Rect(self.start_pos, (0, 0))
                self.dragging_rect = True
                self.clear_selection()
            return True
        if event.type == pygame.MOUSEMOTION:
            if self.dragging_rect and self.rect and self.start_pos:
                self.rect.width = event.pos[0] - self.start_pos.x
                self.rect.height = event.pos[1] - self.start_pos.y
                return True
            if self.dragging_sel and self.rect and self.move_prev:
                delta = pygame.Vector2(event.pos) - self.move_prev
                for p in self.selected_particles:
                    p.pos += delta
                    p.prev_pos += delta
                self.rect.x += delta.x
                self.rect.y += delta.y
                self.move_prev = pygame.Vector2(event.pos)
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_rect and self.rect:
                self.dragging_rect = False
                self.rect.normalize_ip()
                self._compute_selection()
                return True
            if self.dragging_sel:
                self.dragging_sel = False
                return True
        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                self.delete_selection()
                return True
            if event.key == pygame.K_c and mods & pygame.KMOD_CTRL:
                if mods & pygame.KMOD_SHIFT:
                    self.apply_particle_params()
                else:
                    self.copy_selection()
                return True
            if event.key == pygame.K_v and mods & pygame.KMOD_CTRL:
                self.paste_clipboard()
                return True
            if event.key == pygame.K_s and mods & pygame.KMOD_CTRL:
                self.save_selection()
                return True
            if event.key == pygame.K_l and mods & pygame.KMOD_CTRL:
                self.load_structure()
                return True
            if event.key == pygame.K_k and mods & pygame.KMOD_CTRL:
                self.apply_spring_params()
                return True
        if self.apply_p_btn.handle_event(event, offset):
            return True
        if self.apply_s_btn.handle_event(event, offset):
            return True
        if self.delete_btn.handle_event(event, offset):
            return True
        if self.copy_btn.handle_event(event, offset):
            return True
        if self.paste_btn.handle_event(event, offset):
            return True
        if self.save_btn.handle_event(event, offset):
            return True
        if self.load_btn.handle_event(event, offset):
            return True
        return False
