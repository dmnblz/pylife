"""Hover target helpers and distance calculations for world objects."""
from __future__ import annotations

import math
import pygame

from bending_spring import BendingSpring


class HoverHelper:
    def __init__(self, app: "BuilderApp") -> None:
        self.app = app

    # distances ---------------------------------------------------------
    def screen_segment_distance(
        self, a_world: pygame.Vector2, b_world: pygame.Vector2, mouse_screen: tuple[int, int]
    ) -> float:
        a = self.app.world_to_screen(a_world)
        b = self.app.world_to_screen(b_world)
        ax, ay = a.x, a.y
        bx, by = b.x, b.y
        mx, my = float(mouse_screen[0]), float(mouse_screen[1])
        vx, vy = bx - ax, by - ay
        seg_len2 = vx * vx + vy * vy
        if seg_len2 == 0:
            dx, dy = mx - ax, my - ay
            return (dx * dx + dy * dy) ** 0.5
        t = ((mx - ax) * vx + (my - ay) * vy) / seg_len2
        t = max(0.0, min(1.0, t))
        px, py = ax + t * vx, ay + t * vy
        dx, dy = mx - px, my - py
        return (dx * dx + dy * dy) ** 0.5

    def screen_arc_distance(self, bs: BendingSpring, mouse_screen: tuple[int, int]) -> float:
        center = self.app.world_to_screen(bs.p2.pos)
        v1 = self.app.world_to_screen(bs.p1.pos) - center
        v2 = self.app.world_to_screen(bs.p3.pos) - center
        l1, l2 = v1.length(), v2.length()
        if l1 == 0 or l2 == 0:
            return float("inf")
        radius = min(l1, l2) * 0.4
        mv = pygame.Vector2(mouse_screen) - center
        dist = mv.length()
        if dist == 0:
            return float("inf")
        cross12 = -v1.cross(v2)
        angle = math.atan2(cross12, v1.dot(v2))
        cross1m = -v1.cross(mv)
        crossm2 = -mv.cross(v2)
        if angle >= 0:
            if cross1m < 0 or crossm2 < 0:
                return float("inf")
        else:
            if cross1m > 0 or crossm2 > 0:
                return float("inf")
        return abs(dist - radius)

    def screen_bend_distance(self, bs: BendingSpring, mouse_screen: tuple[int, int]) -> float:
        d1 = self.screen_segment_distance(bs.p1.pos, bs.p2.pos, mouse_screen)
        d2 = self.screen_segment_distance(bs.p2.pos, bs.p3.pos, mouse_screen)
        d_arc = self.screen_arc_distance(bs, mouse_screen)
        return min(d1, d2, d_arc)

    # hover update ------------------------------------------------------
    def update_hover_targets(self) -> None:
        app = self.app
        # default clear
        app.hover_particle = None
        app.hover_spring = None
        app.hover_bend = None
        # ignore when mouse over sidebar
        mx, my = pygame.mouse.get_pos()
        if mx >= app.screen.get_width() - app.ui.visible_width():
            return
        mouse_screen = (mx, my)

        # allowed targets per mode
        allowed: set[str]
        if app.mode == "drag":
            allowed = {"particle"}
        elif app.mode in ("spring", "vspring", "bend", "vbend"):
            allowed = {"particle"}
        elif app.mode == "sensor" and (
            app.ui.sensor_tool.await_trigger or app.ui.sensor_tool.linking_trigger
        ):
            allowed = {"particle"}
        elif app.mode == "inspect":
            if app.ui.inspect_tool.choose_trigger or app.ui.inspect_tool.linking_trigger:
                allowed = {"particle"}
            else:
                allowed = {"particle", "spring", "bend"}
        elif app.mode == "delete":
            allowed = {"particle", "spring", "bend"}
        else:
            allowed = set()

        if not allowed:
            return

        # thresholds in pixels
        particle_threshold_px = 30
        spring_threshold_px = 12

        # compute nearest particle
        nearest_p = None
        best_dp = float("inf")
        r_px = 0
        if "particle" in allowed and app.particles:
            for p in app.particles:
                ps = app.world_to_screen(p.pos)
                dp = ((ps.x - mx) ** 2 + (ps.y - my) ** 2) ** 0.5
                if dp < best_dp:
                    best_dp = dp
                    nearest_p = p
                    r_px = int((p.radius or 10) * app.camera_zoom)

        # compute nearest spring segment
        nearest_s = None
        best_ds = float("inf")
        if "spring" in allowed and app.springs:
            for s in app.springs:
                ds = self.screen_segment_distance(s.p1.pos, s.p2.pos, mouse_screen)
                if ds < best_ds:
                    best_ds = ds
                    nearest_s = s

        # compute nearest bend
        nearest_b = None
        best_db = float("inf")
        if "bend" in allowed and app.bending_springs:
            for bs in app.bending_springs:
                db = self.screen_bend_distance(bs, mouse_screen)
                if db < best_db:
                    best_db = db
                    nearest_b = bs

        # filter by thresholds
        p_ok = nearest_p is not None and best_dp <= max(particle_threshold_px, r_px + 10)
        s_ok = nearest_s is not None and best_ds <= spring_threshold_px
        b_ok = nearest_b is not None and best_db <= spring_threshold_px

        # choose one target based on smallest distance among allowed and within threshold
        choice = None
        if p_ok:
            choice = ("particle", best_dp, nearest_p)
        if s_ok and (choice is None or best_ds < choice[1]):
            choice = ("spring", best_ds, nearest_s)
        if b_ok and (choice is None or best_db < choice[1]):
            choice = ("bend", best_db, nearest_b)

        if choice is None:
            return
        kind, _, obj = choice
        if kind == "particle":
            app.hover_particle = obj  # type: ignore[assignment]
        elif kind == "spring":
            app.hover_spring = obj  # type: ignore[assignment]
        elif kind == "bend":
            app.hover_bend = obj  # type: ignore[assignment]

