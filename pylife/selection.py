"""Selection and clipboard management for the builder.

Encapsulates selected objects, rectangle selection, copy/paste, and
preview drawing. Holds a reference to the app to operate on scene data
and registries without duplicating ownership.
"""
from __future__ import annotations

from typing import Iterable
import math
import pygame

from builder_ui import theme
from particle import Particle
from spring import Spring
from bending_spring import BendingSpring
from variable_particle import VariableParticle
from variable_spring import VariableSpring
from variable_bending_spring import VariableBendingSpring
from hook_arm import HookArm


class SelectionManager:
    def __init__(self, app: "BuilderApp") -> None:
        self.app = app
        # selection lists live on the app; keep only geometry here
        self.selection_start: pygame.Vector2 | None = None
        self.selection_rect: pygame.Rect | None = None
        # clipboard lives on the app; use app.clipboard when needed

    # selection lists ---------------------------------------------------
    def clear(self) -> None:
        for p in self.app.selected_particles:
            if hasattr(p, "selected"):
                delattr(p, "selected")
        for s in self.app.selected_springs:
            if hasattr(s, "selected"):
                delattr(s, "selected")
        for b in self.app.selected_bends:
            if hasattr(b, "selected"):
                delattr(b, "selected")
        self.app.selected_particles.clear()
        self.app.selected_springs.clear()
        self.app.selected_bends.clear()

    def delete_selection(self) -> None:
        if not (self.app.selected_particles or self.app.selected_springs or self.app.selected_bends):
            return
        particles = list(self.app.selected_particles)
        springs = list(self.app.selected_springs)
        bends = list(self.app.selected_bends)
        for s in self.app.springs:
            if (s.p1 in particles or s.p2 in particles) and s not in springs:
                springs.append(s)
        for b in self.app.bending_springs:
            if (b.p1 in particles or b.p2 in particles or b.p3 in particles) and b not in bends:
                bends.append(b)
        self.app.remove_entities(particles, springs, bends)
        self.app.push_undo(
            lambda parts=particles, sprs=springs, bds=bends: self._restore_entities(parts, sprs, bds)
        )
        self.clear()

    # internal restore used by delete undo ------------------------------
    def _restore_entities(
        self, particles: list[Particle], springs: list[Spring], bends: list[BendingSpring] | None = None
    ) -> None:
        self.app.particles.extend(particles)
        self.app.springs.extend(springs)
        if bends:
            self.app.bending_springs.extend(bends)
            for b in bends:
                if isinstance(b, VariableBendingSpring):
                    self.app.variable_bending_springs.append(b)
                    self.app.register_variable_bend(b)
        for p in particles:
            if isinstance(p, VariableParticle):
                self.app.variable_particles.append(p)
                self.app.register_variable_particle(p)
        for s in springs:
            if isinstance(s, VariableSpring):
                self.app.variable_springs.append(s)
                self.app.register_variable_spring(s)

    # copy/paste --------------------------------------------------------
    def copy(self) -> None:
        if not (self.app.selected_particles or self.app.selected_springs or self.app.selected_bends):
            return
        origin_x = min(p.pos.x for p in self.app.selected_particles)
        origin_y = min(p.pos.y for p in self.app.selected_particles)
        origin = pygame.Vector2(origin_x, origin_y)
        self.app.clipboard = {"particles": [], "springs": [], "bends": [], "arms": []}
        for p in self.app.selected_particles:
            data = {
                "offset": p.pos - origin,
                "mass": p.mass,
                "color": p.color,
                "radius": p.radius,
                "tag": p.tag,
                "drag": p.drag,
                "fixed": p.fixed,
                "type": "variable" if isinstance(p, VariableParticle) else "particle",
            }
            if isinstance(p, VariableParticle):
                data.update(
                    {
                        "base_drag": p.base_drag,
                        "alt_drag": p.alt_drag,
                        "key": p.key,
                        "mode": p.mode,
                        "change_speed": p.change_speed,
                        "active": p.active,
                    }
                )
            self.app.clipboard["particles"].append(data)
        index = {p: i for i, p in enumerate(self.app.selected_particles)}
        for s in self.app.selected_springs:
            data = {
                "p1": index[s.p1],
                "p2": index[s.p2],
                "rest_length": s.rest_length,
                "stiffness": s.stiffness,
                "max_force": s.max_force,
                "invisible": s.invisible,
                "type": "variable" if isinstance(s, VariableSpring) else "spring",
            }
            if isinstance(s, VariableSpring):
                data.update(
                    {
                        "base_rest": s.base_rest_length,
                        "alt_rest": s.alt_rest_length,
                        "key": s.key,
                        "mode": s.mode,
                        "change_speed": s.change_speed,
                        "active": s.active,
                    }
                )
            self.app.clipboard["springs"].append(data)
        spring_index = {s: i for i, s in enumerate(self.app.selected_springs)}
        for b in self.app.selected_bends:
            data = {
                "p1": index[b.p1],
                "p2": index[b.p2],
                "p3": index[b.p3],
                "angle": b.rest_angle,
                "stiffness": b.stiffness,
                "type": "variable" if isinstance(b, VariableBendingSpring) else "bend",
            }
            if isinstance(b, VariableBendingSpring):
                data.update(
                    {
                        "base_angle": b.base_angle,
                        "alt_angle": b.alt_angle,
                        "key": b.key,
                        "mode": b.mode,
                        "change_speed": b.change_speed,
                        "active": b.active,
                    }
                )
            self.app.clipboard["bends"].append(data)
        for arm in self.app.arms:
            if all(p in index for p in arm.particles) and all(s in spring_index for s in arm.springs):
                data = {
                    "particles": [index[p] for p in arm.particles],
                    "springs": [spring_index[s] for s in arm.springs],
                    "rest_lengths": arm.rest_lengths,
                    "max_lengths": arm.max_lengths,
                    "cycle_speed": arm.cycle_speed,
                    "color": list(arm.color),
                    "high_color": list(arm.high_drag_color),
                    "adhesion": arm.adhesion_mass_factor,
                    "orig_mass": arm._orig_mass,
                    "adhesion_drag": arm.adhesion_drag,
                    "orig_drag": arm._orig_drag,
                    "cycle_key": arm.cycle_key,
                }
                self.app.clipboard["arms"].append(data)

    def paste(self, anchor: pygame.Vector2) -> None:
        if not self.app.clipboard["particles"]:
            return
        app = self.app
        new_particles: list[Particle] = []
        for pdata in self.app.clipboard["particles"]:
            pos = anchor + pdata["offset"]
            if pdata["type"] == "variable":
                p = VariableParticle(
                    pos,
                    mass=pdata["mass"],
                    color=pdata["color"],
                    radius=pdata["radius"],
                    base_drag=pdata["base_drag"],
                    alt_drag=pdata["alt_drag"],
                    key=pdata["key"],
                    mode=pdata["mode"],
                    change_speed=pdata["change_speed"],
                    trail_length=app.environment.trail_length,
                )
                p.active = pdata["active"]
                p.drag = pdata["drag"]
            else:
                p = Particle(
                    pos,
                    mass=pdata["mass"],
                    color=pdata["color"],
                    radius=pdata["radius"],
                    tag=pdata["tag"],
                    drag=pdata["drag"],
                    trail_length=app.environment.trail_length,
                )
            p.fixed = pdata["fixed"]
            new_particles.append(p)
        index_map = {i: p for i, p in enumerate(new_particles)}
        new_springs: list[Spring] = []
        new_bends: list[BendingSpring] = []
        new_arms: list[HookArm] = []
        for sdata in self.app.clipboard["springs"]:
            p1 = index_map[sdata["p1"]]
            p2 = index_map[sdata["p2"]]
            if sdata["type"] == "variable":
                s = VariableSpring(
                    p1,
                    p2,
                    sdata["base_rest"],
                    sdata["alt_rest"],
                    sdata["stiffness"],
                    key=sdata["key"],
                    mode=sdata["mode"],
                    change_speed=sdata["change_speed"],
                    max_force=sdata["max_force"],
                    invisible=sdata["invisible"],
                )
                s.rest_length = sdata["rest_length"]
                s.active = sdata["active"]
            else:
                s = Spring(
                    p1,
                    p2,
                    sdata["rest_length"],
                    sdata["stiffness"],
                    sdata["max_force"],
                    sdata["invisible"],
                )
            new_springs.append(s)
        for bdata in self.app.clipboard["bends"]:
            p1 = index_map[bdata["p1"]]
            p2 = index_map[bdata["p2"]]
            p3 = index_map[bdata["p3"]]
            if bdata.get("type") == "variable":
                b = VariableBendingSpring(
                    p1,
                    p2,
                    p3,
                    bdata["base_angle"],
                    bdata["alt_angle"],
                    bdata["stiffness"],
                    key=bdata["key"],
                    mode=bdata["mode"],
                    change_speed=bdata["change_speed"],
                )
                b.rest_angle = bdata["angle"]
                b.active = bdata["active"]
            else:
                b = BendingSpring(p1, p2, p3, bdata["angle"], bdata["stiffness"])
            new_bends.append(b)
        for adata in self.app.clipboard["arms"]:
            arm = HookArm.__new__(HookArm)
            arm.particles = [new_particles[i] for i in adata["particles"]]
            arm.springs = [new_springs[i] for i in adata["springs"]]
            arm.color = tuple(adata["color"])
            arm.high_drag_color = tuple(adata["high_color"])
            arm.adhesion_mass_factor = adata["adhesion"]
            arm.adhesion_drag = adata["adhesion_drag"]
            arm.cycle_speed = adata["cycle_speed"]
            arm.rest_lengths = adata["rest_lengths"]
            arm.max_lengths = adata["max_lengths"]
            arm.tip = arm.particles[-1]
            arm._orig_mass = adata["orig_mass"]
            arm._orig_drag = adata["orig_drag"]
            arm.extend_held = False
            arm.contract_held = False
            arm.cycle_held = False
            arm.cycle_active = False
            arm.cycle_phase = 0
            arm.cycle_key = adata.get("cycle_key")
            if arm.cycle_key is not None:
                self.app.cycle_keys.setdefault(arm.cycle_key, []).append(arm)
            arm._set_high_drag(False)
            new_arms.append(arm)
        app.particles.extend(new_particles)
        app.springs.extend(new_springs)
        app.bending_springs.extend(new_bends)
        app.arms.extend(new_arms)
        for p in new_particles:
            if isinstance(p, VariableParticle):
                app.variable_particles.append(p)
                app.register_variable_particle(p)
        for s in new_springs:
            if isinstance(s, VariableSpring):
                app.variable_springs.append(s)
                app.register_variable_spring(s)
        for b in new_bends:
            if isinstance(b, VariableBendingSpring):
                app.variable_bending_springs.append(b)
                app.register_variable_bend(b)
        self.clear()
        for p in new_particles:
            p.selected = True
            app.selected_particles.append(p)
        for s in new_springs:
            s.selected = True
            app.selected_springs.append(s)
        for b in new_bends:
            b.selected = True
            app.selected_bends.append(b)
        self.app.push_undo(
            lambda parts=new_particles, sprs=new_springs, bends=new_bends, arms=new_arms: self.app.remove_entities(
                parts, sprs, bends, arms
            )
        )

    def draw_paste_preview(self) -> None:
        app = self.app
        if not app.pasting or not app.clipboard["particles"]:
            return
        anchor = app.screen_to_world(pygame.mouse.get_pos())
        overlay = pygame.Surface(app.screen.get_size(), pygame.SRCALPHA)
        col = theme.ACCENT + (80,)
        for pdata in app.clipboard["particles"]:
            pos = anchor + pdata["offset"]
            c = app.world_to_screen(pos)
            r = int((pdata["radius"] or 5) * app.camera_zoom)
            pygame.draw.circle(overlay, col, (int(c.x), int(c.y)), r)
        for sdata in app.clipboard["springs"]:
            p1 = anchor + app.clipboard["particles"][sdata["p1"]]["offset"]
            p2 = anchor + app.clipboard["particles"][sdata["p2"]]["offset"]
            a = app.world_to_screen(p1)
            b = app.world_to_screen(p2)
            pygame.draw.line(overlay, col, a, b, 2)
        for bdata in app.clipboard["bends"]:
            p1 = anchor + app.clipboard["particles"][bdata["p1"]]["offset"]
            p2 = anchor + app.clipboard["particles"][bdata["p2"]]["offset"]
            p3 = anchor + app.clipboard["particles"][bdata["p3"]]["offset"]
            a = app.world_to_screen(p1)
            b = app.world_to_screen(p2)
            c = app.world_to_screen(p3)
            pygame.draw.line(overlay, col, a, b, 1)
            pygame.draw.line(overlay, col, b, c, 1)
        app.screen.blit(overlay, (0, 0))

    # selection handling -------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        app = self.app
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] >= app.screen.get_width() - app.ui.visible_width():
                return
            self.selection_start = pygame.Vector2(event.pos)
            self.selection_rect = pygame.Rect(self.selection_start, (0, 0))
        elif event.type == pygame.MOUSEMOTION and self.selection_start:
            end = pygame.Vector2(event.pos)
            rect = pygame.Rect(self.selection_start, (end.x - self.selection_start.x, end.y - self.selection_start.y))
            rect.normalize()
            self.selection_rect = rect
        elif (
            event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.selection_rect is not None
        ):
            mods = pygame.key.get_mods()
            additive = bool(mods & (pygame.KMOD_CTRL | pygame.KMOD_META))
            rect_px = self.selection_rect
            is_click = rect_px.width < 4 and rect_px.height < 4
            if is_click:
                mx, my = int(self.selection_start.x), int(self.selection_start.y)
                mouse_screen = (mx, my)
                particle_threshold_px = 30
                spring_threshold_px = 12
                # nearest particle
                nearest_p = None
                best_dp = float("inf")
                for p in app.particles:
                    ps = app.world_to_screen(p.pos)
                    dp = ((ps.x - mx) ** 2 + (ps.y - my) ** 2) ** 0.5
                    if dp < best_dp:
                        best_dp = dp
                        nearest_p = p
                # nearest spring
                def seg_dist(a_world, b_world):
                    a = app.world_to_screen(a_world)
                    b = app.world_to_screen(b_world)
                    ax, ay = a.x, a.y
                    bx, by = b.x, b.y
                    mx_, my_ = float(mx), float(my)
                    vx, vy = bx - ax, by - ay
                    seg_len2 = vx * vx + vy * vy
                    if seg_len2 == 0:
                        dx, dy = mx_ - ax, my_ - ay
                        return (dx * dx + dy * dy) ** 0.5
                    t = ((mx_ - ax) * vx + (my_ - ay) * vy) / seg_len2
                    t = max(0.0, min(1.0, t))
                    px, py = ax + t * vx, ay + t * vy
                    dx, dy = mx_ - px, my_ - py
                    return (dx * dx + dy * dy) ** 0.5
                nearest_s = None
                best_ds = float("inf")
                for s in app.springs:
                    ds = seg_dist(s.p1.pos, s.p2.pos)
                    if ds < best_ds:
                        best_ds = ds
                        nearest_s = s
                # nearest bend
                def bend_distance(bs: BendingSpring, mouse_screen: tuple[int, int]) -> float:
                    # approximate with segments and inner arc distance using app helper
                    return app._screen_bend_distance(bs, mouse_screen)

                nearest_b = None
                best_db = float("inf")
                for bs in app.bending_springs:
                    db = bend_distance(bs, mouse_screen)
                    if db < best_db:
                        best_db = db
                        nearest_b = bs
                if not additive:
                    self.clear()
                choice = None
                if nearest_p is not None and best_dp <= particle_threshold_px:
                    choice = ("particle", best_dp, nearest_p)
                if nearest_s is not None and best_ds <= spring_threshold_px and (choice is None or best_ds < choice[1]):
                    choice = ("spring", best_ds, nearest_s)
                if nearest_b is not None and best_db <= spring_threshold_px and (choice is None or best_db < choice[1]):
                    choice = ("bend", best_db, nearest_b)
                if choice is not None:
                    kind, _, obj = choice
                    if kind == "particle":
                        if obj not in app.selected_particles:
                            app.selected_particles.append(obj)
                        obj.selected = True
                    elif kind == "spring":
                        if obj not in app.selected_springs:
                            app.selected_springs.append(obj)
                        obj.selected = True
                    elif kind == "bend":
                        if obj not in app.selected_bends:
                            app.selected_bends.append(obj)
                        obj.selected = True
            else:
                # rectangle selection in world space
                start = app.screen_to_world(self.selection_rect.topleft)
                end = app.screen_to_world(self.selection_rect.bottomright)
                world_rect = pygame.Rect(start, (end.x - start.x, end.y - start.y))
                world_rect.normalize()
                if not additive:
                    self.clear()
                for p in app.particles:
                    if world_rect.collidepoint(p.pos.x, p.pos.y):
                        if p not in app.selected_particles:
                            app.selected_particles.append(p)
                        p.selected = True
                for s in app.springs:
                    if world_rect.collidepoint(s.p1.pos.x, s.p1.pos.y) and world_rect.collidepoint(
                        s.p2.pos.x, s.p2.pos.y
                    ):
                        if s not in app.selected_springs:
                            app.selected_springs.append(s)
                        s.selected = True
                for b in app.bending_springs:
                    if (
                        world_rect.collidepoint(b.p1.pos.x, b.p1.pos.y)
                        and world_rect.collidepoint(b.p2.pos.x, b.p2.pos.y)
                        and world_rect.collidepoint(b.p3.pos.x, b.p3.pos.y)
                    ):
                        if b not in app.selected_bends:
                            app.selected_bends.append(b)
                        b.selected = True
            self.selection_rect = None
            self.selection_start = None
