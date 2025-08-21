"""Interactive builder for creating and editing particles and constraints."""

import pygame
import math
from collections import deque
from typing import Callable, Iterable

from particle import Particle
from spring import Spring
from variable_spring import VariableSpring
from variable_particle import VariableParticle
from variable_bending_spring import VariableBendingSpring
from channel import ChannelControlled
from physics import PhysicsEngine
from bending_spring import BendingSpring
from renderer import Renderer
from builder_ui.sidebar import SidebarUI
from builder_ui import theme
from builder_ui.fonts import get_font
from builder_ui.config import (
    ParticleParams,
    SpringParams,
    VariableSpringParams,
    VariableParticleParams,
    VariableBendParams,
    EnvironmentParams,
    SensorParams,
)
from sensor_particle import SensorParticle
import builder_io
from structures import create_rod as structure_create_rod
from hook_arm import HookArm

SCREEN_SIZE = (1300, 900)
FPS = 240


class BuilderApp:
    """Main application class for the particle builder demo."""
    def __init__(self):
        """Initialise pygame, state containers and helper objects."""

        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("Particle Builder")
        self.clock = pygame.time.Clock()
        self.particles: list[Particle] = []
        self.springs: list[Spring] = []
        self.variable_springs: list[VariableSpring] = []
        self.variable_particles: list[VariableParticle] = []
        self.bending_springs: list[BendingSpring] = []
        self.variable_bending_springs: list[VariableBendingSpring] = []
        self.arms: list[HookArm] = []
        self.sensors: list[SensorParticle] = []
        self.cycle_keys: dict[int, list[HookArm]] = {}
        self.vspring_keys: dict[int, list[VariableSpring]] = {}
        self.vparticle_keys: dict[int, list[VariableParticle]] = {}
        self.vbend_keys: dict[int, list[VariableBendingSpring]] = {}
        self.channels: dict[int, set[ChannelControlled]] = {}
        self.active_channels: set[int] = set()
        self.selected = None
        self.selection_start: pygame.Vector2 | None = None
        self.selection_rect: pygame.Rect | None = None
        self.selected_particles: list[Particle] = []
        self.selected_springs: list[Spring] = []
        self.selected_bends: list[BendingSpring] = []
        self.clipboard: dict[str, list] = {
            "particles": [],
            "springs": [],
            "bends": [],
            "arms": [],
        }
        self.pasting = False
        self.spring_first = None
        self.paused = False
        self.show_help = False

        # configuration dataclasses for creation
        self.mode = "drag"  # drag, particle, spring, rod
        self.particle = ParticleParams()
        self.spring = SpringParams()
        self.vspring = VariableSpringParams()
        self.vparticle = VariableParticleParams()
        self.vbend = VariableBendParams()
        self.sensor = SensorParams()
        self.environment = EnvironmentParams()
        self.grid_enabled = False
        self.grid_size = 40.0

        self.font = get_font(24)
        self.physics = PhysicsEngine(
            self.particles,
            self.springs,
            self.bending_springs,
            gravity=self.environment.gravity,
            repulsion_radius=self.environment.repulsion_radius,
            repulsion_strength=self.environment.repulsion_strength,
            temperature=self.environment.temperature,
            damping_coeff=self.environment.damping,
            integration_damping=self.environment.integration_damping,
            collisions_enabled=self.environment.collisions,
            collision_bucket_size=self.environment.collision_bucket_size,
        )
        # Use a fixed timestep with substeps for stability across variable framerates
        self.physics.set_fixed_timestep(1.0 / FPS, substeps=2)
        self.renderer = Renderer(self.screen)
        self.physics.trails_enabled = self.environment.trails_enabled
        self.renderer.set_trails_enabled(self.environment.trails_enabled)
        self.ui = SidebarUI(self.screen, self)
        # camera / play area
        self.play_area = pygame.Rect(0, 0, SCREEN_SIZE[0], SCREEN_SIZE[1])
        self.camera_offset = pygame.Vector2(0, 0)
        self.camera_zoom = 1.0
        self.renderer.set_camera(self.camera_offset, self.camera_zoom)
        self.panning = False
        # inform physics of current window size for boundary effects
        self.physics.set_screen_size(*self.screen.get_size())
        self.physics.set_play_area(self.play_area)

        # theme toggle UI state
        self.theme_name = theme.get_theme_name()

        # hover highlights
        self.hover_particle: Particle | None = None
        self.hover_spring: Spring | None = None
        self.hover_bend: BendingSpring | None = None

        # initialise undo/history and mode handlers
        self.history: list[callable] = []
        self.mode_handlers: dict[str, Callable[[pygame.event.Event], None]] = {
            "select": self.handle_select_event,
            "drag": self.handle_drag_event,
            "particle": self.handle_particle_event,
            "vparticle": self.handle_variable_particle_event,
            "spring": self.handle_spring_event,
            "vspring": self.handle_variable_spring_event,
            "delete": self.handle_delete_event,
        }

    # ------------------------------------------------------------------ camera helpers
    def screen_to_world(self, pos: tuple[float, float] | pygame.Vector2) -> pygame.Vector2:
        return self.renderer.screen_to_world(pos)

    def world_to_screen(self, pos: tuple[float, float] | pygame.Vector2) -> pygame.Vector2:
        return self.renderer.world_to_screen(pos)

    # ------------------------------------------------------------------ parameter helpers
    def set_mode(self, mode: str):
        """Switch the active builder mode and notify tools."""
        if self.mode == "circle" and mode != "circle":
            self.ui.circle_tool.cancel()
        if self.mode == "rod" and mode != "rod":
            self.ui.rod_tool.cancel()
        if self.mode == "arm" and mode != "arm":
            self.ui.arm_tool.cancel()
        if self.mode == "inspect" and mode != "inspect":
            self.ui.inspect_tool.cancel()
        if self.mode == "particle" and mode != "particle":
            self.ui.particle_tool.cancel()
        if self.mode == "spring" and mode != "spring":
            self.ui.spring_tool.cancel()
        if self.mode == "vspring" and mode != "vspring":
            self.ui.variable_spring_tool.cancel()
        if self.mode == "vparticle" and mode != "vparticle":
            self.ui.variable_particle_tool.cancel()
        if self.mode == "bend" and mode != "bend":
            self.ui.bend_tool.cancel()
        if self.mode == "vbend" and mode != "vbend":
            self.ui.variable_bend_tool.cancel()
        if self.mode == "sensor" and mode != "sensor":
            self.ui.sensor_tool.cancel()
        if self.mode == "env" and mode != "env":
            self.ui.env_tool.cancel()
        if self.mode == "grid" and mode != "grid":
            self.ui.grid_tool.cancel()

        self.mode = mode
        if mode == "circle":
            self.ui.circle_tool.start()
        if mode == "rod":
            self.ui.rod_tool.start()
        if mode == "arm":
            self.ui.arm_tool.start()
        if mode == "inspect":
            self.ui.inspect_tool.start()
        if mode == "particle":
            self.ui.particle_tool.start()
        if mode == "spring":
            self.ui.spring_tool.start()
        if mode == "vspring":
            self.ui.variable_spring_tool.start()
        if mode == "vparticle":
            self.ui.variable_particle_tool.start()
        if mode == "bend":
            self.ui.bend_tool.start()
        if mode == "vbend":
            self.ui.variable_bend_tool.start()
        if mode == "sensor":
            self.ui.sensor_tool.start()
        if mode == "env":
            self.ui.env_tool.start()
        if mode == "grid":
            self.ui.grid_tool.start()
        if mode not in ("spring", "vspring"):
            self.spring_first = None
        if self.selected and mode != "drag":
            self.selected.fixed = False
            self.selected = None

    def choose_color(self):
        """Open the color chooser and update the particle colour."""
        from color_picker import choose_color

        rgb = choose_color(self.particle.color)
        if rgb:
            self.particle.color = rgb

    def adjust_mass(self, delta: float):
        """Increment particle mass by ``delta``."""
        self.particle.mass = max(0.1, self.particle.mass + delta)

    def adjust_radius(self, delta: int):
        """Increment particle radius by ``delta`` pixels."""
        self.particle.radius = max(1, self.particle.radius + delta)

    def adjust_stiffness(self, delta: float):
        """Increment spring stiffness by ``delta``."""
        self.spring.stiffness = max(10, self.spring.stiffness + delta)

    def adjust_temperature(self, delta: float):
        """Increment environment temperature by ``delta``."""
        self.environment.temperature = max(0, self.environment.temperature + delta)
        self.physics.temperature = self.environment.temperature

    def toggle_pause(self):
        """Pause or resume the simulation."""
        self.paused = not self.paused

    def toggle_theme(self) -> None:
        """Switch between dark and light UI themes."""
        self.theme_name = (
            "light" if theme.get_theme_name() == "dark" else "dark"
        )
        theme.set_theme(self.theme_name)
        self.renderer.reset_cache()

    def toggle_grid(self):
        """Enable or disable the placement grid."""
        self.grid_enabled = not self.grid_enabled

    def toggle_help(self) -> None:
        """Flip the visibility of the help overlay."""
        self.show_help = not self.show_help

    def set_grid_size(self, value: float):
        """Set the grid spacing in pixels."""
        self.grid_size = max(5.0, value)

    def snap_to_grid(self, vec: pygame.Vector2) -> pygame.Vector2:
        """Return ``vec`` snapped to the nearest grid intersection.

        If the grid is disabled or ``vec`` already lies on a grid intersection,
        the original vector is returned unchanged.
        """

        if not self.grid_enabled:
            return vec

        x = round(vec.x / self.grid_size) * self.grid_size
        y = round(vec.y / self.grid_size) * self.grid_size

        if x == vec.x and y == vec.y:
            return vec

        return pygame.Vector2(x, y)

    # ------------------------------------------------------------------ hover helpers
    def _screen_segment_distance(self, a_world: pygame.Vector2, b_world: pygame.Vector2, mouse_screen: tuple[int, int]) -> float:
        """Return distance in pixels from mouse to segment AB rendered on screen."""
        a = self.world_to_screen(a_world)
        b = self.world_to_screen(b_world)
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

    def _screen_arc_distance(self, bs: BendingSpring, mouse_screen: tuple[int, int]) -> float:
        """Return pixel distance from mouse to the bend's angle arc."""
        center = self.world_to_screen(bs.p2.pos)
        v1 = self.world_to_screen(bs.p1.pos) - center
        v2 = self.world_to_screen(bs.p3.pos) - center
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

    def _screen_bend_distance(self, bs: BendingSpring, mouse_screen: tuple[int, int]) -> float:
        """Return minimal distance from mouse to any part of the bend."""
        d1 = self._screen_segment_distance(bs.p1.pos, bs.p2.pos, mouse_screen)
        d2 = self._screen_segment_distance(bs.p2.pos, bs.p3.pos, mouse_screen)
        d_arc = self._screen_arc_distance(bs, mouse_screen)
        return min(d1, d2, d_arc)

    def _update_hover_targets(self) -> None:
        """Update hover highlights based on current mode and mouse position."""
        # default clear
        self.hover_particle = None
        self.hover_spring = None
        self.hover_bend = None
        # ignore when mouse over sidebar
        mx, my = pygame.mouse.get_pos()
        if mx >= self.screen.get_width() - self.ui.visible_width():
            return
        mouse_screen = (mx, my)

        # allowed targets per mode
        allowed: set[str]
        if self.mode == "drag":
            allowed = {"particle"}
        elif self.mode in ("spring", "vspring", "bend", "vbend"):
            allowed = {"particle"}
        elif self.mode == "sensor" and (
            self.ui.sensor_tool.await_trigger or self.ui.sensor_tool.linking_trigger
        ):
            allowed = {"particle"}
        elif self.mode == "inspect":
            if self.ui.inspect_tool.choose_trigger or self.ui.inspect_tool.linking_trigger:
                allowed = {"particle"}
            else:
                allowed = {"particle", "spring", "bend"}
        elif self.mode == "delete":
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
        if "particle" in allowed and self.particles:
            for p in self.particles:
                ps = self.world_to_screen(p.pos)
                dp = ((ps.x - mx) ** 2 + (ps.y - my) ** 2) ** 0.5
                if dp < best_dp:
                    best_dp = dp
                    nearest_p = p
                    r_px = int((p.radius or 10) * self.camera_zoom)

        # compute nearest spring segment
        nearest_s = None
        best_ds = float("inf")
        if "spring" in allowed and self.springs:
            for s in self.springs:
                ds = self._screen_segment_distance(s.p1.pos, s.p2.pos, mouse_screen)
                if ds < best_ds:
                    best_ds = ds
                    nearest_s = s

        # compute nearest bend
        nearest_b = None
        best_db = float("inf")
        if "bend" in allowed and self.bending_springs:
            for bs in self.bending_springs:
                db = self._screen_bend_distance(bs, mouse_screen)
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
            self.hover_particle = obj  # type: ignore[assignment]
        elif kind == "spring":
            self.hover_spring = obj  # type: ignore[assignment]
        elif kind == "bend":
            self.hover_bend = obj  # type: ignore[assignment]

    def _draw_hover_tooltip(self, obj) -> None:
        """Render a small property preview beside the mouse cursor."""
        lines = self.ui.inspect_tool.get_hover_lines(obj)
        if not lines:
            return
        padding = 6
        line_h = self.font.get_linesize()
        width = max(self.font.size(t)[0] for t in lines) + padding * 2
        height = line_h * len(lines) + padding * 2
        mx, my = pygame.mouse.get_pos()
        x = mx + 12
        y = my + 12
        sw, sh = self.screen.get_size()
        sidebar_w = self.ui.visible_width()
        max_x = sw - sidebar_w - width - 5
        if x > max_x:
            x = max(mx - width - 12, 5)
        if y + height > sh - 5:
            y = sh - height - 5
        rect = pygame.Rect(x, y, width, height)
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (*theme.BG_SIDEBAR, 200), panel.get_rect(), border_radius=8)
        pygame.draw.rect(
            panel,
            (*theme.TEXT, 40),
            panel.get_rect().inflate(-2, -2),
            width=1,
            border_radius=6,
        )
        for i, line in enumerate(lines):
            txt = self.font.render(line, True, theme.TEXT)
            panel.blit(txt, (padding, padding + i * line_h))
        self.screen.blit(panel, rect)

    # ------------------------------------------------------------------ undo support
    def push_undo(self, action: Callable[[], None]):
        """Record a callable capable of undoing the last change."""
        self.history.append(action)

    def undo(self):
        """Undo the most recent change if any exist."""
        if self.history:
            self.history.pop()()

    def clear_selection(self) -> None:
        """Remove selection flags from all currently selected objects."""
        for p in self.selected_particles:
            if hasattr(p, "selected"):
                delattr(p, "selected")
        for s in self.selected_springs:
            if hasattr(s, "selected"):
                delattr(s, "selected")
        for b in self.selected_bends:
            if hasattr(b, "selected"):
                delattr(b, "selected")
        self.selected_particles.clear()
        self.selected_springs.clear()
        self.selected_bends.clear()

    def delete_selection(self) -> None:
        """Delete all currently selected particles, springs and bends."""
        if not (self.selected_particles or self.selected_springs or self.selected_bends):
            return
        particles = list(self.selected_particles)
        springs = list(self.selected_springs)
        bends = list(self.selected_bends)
        for s in self.springs:
            if (s.p1 in particles or s.p2 in particles) and s not in springs:
                springs.append(s)
        for b in self.bending_springs:
            if (b.p1 in particles or b.p2 in particles or b.p3 in particles) and b not in bends:
                bends.append(b)
        self.remove_entities(particles, springs, bends)
        self.push_undo(
            lambda parts=particles, sprs=springs, bds=bends: self._restore_entities(parts, sprs, bds)
        )
        self.clear_selection()

    def copy_selection(self) -> None:
        """Copy selected particles, springs, bends and arms to the clipboard."""
        if not (self.selected_particles or self.selected_springs or self.selected_bends):
            return
        origin_x = min(p.pos.x for p in self.selected_particles)
        origin_y = min(p.pos.y for p in self.selected_particles)
        origin = pygame.Vector2(origin_x, origin_y)
        self.clipboard = {
            "particles": [],
            "springs": [],
            "bends": [],
            "arms": [],
        }
        for p in self.selected_particles:
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
            self.clipboard["particles"].append(data)
        index = {p: i for i, p in enumerate(self.selected_particles)}
        for s in self.selected_springs:
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
            self.clipboard["springs"].append(data)
        spring_index = {s: i for i, s in enumerate(self.selected_springs)}
        for b in self.selected_bends:
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
            self.clipboard["bends"].append(data)
        for arm in self.arms:
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
                self.clipboard["arms"].append(data)

    def paste_selection(self, anchor: pygame.Vector2) -> None:
        """Paste the clipboard with its top-left anchored at *anchor*."""
        if not self.clipboard["particles"]:
            return
        new_particles: list[Particle] = []
        for pdata in self.clipboard["particles"]:
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
                    trail_length=self.environment.trail_length,
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
                    trail_length=self.environment.trail_length,
                )
            p.fixed = pdata["fixed"]
            new_particles.append(p)
        index_map = {i: p for i, p in enumerate(new_particles)}
        new_springs: list[Spring] = []
        new_bends: list[BendingSpring] = []
        new_arms: list[HookArm] = []
        for sdata in self.clipboard["springs"]:
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
        for bdata in self.clipboard["bends"]:
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
        for adata in self.clipboard["arms"]:
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
                self.cycle_keys.setdefault(arm.cycle_key, []).append(arm)
            arm._set_high_drag(False)
            new_arms.append(arm)
        self.particles.extend(new_particles)
        self.springs.extend(new_springs)
        self.bending_springs.extend(new_bends)
        self.arms.extend(new_arms)
        for p in new_particles:
            if isinstance(p, VariableParticle):
                self.variable_particles.append(p)
                self.register_variable_particle(p)
        for s in new_springs:
            if isinstance(s, VariableSpring):
                self.variable_springs.append(s)
                self.register_variable_spring(s)
        for b in new_bends:
            if isinstance(b, VariableBendingSpring):
                self.variable_bending_springs.append(b)
                self.register_variable_bend(b)
        self.clear_selection()
        for p in new_particles:
            p.selected = True
            self.selected_particles.append(p)
        for s in new_springs:
            s.selected = True
            self.selected_springs.append(s)
        for b in new_bends:
            b.selected = True
            self.selected_bends.append(b)
        self.push_undo(
            lambda parts=new_particles, sprs=new_springs, bends=new_bends, arms=new_arms: self.remove_entities(
                parts, sprs, bends, arms
            )
        )

    def draw_paste_preview(self) -> None:
        """Render a faint preview of the clipboard at the cursor."""
        if not self.pasting or not self.clipboard["particles"]:
            return
        anchor = self.screen_to_world(pygame.mouse.get_pos())
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        col = theme.ACCENT + (80,)
        for pdata in self.clipboard["particles"]:
            pos = anchor + pdata["offset"]
            c = self.world_to_screen(pos)
            r = int((pdata["radius"] or 5) * self.camera_zoom)
            pygame.draw.circle(overlay, col, (int(c.x), int(c.y)), r)
        for sdata in self.clipboard["springs"]:
            p1 = anchor + self.clipboard["particles"][sdata["p1"]]["offset"]
            p2 = anchor + self.clipboard["particles"][sdata["p2"]]["offset"]
            a = self.world_to_screen(p1)
            b = self.world_to_screen(p2)
            pygame.draw.line(overlay, col, a, b, 2)
        for bdata in self.clipboard["bends"]:
            p1 = anchor + self.clipboard["particles"][bdata["p1"]]["offset"]
            p2 = anchor + self.clipboard["particles"][bdata["p2"]]["offset"]
            p3 = anchor + self.clipboard["particles"][bdata["p3"]]["offset"]
            a = self.world_to_screen(p1)
            b = self.world_to_screen(p2)
            c = self.world_to_screen(p3)
            pygame.draw.line(overlay, col, a, b, 1)
            pygame.draw.line(overlay, col, b, c, 1)
        self.screen.blit(overlay, (0, 0))

    def draw_help_overlay(self) -> None:
        """Draw a translucent panel with common key bindings."""
        if not self.show_help:
            return
        lines = [
            "F1  - toggle this help",
            "Space - pause/resume",
            "1-0 - switch tools",
            "Ctrl+S - select tool",
            "Ctrl+C / Ctrl+V - copy/paste",
            "Delete - delete selection",
        ]
        font = get_font(20)
        line_h = font.get_linesize()
        width = max(font.size(t)[0] for t in lines) + 24
        height = line_h * len(lines) + 24
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(surf, (*theme.BG_SIDEBAR, 200), surf.get_rect(), border_radius=10)
        pygame.draw.rect(
            surf,
            (*theme.TEXT, 40),
            surf.get_rect().inflate(-2, -2),
            width=1,
            border_radius=8,
        )
        for i, line in enumerate(lines):
            txt = font.render(line, True, theme.TEXT)
            surf.blit(txt, (12, 12 + i * line_h))
        x = (self.screen.get_width() - width) // 2
        y = (self.screen.get_height() - height) // 2
        self.screen.blit(surf, (x, y))

    def remove_entities(
        self,
        particles: Iterable[Particle] = (),
        springs: Iterable[Spring] = (),
        bends: Iterable[BendingSpring] = (),
        arms: Iterable[HookArm] = (),
        sensors: Iterable[SensorParticle] = (),
    ) -> None:
        """Remove collections of objects from the simulation.

        Arms listed in ``arms`` are detached along with their particles and
        springs.  Springs, bending springs and particles referencing a particle
        slated for removal are also discarded.  Lists are mutated in place so
        external references such as the physics engine remain valid.
        """

        parts_set = set(particles)
        springs_set = set(springs)
        bends_set = set(bends)
        arms_set = set(arms)
        sensors_set = set(sensors)
        parts_set.update(sensors_set)

        # remove arms explicitly passed or those referencing removed particles
        for arm in list(self.arms):
            if arm in arms_set or any(p in parts_set for p in arm.particles):
                self._remove_arm(arm)
                parts_set.difference_update(arm.particles)
                springs_set.difference_update(arm.springs)

        # remove springs either passed explicitly or attached to removed particles
        if parts_set or springs_set:
            for s in list(self.springs):
                if s in springs_set or s.p1 in parts_set or s.p2 in parts_set:
                    self.springs.remove(s)
                    if isinstance(s, VariableSpring):
                        if s in self.variable_springs:
                            self.variable_springs.remove(s)
                        if s.key is not None and s.key in self.vspring_keys:
                            lst = self.vspring_keys[s.key]
                            if s in lst:
                                lst.remove(s)
                            if not lst:
                                del self.vspring_keys[s.key]
                        self.update_channel(s, None)

        # remove bending springs tied to removed particles or specified directly
        if parts_set or bends_set:
            new_bends = []
            for bs in self.bending_springs:
                if (
                    bs not in bends_set
                    and bs.p1 not in parts_set
                    and bs.p2 not in parts_set
                    and bs.p3 not in parts_set
                ):
                    new_bends.append(bs)
                else:
                    if isinstance(bs, VariableBendingSpring):
                        if bs in self.variable_bending_springs:
                            self.variable_bending_springs.remove(bs)
                        if bs.key is not None and bs.key in self.vbend_keys:
                            lst = self.vbend_keys[bs.key]
                            if bs in lst:
                                lst.remove(bs)
                            if not lst:
                                del self.vbend_keys[bs.key]
                        self.update_channel(bs, None)
            self.bending_springs[:] = new_bends

        if sensors_set:
            for s in list(self.sensors):
                if s in sensors_set:
                    self.sensors.remove(s)

        # finally drop particles themselves
        for p in parts_set:
            if p in self.particles:
                self.particles.remove(p)
            if isinstance(p, VariableParticle) and p in self.variable_particles:
                self.variable_particles.remove(p)
                if p.key is not None and p.key in self.vparticle_keys:
                    lst = self.vparticle_keys[p.key]
                    if p in lst:
                        lst.remove(p)
                    if not lst:
                        del self.vparticle_keys[p.key]
                self.update_channel(p, None)

    def _remove_arm(self, arm: HookArm):
        """Detach and delete ``arm`` along with its parts."""
        if arm in self.arms:
            self.arms.remove(arm)
        for key, arms in list(self.cycle_keys.items()):
            if arm in arms:
                arms.remove(arm)
                if not arms:
                    del self.cycle_keys[key]
        for s in arm.springs:
            if s in self.springs:
                self.springs.remove(s)
        for p in arm.particles:
            if p in self.particles:
                self.particles.remove(p)

    def _remove_bending(self, bend: BendingSpring) -> None:
        """Remove a single bending spring from the scene."""
        if bend in self.bending_springs:
            self.bending_springs.remove(bend)
        if bend in self.selected_bends:
            self.selected_bends.remove(bend)
        if isinstance(bend, VariableBendingSpring):
            if bend in self.variable_bending_springs:
                self.variable_bending_springs.remove(bend)
            if bend.key is not None and bend.key in self.vbend_keys:
                lst = self.vbend_keys[bend.key]
                if bend in lst:
                    lst.remove(bend)
                if not lst:
                    del self.vbend_keys[bend.key]
        self.physics.bending_springs = self.bending_springs

    def _restore_particle(self, p: Particle, springs: list[Spring]):
        """Reinsert ``p`` and associated springs."""
        self.particles.append(p)
        self.springs.extend(springs)
        for s in springs:
            if isinstance(s, VariableSpring):
                self.variable_springs.append(s)
                self.register_variable_spring(s)
        if isinstance(p, VariableParticle):
            self.variable_particles.append(p)
            self.register_variable_particle(p)
        if isinstance(p, SensorParticle):
            self.sensors.append(p)
            self.register_sensor(p)

    def _restore_spring(self, s: Spring):
        """Reinsert ``s`` into the simulation."""
        self.springs.append(s)
        if isinstance(s, VariableSpring):
            self.variable_springs.append(s)
            self.register_variable_spring(s)

    def _restore_entities(
        self,
        particles: list[Particle],
        springs: list[Spring],
        bends: list[BendingSpring] | None = None,
    ) -> None:
        """Reinsert collections of particles, springs and bends."""
        self.particles.extend(particles)
        self.springs.extend(springs)
        if bends:
            self.bending_springs.extend(bends)
            for b in bends:
                if isinstance(b, VariableBendingSpring):
                    self.variable_bending_springs.append(b)
                    self.register_variable_bend(b)
        for p in particles:
            if isinstance(p, VariableParticle):
                self.variable_particles.append(p)
                self.register_variable_particle(p)
        for s in springs:
            if isinstance(s, VariableSpring):
                self.variable_springs.append(s)
                self.register_variable_spring(s)

    # ------------------------------------------------------------------ save/load
    def save_state_dialog(self):
        """Export the current scene through a save dialog."""
        builder_io.save_state_dialog(self._build_state())

    def load_state_dialog(self):
        """Import a scene from a chosen file path."""
        data = builder_io.load_state_dialog()
        if data:
            self._apply_state(data)

    def _build_springs(self) -> list[dict]:
        """Return serialisable data for all springs."""
        data: list[dict] = []
        for s in self.springs:
            sd = {
                "p1": self.particles.index(s.p1),
                "p2": self.particles.index(s.p2),
                "rest": s.rest_length,
                "stiff": s.stiffness,
                "max": s.max_force,
                "invis": s.invisible,
            }
            if getattr(s, "channel", None) is not None:
                sd["channel"] = s.channel
            if isinstance(s, VariableSpring):
                sd.update(
                    {
                        "type": "variable",
                        "rest": s.base_rest_length,
                        "alt": s.alt_rest_length,
                        "speed": s.change_speed,
                        "key": s.key,
                        "mode": s.mode,
                        "active": s.active,
                        "curr": s.rest_length,
                    }
                )
            data.append(sd)
        return data

    def _build_state(self) -> dict:
        """Return a serialisable representation of the scene."""
        return {
            "particles": [
                {
                    "pos": [p.pos.x, p.pos.y],
                    "prev": [p.prev_pos.x, p.prev_pos.y],
                    "mass": p.mass,
                    "radius": p.radius,
                    "color": list(p.color) if p.color else None,
                    "tag": p.tag,
                    "fixed": p.fixed,
                    "drag": p.drag,
                    "channel": getattr(p, "channel", None),
                    "elasticity": getattr(p, "elasticity", 1.0),
                    **(
                        {
                            "type": "variable",
                            "base": p.base_drag,
                            "alt": p.alt_drag,
                            "speed": p.change_speed,
                            "key": p.key,
                            "mode": p.mode,
                            "active": p.active,
                            "curr": p.drag,
                        }
                        if isinstance(p, VariableParticle)
                        else {}
                      ),
                    **(
                        {
                            "type": "sensor",
                            "forward": [p.forward.x, p.forward.y],
                            "sense_radius": p.sense_radius,
                            "half_angle": p.half_angle,
                            "tags": sorted(p.tags),
                        }
                        if isinstance(p, SensorParticle)
                        else {}
                    ),
                  }
                  for p in self.particles
              ],
            "springs": self._build_springs(),
            "bending": [
                (
                    {
                        "p1": self.particles.index(bs.p1),
                        "p2": self.particles.index(bs.p2),
                        "p3": self.particles.index(bs.p3),
                        "angle": bs.rest_angle,
                        "stiff": bs.stiffness,
                    }
                    if not isinstance(bs, VariableBendingSpring)
                    else {
                        "p1": self.particles.index(bs.p1),
                        "p2": self.particles.index(bs.p2),
                        "p3": self.particles.index(bs.p3),
                        "type": "variable",
                        "angle": bs.base_angle,
                        "alt": bs.alt_angle,
                        "speed": bs.change_speed,
                        "key": bs.key,
                        "mode": bs.mode,
                        "active": bs.active,
                        "curr": bs.rest_angle,
                        "stiff": bs.stiffness,
                        "channel": bs.channel,
                    }
                )
                for bs in self.bending_springs
            ],
            "arms": [
                {
                    "particles": [self.particles.index(p) for p in arm.particles],
                    "springs": [self.springs.index(s) for s in arm.springs],
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
                for arm in self.arms
            ],
            "physics": {
                "gravity": [self.physics.gravity.x, self.physics.gravity.y],
                "repulsion_radius": self.physics.repulsion_radius,
                "repulsion_strength": self.physics.repulsion_strength,
                "temperature": self.physics.temperature,
                "damping_coeff": self.physics.damping_coeff,
                "integration_damping": self.physics.integration_damping,
                "collisions": self.physics.collisions_enabled,
                "collision_elasticity": self.physics.collision_elasticity,
                "collision_bucket_size": self.physics.collision_bucket_size or 0,
                "trails_enabled": self.environment.trails_enabled,
                "trail_length": self.environment.trail_length,
            },
        }

    def _apply_state(self, data: dict) -> None:
        """Rebuild the scene from a serialised *data* structure."""
        self.particles = []
        self.variable_particles = []
        self.vparticle_keys = {}
        self.sensors = []
        for pd in data.get("particles", []):
            if pd.get("type") == "variable":
                p = VariableParticle(
                    pd["pos"],
                    mass=pd.get("mass", 1.0),
                    color=tuple(pd["color"]) if pd.get("color") else None,
                    radius=pd.get("radius"),
                    elasticity=pd.get("elasticity", 1.0),
                    base_drag=pd.get("base", 1.0),
                    alt_drag=pd.get("alt", 100.0),
                    channel=pd.get("channel"),
                    key=pd.get("key"),
                    mode=pd.get("mode", "hold"),
                    change_speed=pd.get("speed", 240.0),
                    trail_length=self.environment.trail_length,
                )
                p.active = pd.get("active", False)
                p.drag = pd.get("curr", p.base_drag)
                self.variable_particles.append(p)
                self.register_variable_particle(p)
            elif pd.get("type") == "sensor":
                p = SensorParticle(
                    pd["pos"],
                    forward=pd.get("forward", (1, 0)),
                    sense_radius=pd.get("sense_radius", 1.0),
                    half_angle=pd.get("half_angle", math.pi),
                    tags=pd.get("tags"),
                    channel=pd.get("channel"),
                    mass=pd.get("mass", 1.0),
                    color=tuple(pd["color"]) if pd.get("color") else None,
                    radius=pd.get("radius"),
                    tag=pd.get("tag"),
                    drag=pd.get("drag", 1.0),
                    elasticity=pd.get("elasticity", 1.0),
                    trail_length=self.environment.trail_length,
                )
                self.sensors.append(p)
                self.register_sensor(p)
            else:
                p = Particle(
                    pd["pos"],
                    mass=pd.get("mass", 1.0),
                    color=tuple(pd["color"]) if pd.get("color") else None,
                    radius=pd.get("radius"),
                    tag=pd.get("tag"),
                    drag=pd.get("drag", 1.0),
                    elasticity=pd.get("elasticity", 1.0),
                    trail_length=self.environment.trail_length,
                )
            p.prev_pos = pygame.Vector2(pd.get("prev", pd["pos"]))
            p.fixed = pd.get("fixed", False)
            self.particles.append(p)

        self.springs = []
        self.variable_springs = []
        self.vspring_keys = {}
        for sd in data.get("springs", []):
            if sd.get("type") == "variable":
                s = VariableSpring(
                    self.particles[sd["p1"]],
                    self.particles[sd["p2"]],
                    sd.get("rest", 0),
                    sd.get("alt", 0),
                    sd.get("stiff", 200.0),
                    channel=sd.get("channel"),
                    key=sd.get("key"),
                    mode=sd.get("mode", "hold"),
                    change_speed=sd.get("speed", 240.0),
                    max_force=sd.get("max"),
                    invisible=sd.get("invis", False),
                )
                s.active = sd.get("active", False)
                s.rest_length = sd.get("curr", s.base_rest_length)
                self.springs.append(s)
                self.variable_springs.append(s)
                self.register_variable_spring(s)
            else:
                s = Spring(
                    self.particles[sd["p1"]],
                    self.particles[sd["p2"]],
                    sd.get("rest", 0),
                    stiffness=sd.get("stiff", 200.0),
                    max_force=sd.get("max"),
                    invisible=sd.get("invis", False),
                )
                self.springs.append(s)

        self.bending_springs = []
        self.variable_bending_springs = []
        self.vbend_keys = {}
        for bd in data.get("bending", []):
            if bd.get("type") == "variable":
                bs = VariableBendingSpring(
                    self.particles[bd["p1"]],
                    self.particles[bd["p2"]],
                    self.particles[bd["p3"]],
                    bd.get("angle", 0),
                    bd.get("alt", 0),
                    bd.get("stiff", 0),
                    channel=bd.get("channel"),
                    key=bd.get("key"),
                    mode=bd.get("mode", "hold"),
                    change_speed=bd.get("speed", math.radians(240.0)),
                )
                bs.active = bd.get("active", False)
                bs.rest_angle = bd.get("curr", bs.base_angle)
                self.bending_springs.append(bs)
                self.variable_bending_springs.append(bs)
                self.register_variable_bend(bs)
            else:
                bs = BendingSpring(
                    self.particles[bd["p1"]],
                    self.particles[bd["p2"]],
                    self.particles[bd["p3"]],
                    bd.get("angle", 0),
                    bd.get("stiff", 0),
                )
                self.bending_springs.append(bs)

        self.arms = []
        self.cycle_keys = {}
        for ad in data.get("arms", []):
            arm = HookArm.__new__(HookArm)
            arm.particles = [self.particles[i] for i in ad["particles"]]
            arm.springs = [self.springs[i] for i in ad["springs"]]
            arm.color = tuple(ad["color"])
            arm.high_drag_color = tuple(ad["high_color"])
            arm.adhesion_mass_factor = ad.get("adhesion", 10.0)
            arm.adhesion_drag = ad.get("adhesion_drag", 100.0)
            arm.cycle_speed = ad.get("cycle_speed", 240.0)
            arm.rest_lengths = ad.get("rest_lengths", [s.rest_length for s in arm.springs])
            arm.max_lengths = ad.get("max_lengths", [r * 4 for r in arm.rest_lengths])
            arm.tip = arm.particles[-1]
            arm._orig_mass = ad.get("orig_mass", arm.tip.mass)
            arm._orig_drag = ad.get("orig_drag", arm.tip.drag)
            arm.extend_held = False
            arm.contract_held = False
            arm.cycle_held = False
            arm.cycle_active = False
            arm.cycle_phase = 0
            arm.cycle_key = ad.get("cycle_key")
            if arm.cycle_key is not None:
                self.cycle_keys.setdefault(arm.cycle_key, []).append(arm)
            arm._set_high_drag(False)
            self.arms.append(arm)

        phys = data.get("physics", {})
        self.physics.gravity = pygame.Vector2(phys.get("gravity", [0, 0]))
        self.environment.gravity = self.physics.gravity
        self.physics.repulsion_radius = phys.get("repulsion_radius", 20)
        self.environment.repulsion_radius = self.physics.repulsion_radius
        self.physics.repulsion_strength = phys.get("repulsion_strength", 100)
        self.environment.repulsion_strength = self.physics.repulsion_strength
        self.physics.temperature = phys.get("temperature", 0)
        self.environment.temperature = self.physics.temperature
        self.physics.damping_coeff = phys.get("damping_coeff", 1)
        self.environment.damping = self.physics.damping_coeff
        self.physics.integration_damping = phys.get("integration_damping", 0.98)
        self.environment.integration_damping = self.physics.integration_damping
        self.physics.collisions_enabled = phys.get("collisions", True)
        self.environment.collisions = self.physics.collisions_enabled
        self.physics.collision_elasticity = phys.get("collision_elasticity", 1.0)
        self.physics.collision_bucket_size = phys.get("collision_bucket_size", 0) or None
        self.environment.collision_bucket_size = self.physics.collision_bucket_size or 0
        self.physics.trails_enabled = phys.get("trails_enabled", False)
        self.environment.trails_enabled = self.physics.trails_enabled
        self.environment.trail_length = int(phys.get("trail_length", self.environment.trail_length))
        self.renderer.set_trails_enabled(self.environment.trails_enabled)
        for p in self.particles:
            p.trail = deque(p.trail, maxlen=self.environment.trail_length)

        # refresh physics engine references so loaded objects are simulated
        self.physics.particles = self.particles
        self.physics.springs = self.springs
        self.physics.bending_springs = self.bending_springs

    # ------------------------------------------------------------------ circle creation
    def create_circle(
        self,
        center: pygame.Vector2,
        radius: float,
        segments: int,
        stiffness: float,
        add_bending: bool,
        bend_stiffness: float,
    ):
        """Spawn a ring of particles with optional bending springs."""
        center = self.snap_to_grid(center)
        particles = []
        springs = []
        for i in range(segments):
            theta = (i / segments) * 2 * math.pi
            pos = center + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
            pos = self.snap_to_grid(pos)
            p = Particle(
                pos,
                mass=self.particle.mass,
                color=self.particle.color,
                radius=self.particle.radius,
                trail_length=self.environment.trail_length,
            )
            particles.append(p)
        for i in range(segments):
            p1 = particles[i]
            p2 = particles[(i + 1) % segments]
            rest = (p2.pos - p1.pos).length()
            springs.append(Spring(p1, p2, rest_length=rest, stiffness=stiffness))
        bends = []
        if add_bending:
            for i in range(segments):
                p1 = particles[i - 1]
                p2 = particles[i]
                p3 = particles[(i + 1) % segments]
                v1 = p1.pos - p2.pos
                v2 = p3.pos - p2.pos
                if v1.length() == 0 or v2.length() == 0:
                    angle = 0.0
                else:
                    dot = max(-1.0, min(1.0, v1.normalize().dot(v2.normalize())))
                    angle = math.acos(dot)
                bends.append(BendingSpring(p1, p2, p3, angle, bend_stiffness))
            self.bending_springs.extend(bends)
        self.particles.extend(particles)
        self.springs.extend(springs)
        self.push_undo(
            lambda parts=particles, sprs=springs, bends=bends: self.remove_entities(
                parts, sprs, bends
            )
        )

    # ------------------------------------------------------------------ mode handlers
    def handle_select_event(self, event: pygame.event.Event):
        """Handle rectangle selection of particles, springs and bends."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] >= self.screen.get_width() - self.ui.visible_width():
                return
            self.selection_start = pygame.Vector2(event.pos)
            self.selection_rect = pygame.Rect(self.selection_start, (0, 0))
        elif event.type == pygame.MOUSEMOTION and self.selection_start:
            end = pygame.Vector2(event.pos)
            rect = pygame.Rect(self.selection_start, (end.x - self.selection_start.x, end.y - self.selection_start.y))
            rect.normalize()
            self.selection_rect = rect
        elif (
            event.type == pygame.MOUSEBUTTONUP
            and event.button == 1
            and self.selection_rect is not None
        ):
            start = self.screen_to_world(self.selection_rect.topleft)
            end = self.screen_to_world(self.selection_rect.bottomright)
            world_rect = pygame.Rect(start, (end.x - start.x, end.y - start.y))
            world_rect.normalize()
            self.clear_selection()
            for p in self.particles:
                if world_rect.collidepoint(p.pos.x, p.pos.y):
                    p.selected = True
                    self.selected_particles.append(p)
            for s in self.springs:
                if world_rect.collidepoint(s.p1.pos.x, s.p1.pos.y) and world_rect.collidepoint(
                    s.p2.pos.x, s.p2.pos.y
                ):
                    s.selected = True
                    self.selected_springs.append(s)
            for b in self.bending_springs:
                if (
                    world_rect.collidepoint(b.p1.pos.x, b.p1.pos.y)
                    and world_rect.collidepoint(b.p2.pos.x, b.p2.pos.y)
                    and world_rect.collidepoint(b.p3.pos.x, b.p3.pos.y)
                ):
                    b.selected = True
                    self.selected_bends.append(b)
            self.selection_rect = None
            self.selection_start = None

    def handle_drag_event(self, event: pygame.event.Event):
        """Handle interactions while in *drag* mode."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # ignore clicks on the sidebar area
            if event.pos[0] >= self.screen.get_width() - self.ui.visible_width():
                return
            mouse = self.screen_to_world(event.pos)
            if self.particles:
                self.selected = min(self.particles, key=lambda p: (p.pos - mouse).length())
                self.selected.fixed = True

    def handle_particle_event(self, event: pygame.event.Event):
        """Spawn a new particle at the clicked position."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = pygame.Vector2(event.pos)
            snap_mouse = self.snap_to_grid(mouse)
            p = Particle(
                snap_mouse,
                mass=self.particle.mass,
                color=self.particle.color,
                radius=self.particle.radius,
                trail_length=self.environment.trail_length,
            )
            self.particles.append(p)
            self.push_undo(lambda p=p: self.remove_entities([p]))

    def handle_variable_particle_event(self, event: pygame.event.Event):
        """Spawn a variable particle that can change drag via a key."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = pygame.Vector2(event.pos)
            snap_mouse = self.snap_to_grid(mouse)
            p = VariableParticle(
                snap_mouse,
                mass=self.particle.mass,
                color=self.particle.color,
                radius=self.particle.radius,
                base_drag=1.0,
                alt_drag=self.vparticle.alt_drag,
                key=self.vparticle.key,
                mode=self.vparticle.mode,
                change_speed=self.vparticle.speed,
                trail_length=self.environment.trail_length,
            )
            self.particles.append(p)
            self.variable_particles.append(p)
            self.register_variable_particle(p)
            self.push_undo(lambda p=p: self.remove_entities([p]))

    def handle_spring_event(self, event: pygame.event.Event):
        """Connect two particles with a spring or cancel with ``Escape``."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.particles:
                mouse = pygame.Vector2(event.pos)
                particle = min(
                    self.particles, key=lambda p: (p.pos - mouse).length()
                )
                if self.spring_first is None:
                    self.spring_first = particle
                else:
                    rest = (particle.pos - self.spring_first.pos).length()
                    s = Spring(
                        self.spring_first,
                        particle,
                        rest_length=rest,
                        stiffness=self.spring.stiffness,
                    )
                    self.springs.append(s)
                    self.push_undo(lambda s=s: self.remove_entities(springs=[s]))
                    self.spring_first = None
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.spring_first = None

    def handle_variable_spring_event(self, event: pygame.event.Event):
        """Connect two particles with a variable spring."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.particles:
                mouse = pygame.Vector2(event.pos)
                particle = min(self.particles, key=lambda p: (p.pos - mouse).length())
                if self.spring_first is None:
                    self.spring_first = particle
                else:
                    rest = (particle.pos - self.spring_first.pos).length()
                    alt = rest * self.vspring.alt_factor
                    s = VariableSpring(
                        self.spring_first,
                        particle,
                        rest_length=rest,
                        alt_rest_length=alt,
                        stiffness=self.vspring.stiffness,
                        key=self.vspring.key,
                        mode=self.vspring.mode,
                        change_speed=self.vspring.speed,
                    )
                    self.springs.append(s)
                    self.variable_springs.append(s)
                    self.register_variable_spring(s)
                    self.push_undo(lambda s=s: self.remove_entities(springs=[s]))
                    self.spring_first = None
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.spring_first = None

    def handle_delete_event(self, event: pygame.event.Event):
        """Remove the closest particle or spring under the cursor."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = pygame.Vector2(event.pos)
            target_p = None
            target_s = None
            dist_p = float("inf")
            dist_s = float("inf")
            if self.particles:
                target_p = min(self.particles, key=lambda p: (p.pos - mouse).length())
                dist_p = (target_p.pos - mouse).length()
            if self.springs:
                def mid_dist(s):
                    mid = (s.p1.pos + s.p2.pos) * 0.5
                    return (mid - mouse).length()
                target_s = min(self.springs, key=mid_dist)
                dist_s = mid_dist(target_s)
            if dist_p < dist_s and dist_p < 30 and target_p:
                removed = [
                    s for s in self.springs if s.p1 == target_p or s.p2 == target_p
                ]
                self.remove_entities([target_p])
                self.push_undo(
                    lambda p=target_p, ss=removed: self._restore_particle(p, ss)
                )
            elif dist_s < 30 and target_s:
                self.remove_entities(springs=[target_s])
                self.push_undo(lambda s=target_s: self._restore_spring(s))

    def register_variable_spring(self, spring: VariableSpring) -> None:
        """Register ``spring`` under its control key if any."""
        if spring.key is not None:
            self.vspring_keys.setdefault(spring.key, []).append(spring)
        self._register_channel(spring)

    def update_vspring_key(self, spring: VariableSpring, key: int | None) -> None:
        """Update the control key mapping for ``spring``."""
        old = spring.key
        if old is not None:
            lst = self.vspring_keys.get(old, [])
            if spring in lst:
                lst.remove(spring)
            if not lst and old in self.vspring_keys:
                del self.vspring_keys[old]
        spring.key = key
        if key is not None:
            self.vspring_keys.setdefault(key, []).append(spring)

    def register_variable_particle(self, part: VariableParticle) -> None:
        """Register ``part`` under its control key if any."""
        if part.key is not None:
            self.vparticle_keys.setdefault(part.key, []).append(part)
        self._register_channel(part)

    def update_vparticle_key(self, part: VariableParticle, key: int | None) -> None:
        """Update the control key mapping for ``part``."""
        old = part.key
        if old is not None:
            lst = self.vparticle_keys.get(old, [])
            if part in lst:
                lst.remove(part)
            if not lst and old in self.vparticle_keys:
                del self.vparticle_keys[old]
        part.key = key
        if key is not None:
            self.vparticle_keys.setdefault(key, []).append(part)

    def register_variable_bend(self, bend: VariableBendingSpring) -> None:
        """Register ``bend`` under its control key if any."""
        if bend.key is not None:
            self.vbend_keys.setdefault(bend.key, []).append(bend)
        self._register_channel(bend)

    def update_vbend_key(self, bend: VariableBendingSpring, key: int | None) -> None:
        """Update the control key mapping for ``bend``."""
        old = bend.key
        if old is not None:
            lst = self.vbend_keys.get(old, [])
            if bend in lst:
                lst.remove(bend)
            if not lst and old in self.vbend_keys:
                del self.vbend_keys[old]
        bend.key = key
        if key is not None:
            self.vbend_keys.setdefault(key, []).append(bend)

    # channel registration -------------------------------------------------
    def _register_channel(self, obj: ChannelControlled) -> None:
        """Add *obj* to the channel map if it has a channel."""
        ch = obj.channel
        if ch is not None:
            self.channels.setdefault(ch, set()).add(obj)

    def update_channel(self, obj: ChannelControlled, channel: int | None) -> None:
        """Move *obj* to *channel* in the channel map."""
        old = obj.channel
        if old is not None:
            objs = self.channels.get(old)
            if objs:
                objs.discard(obj)
                if not objs:
                    del self.channels[old]
        obj.channel = channel
        if channel is not None:
            self.channels.setdefault(channel, set()).add(obj)

    def register_sensor(self, sensor: SensorParticle) -> None:
        sensor.add_callback(lambda s, o: self._signal_channel(s.channel))

    def _signal_channel(self, channel: int | None) -> None:
        """Mark *channel* as active for the current frame."""
        if channel is not None:
            self.active_channels.add(channel)

    def _apply_channel_signals(self) -> None:
        """Update variable objects and clear the per-frame channel state."""
        for ch, objs in self.channels.items():
            state = ch in self.active_channels
            for obj in set(objs):
                obj.set_channel_active(state)
        self.active_channels.clear()

    def create_hook_arm(
        self,
        base: Particle,
        direction: pygame.Vector2,
        segments: int,
        spacing: float,
        mass: float,
        radius: float,
        stiffness: float,
        color,
        high_drag_color,
        adhesion_factor: float,
        cycle_key: int | None,
        cycle_speed: float,
    ):
        """Attach a new :class:`HookArm` to ``base`` and register its cycle key."""
        arm = HookArm(
            base,
            direction if direction.length() > 0 else pygame.Vector2(1, 0),
            segments=segments,
            spacing=spacing,
            stiffness=stiffness,
            color=color,
            high_drag_color=high_drag_color,
            adhesion_mass_factor=adhesion_factor,
            mass=mass,
            radius=radius,
            cycle_speed=cycle_speed,
        )
        arm.cycle_key = cycle_key
        if cycle_key is not None:
            self.cycle_keys.setdefault(cycle_key, []).append(arm)

        for p in arm.particles:
            p.pos = self.snap_to_grid(p.pos)
            p.prev_pos = p.pos.copy()
        self.arms.append(arm)
        self.particles.extend(arm.particles)
        self.springs.extend(arm.springs)
        self.push_undo(lambda arm=arm: self.remove_entities(arms=[arm]))

    def create_rod(
        self,
        center: pygame.Vector2,
        radius: float,
        length: float,
        segments: int,
        include_cytoskeleton: bool,
        include_skeleton: bool,
        skeleton_count: int,
        stiffness: float,
        add_bending: bool,
        bend_stiffness: float,
    ):
        """Create a capsule-shaped rod with optional bending springs."""
        center = self.snap_to_grid(center)
        particles, springs = structure_create_rod(
            center,
            radius=radius,
            length=length,
            segments=segments,
            stiffness=stiffness,
            max_force=None,
            color=self.particle.color,
            include_cytoskeleton=include_cytoskeleton,
            cyto_stiffness=stiffness,
            include_skeleton=include_skeleton,
            skeleton_count=skeleton_count,
            skeleton_stiffness=stiffness,
        )
        for p in particles:
            p.mass = self.particle.mass
            p.radius = self.particle.radius
            p.color = self.particle.color
            p.pos = self.snap_to_grid(p.pos)
            p.prev_pos = p.pos.copy()
        self.particles.extend(particles)
        self.springs.extend(springs)
        bends = []
        if add_bending:
            perimeter = particles[:segments]
            for i in range(len(perimeter)):
                p1 = perimeter[i - 1]
                p2 = perimeter[i]
                p3 = perimeter[(i + 1) % len(perimeter)]
                v1 = p1.pos - p2.pos
                v2 = p3.pos - p2.pos
                if v1.length() == 0 or v2.length() == 0:
                    angle = 0.0
                else:
                    dot = max(-1.0, min(1.0, v1.normalize().dot(v2.normalize())))
                    angle = math.acos(dot)
                bends.append(BendingSpring(p1, p2, p3, angle, bend_stiffness))
            self.bending_springs.extend(bends)
        self.push_undo(
            lambda parts=particles, sprs=springs, bends=bends: self.remove_entities(
                parts, sprs, bends
            )
        )

    # ------------------------------------------------------------------ main
    def run(self):
        """Main application loop."""
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000

            for e in pygame.event.get():
                # handle window resize
                if e.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                    self.renderer.screen = self.screen
                    # rebuild the sidebar UI to recompute layout against new width
                    self.ui = SidebarUI(self.screen, self)
                    # update physics boundary size
                    self.physics.set_screen_size(e.w, e.h)
                    continue
                # zoom with mouse wheel when not over sidebar
                if e.type == pygame.MOUSEWHEEL:
                    mouse_pos = pygame.mouse.get_pos()
                    # ignore zoom if over sidebar toggle/area
                    if mouse_pos[0] < self.screen.get_width() - self.ui.visible_width():
                        # zoom around mouse position
                        zoom_factor = 1.1 if e.y > 0 else 1/1.1
                        old_zoom = self.camera_zoom
                        self.camera_zoom = max(0.1, min(10.0, self.camera_zoom * zoom_factor))
                        # keep mouse position anchored in world coordinates
                        mouse_world_before = self.renderer.screen_to_world(mouse_pos)
                        self.renderer.set_camera(self.camera_offset, self.camera_zoom)
                        mouse_world_after = self.renderer.screen_to_world(mouse_pos)
                        self.camera_offset += (mouse_world_before - mouse_world_after)
                        self.renderer.set_camera(self.camera_offset, self.camera_zoom)
                        continue
                # legacy scroll buttons 4/5 -> zoom world if cursor over world; otherwise pass to UI
                if e.type == pygame.MOUSEBUTTONDOWN and e.button in (4, 5):
                    mouse_pos = e.pos
                    if mouse_pos[0] < self.screen.get_width() - self.ui.visible_width():
                        zoom_factor = 1.1 if e.button == 4 else 1/1.1
                        self.camera_zoom = max(0.1, min(10.0, self.camera_zoom * zoom_factor))
                        mouse_world_before = self.renderer.screen_to_world(mouse_pos)
                        self.renderer.set_camera(self.camera_offset, self.camera_zoom)
                        mouse_world_after = self.renderer.screen_to_world(mouse_pos)
                        self.camera_offset += (mouse_world_before - mouse_world_after)
                        self.renderer.set_camera(self.camera_offset, self.camera_zoom)
                        continue

                if self.ui.handle_event(e):
                    continue

                if self.pasting:
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        anchor = self.screen_to_world(e.pos)
                        self.paste_selection(anchor)
                        self.pasting = False
                        continue
                    if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                        self.pasting = False
                        continue

                # pan camera with right mouse drag when cursor is over world area
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                    if e.pos[0] < self.screen.get_width() - self.ui.visible_width():
                        self.panning = True
                    continue
                if e.type == pygame.MOUSEMOTION and self.panning:
                    self.camera_offset -= pygame.Vector2(e.rel) / self.camera_zoom
                    self.renderer.set_camera(self.camera_offset, self.camera_zoom)
                    continue
                if e.type == pygame.MOUSEBUTTONUP and e.button == 3 and self.panning:
                    self.panning = False
                    continue

                if e.type == pygame.QUIT:
                    running = False
                    continue

                elif e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                        if self.selected_particles or self.selected_springs or self.selected_bends:
                            self.delete_selection()
                        else:
                            self.set_mode("delete")
                    else:
                        tool_keys = {
                            pygame.K_1: "drag",
                            pygame.K_2: "particle",
                            pygame.K_3: "spring",
                            pygame.K_4: "bend",
                            pygame.K_5: "circle",
                            pygame.K_6: "rod",
                            pygame.K_7: "arm",
                            pygame.K_8: "inspect",
                            pygame.K_9: "grid",
                            pygame.K_0: "env",
                        }
                        mode = tool_keys.get(e.key)
                        mods = pygame.key.get_mods()
                        ctrl = mods & (pygame.KMOD_CTRL | pygame.KMOD_META)
                        if mode:
                            self.set_mode(mode)
                        elif ctrl and e.key == pygame.K_s:
                            self.set_mode("select")
                        elif ctrl and e.key == pygame.K_c:
                            if self.selected_particles or self.selected_springs or self.selected_bends:
                                self.copy_selection()
                        elif ctrl and e.key == pygame.K_v:
                            if self.clipboard["particles"]:
                                self.pasting = True
                        elif e.key == pygame.K_F1:
                            self.toggle_help()
                        elif e.key == pygame.K_SPACE:
                            self.toggle_pause()
                        else:
                            arms = self.cycle_keys.get(e.key, [])
                            for arm in arms:
                                arm.cycle_held = True
                            vsprings = self.vspring_keys.get(e.key, [])
                            for s in vsprings:
                                s.on_keydown()
                            vparts = self.vparticle_keys.get(e.key, [])
                            for p in vparts:
                                p.on_keydown()
                            vbends = self.vbend_keys.get(e.key, [])
                            for b in vbends:
                                b.on_keydown()

                elif e.type == pygame.KEYUP:
                    arms = self.cycle_keys.get(e.key, [])
                    for arm in arms:
                        arm.cycle_held = False
                        arm.reset_inert()
                    vsprings = self.vspring_keys.get(e.key, [])
                    for s in vsprings:
                        s.on_keyup()
                    vparts = self.vparticle_keys.get(e.key, [])
                    for p in vparts:
                        p.on_keyup()
                    vbends = self.vbend_keys.get(e.key, [])
                    for b in vbends:
                        b.on_keyup()

                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    if self.selected:
                        self.selected.fixed = False
                        self.selected = None

                handler = self.mode_handlers.get(self.mode)
                if handler:
                    # Adapt world interactions to use world coordinates inside handlers
                    handler(e)

            if self.selected:
                # move directly to mouse in world coordinates to avoid velocity injection
                mouse_world = self.screen_to_world(pygame.mouse.get_pos())
                self.selected.pos = mouse_world
                self.selected.prev_pos = self.selected.pos.copy()

            if not self.paused:
                self.physics.update(dt)
                for arm in self.arms:
                    arm.update(dt)
                for s in self.variable_springs:
                    s.update(dt)
                for p in self.variable_particles:
                    p.update(dt)
                for b in self.variable_bending_springs:
                    b.update(dt)
            for s in self.sensors:
                if s.trigger:
                    s.check(s.trigger)
            self._apply_channel_signals()

            # keep particles inside the world play area (independent of screen size)
            left, top, width, height = self.play_area
            right = left + width
            bottom = top + height
            for p in self.particles:
                if p.pos.x < left:
                    p.pos.x = left
                    p.prev_pos.x = p.pos.x
                elif p.pos.x > right:
                    p.pos.x = right
                    p.prev_pos.x = p.pos.x
                if p.pos.y < top:
                    p.pos.y = top
                    p.prev_pos.y = p.pos.y
                elif p.pos.y > bottom:
                    p.pos.y = bottom
                    p.prev_pos.y = p.pos.y

            self.renderer.draw_background(self.play_area)
            # draw play area boundary
            self.renderer.draw_play_area(self.play_area)
            if self.grid_enabled:
                # draw grid in world space so it zooms/pans with camera
                # fade with zoom for subtlety
                z = self.camera_zoom
                fade = max(0.15, min(1.0, (z - 0.4) / 0.8))

                def with_alpha(rgb: tuple[int, int, int], a: float) -> tuple[int, int, int, int]:
                    return (rgb[0], rgb[1], rgb[2], int(255 * max(0.0, min(1.0, a))))

                minor_rgb = theme.BORDER
                major_rgb = theme.BORDER_ACTIVE
                minor = with_alpha(minor_rgb, 0.35 * fade)
                major = with_alpha(major_rgb, 0.6 * fade)
                grid_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                left = self.play_area.left
                right = self.play_area.right
                top = self.play_area.top
                bottom = self.play_area.bottom
                step = max(5.0, self.grid_size)
                # vertical lines
                x = left - (left % step)
                while x <= right:
                    p1 = self.renderer.world_to_screen((x, top))
                    p2 = self.renderer.world_to_screen((x, bottom))
                    n = round(x / step)
                    color = major if n % 5 == 0 else minor
                    pygame.draw.line(grid_surf, color, p1, p2)
                    x += step
                # horizontal lines
                y = top - (top % step)
                while y <= bottom:
                    p1 = self.renderer.world_to_screen((left, y))
                    p2 = self.renderer.world_to_screen((right, y))
                    n = round(y / step)
                    color = major if n % 5 == 0 else minor
                    pygame.draw.line(grid_surf, color, p1, p2)
                    y += step
                self.screen.blit(grid_surf, (0, 0))
            # update hover highlights each frame
            self._update_hover_targets()
            self.renderer.draw(
                self.particles,
                self.springs,
                self.bending_springs,
                self.sensors,
                hover_particle=self.hover_particle,
                hover_spring=self.hover_spring,
                hover_bend=self.hover_bend,
            )
            link = self.ui.sensor_tool.linking_trigger or self.ui.inspect_tool.linking_trigger
            if link is not None:
                start = self.world_to_screen(link.pos)
                pygame.draw.line(
                    self.screen,
                    theme.ACCENT,
                    start,
                    pygame.mouse.get_pos(),
                    2,
                )
            self.draw_paste_preview()
            if self.selection_rect:
                pygame.draw.rect(self.screen, theme.ACCENT, self.selection_rect, width=1)
            if self.mode == "inspect":
                obj = self.hover_particle or self.hover_spring or self.hover_bend
                if obj:
                    self._draw_hover_tooltip(obj)
            self.ui.draw()
            # highlight first spring particle (accent)
            if self.spring_first is not None and self.mode in ("spring", "vspring"):
                c = self.world_to_screen(self.spring_first.pos)
                from builder_ui import theme as _theme
                pygame.draw.circle(self.screen, _theme.ACCENT, (int(c.x), int(c.y)), int(self.spring_first.radius * self.camera_zoom) + 6, 2)
            # HUD card (no heavy shadow)
            fps = self.clock.get_fps()
            energy = self.physics.total_energy()
            hud_w, hud_h = 320, 96
            hud = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
            # glass panel
            pygame.draw.rect(
                hud,
                (*theme.BG_SIDEBAR, 150),
                hud.get_rect(),
                border_radius=10,
            )
            # inner light stroke
            pygame.draw.rect(
                hud,
                (*theme.TEXT, 40),
                hud.get_rect().inflate(-2, -2),
                width=1,
                border_radius=8,
            )
            # text
            stat_txt = self.font.render(
                f"{fps:5.1f} FPS  |  {len(self.particles)} P  {len(self.springs)} S",
                True,
                theme.TEXT,
            )
            energy_txt = self.font.render(f"Energy: {energy:.2E}", True, theme.TEXT)
            mode_txt = self.font.render(f"Mode: {self.mode}", True, theme.ACCENT)
            hud.blit(stat_txt, (12, 10))
            hud.blit(energy_txt, (12, 36))
            hud.blit(mode_txt, (12, 62))
            self.screen.blit(hud, (12, 12))
            self.draw_help_overlay()
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    app = BuilderApp()
    app.run()
