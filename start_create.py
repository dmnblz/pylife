"""Interactive builder for creating and editing particles and constraints."""

import pygame
import math
from typing import Callable, Iterable

from particle import Particle
from spring import Spring
from variable_spring import VariableSpring
from variable_particle import VariableParticle
from physics import PhysicsEngine
from bending_spring import BendingSpring
from renderer import Renderer
from builder_ui.sidebar import SidebarUI
from builder_ui import theme
from builder_ui.config import (
    ParticleParams,
    SpringParams,
    VariableSpringParams,
    VariableParticleParams,
    EnvironmentParams,
)
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
        self.arms: list[HookArm] = []
        self.cycle_keys: dict[int, list[HookArm]] = {}
        self.vspring_keys: dict[int, list[VariableSpring]] = {}
        self.vparticle_keys: dict[int, list[VariableParticle]] = {}
        self.selected = None
        self.selection_start: pygame.Vector2 | None = None
        self.selection_rect: pygame.Rect | None = None
        self.selected_particles: list[Particle] = []
        self.selected_springs: list[Spring] = []
        self.spring_first = None
        self.paused = False

        # configuration dataclasses for creation
        self.mode = "drag"  # drag, particle, spring, rod
        self.particle = ParticleParams()
        self.spring = SpringParams()
        self.vspring = VariableSpringParams()
        self.vparticle = VariableParticleParams()
        self.environment = EnvironmentParams()
        self.grid_enabled = False
        self.grid_size = 40.0

        self.font = pygame.font.SysFont(None, 24)
        self.physics = PhysicsEngine(
            self.particles,
            self.springs,
            self.bending_springs,
            gravity=self.environment.gravity,
            repulsion_radius=self.environment.repulsion_radius,
            repulsion_strength=self.environment.repulsion_strength,
            temperature=self.environment.temperature,
            damping_coeff=self.environment.damping,
        )
        # Use a fixed timestep with substeps for stability across variable framerates
        self.physics.set_fixed_timestep(1.0 / FPS, substeps=2)
        self.renderer = Renderer(self.screen)
        self.ui = SidebarUI(self.screen, self)
        # camera / play area
        self.play_area = pygame.Rect(0, 0, SCREEN_SIZE[0], SCREEN_SIZE[1])
        self.camera_offset = pygame.Vector2(0, 0)
        self.camera_zoom = 1.0
        self.renderer.set_camera(self.camera_offset, self.camera_zoom)
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

    def toggle_grid(self):
        """Enable or disable the placement grid."""
        self.grid_enabled = not self.grid_enabled

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
        if self.mode in ("drag",):
            allowed = {"particle"}
        elif self.mode in ("spring", "vspring", "bend"):
            allowed = {"particle"}
        elif self.mode in ("delete", "inspect"):
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

        # compute nearest bend segment pair
        nearest_b = None
        best_db = float("inf")
        if "bend" in allowed and self.bending_springs:
            for bs in self.bending_springs:
                d1 = self._screen_segment_distance(bs.p1.pos, bs.p2.pos, mouse_screen)
                d2 = self._screen_segment_distance(bs.p2.pos, bs.p3.pos, mouse_screen)
                db = min(d1, d2)
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
        self.selected_particles.clear()
        self.selected_springs.clear()

    def remove_entities(
        self,
        particles: Iterable[Particle] = (),
        springs: Iterable[Spring] = (),
        bends: Iterable[BendingSpring] = (),
        arms: Iterable[HookArm] = (),
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

        # remove bending springs tied to removed particles or specified directly
        if parts_set or bends_set:
            self.bending_springs[:] = [
                bs
                for bs in self.bending_springs
                if bs not in bends_set
                and bs.p1 not in parts_set
                and bs.p2 not in parts_set
                and bs.p3 not in parts_set
            ]

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

    def _restore_spring(self, s: Spring):
        """Reinsert ``s`` into the simulation."""
        self.springs.append(s)
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
                }
                for p in self.particles
            ],
            "springs": self._build_springs(),
            "bending": [
                {
                    "p1": self.particles.index(bs.p1),
                    "p2": self.particles.index(bs.p2),
                    "p3": self.particles.index(bs.p3),
                    "angle": bs.rest_angle,
                    "stiff": bs.stiffness,
                }
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
            },
        }

    def _apply_state(self, data: dict) -> None:
        """Rebuild the scene from a serialised *data* structure."""
        self.particles = []
        self.variable_particles = []
        self.vparticle_keys = {}
        for pd in data.get("particles", []):
            if pd.get("type") == "variable":
                p = VariableParticle(
                    pd["pos"],
                    mass=pd.get("mass", 1.0),
                    color=tuple(pd["color"]) if pd.get("color") else None,
                    radius=pd.get("radius"),
                    base_drag=pd.get("base", 1.0),
                    alt_drag=pd.get("alt", 100.0),
                    key=pd.get("key"),
                    mode=pd.get("mode", "hold"),
                    change_speed=pd.get("speed", 240.0),
                )
                p.active = pd.get("active", False)
                p.drag = pd.get("curr", p.base_drag)
                self.variable_particles.append(p)
                self.register_variable_particle(p)
            else:
                p = Particle(
                    pd["pos"],
                    mass=pd.get("mass", 1.0),
                    color=tuple(pd["color"]) if pd.get("color") else None,
                    radius=pd.get("radius"),
                    tag=pd.get("tag"),
                    drag=pd.get("drag", 1.0),
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
        for bd in data.get("bending", []):
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
        """Handle rectangle selection of particles and springs."""
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

                if e.type == pygame.QUIT:
                    running = False
                    continue

                elif e.type == pygame.KEYDOWN:
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
                        pygame.K_s: "select",
                        pygame.K_BACKSPACE: "delete",
                        pygame.K_DELETE: "delete",
                    }
                    mode = tool_keys.get(e.key)
                    if mode:
                        self.set_mode(mode)
                    elif e.key == pygame.K_c:
                        self.choose_color()
                    elif e.key == pygame.K_z:
                        self.adjust_mass(-0.1)
                    elif e.key == pygame.K_x:
                        self.adjust_mass(0.1)
                    elif e.key == pygame.K_v:
                        self.adjust_radius(-1)
                    elif e.key == pygame.K_b:
                        self.adjust_radius(1)
                    elif e.key == pygame.K_k:
                        self.adjust_stiffness(-10)
                    elif e.key == pygame.K_l:
                        self.adjust_stiffness(10)
                    elif e.key == pygame.K_n:
                        self.adjust_temperature(-10)
                    elif e.key == pygame.K_m:
                        self.adjust_temperature(10)
                    elif e.key == pygame.K_p:
                        self.toggle_pause()
                    elif e.key == pygame.K_t:
                        # toggle theme
                        self.theme_name = "light" if theme.get_theme_name() == "dark" else "dark"
                        theme.set_theme(self.theme_name)
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
            self.renderer.draw_play_area(self.play_area, color=(70, 75, 90))
            if self.grid_enabled:
                # draw grid in world space so it zooms/pans with camera
                # fade with zoom for subtlety
                z = self.camera_zoom
                fade = max(0.15, min(1.0, (z - 0.4) / 0.8))
                def with_alpha(rgb: tuple[int, int, int], a: float) -> tuple[int, int, int, int]:
                    return (rgb[0], rgb[1], rgb[2], int(255 * max(0.0, min(1.0, a))))
                minor_rgb = (50, 52, 60)
                major_rgb = (70, 72, 82)
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
                hover_particle=self.hover_particle,
                hover_spring=self.hover_spring,
                hover_bend=self.hover_bend,
            )
            if self.selection_rect:
                pygame.draw.rect(self.screen, theme.ACCENT, self.selection_rect, width=1)
            self.ui.draw()
            # highlight first spring particle (accent)
            if self.spring_first is not None and self.mode in ("spring", "vspring"):
                c = self.world_to_screen(self.spring_first.pos)
                from builder_ui import theme as _theme
                pygame.draw.circle(self.screen, _theme.ACCENT, (int(c.x), int(c.y)), int(self.spring_first.radius * self.camera_zoom) + 6, 2)
            # HUD card (no heavy shadow)
            fps = self.clock.get_fps()
            hud_w, hud_h = 320, 72
            hud = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
            # glass panel
            pygame.draw.rect(hud, (30, 36, 48, 170), hud.get_rect(), border_radius=10)
            # inner light stroke
            pygame.draw.rect(hud, (255, 255, 255, 40), hud.get_rect().inflate(-2, -2), width=1, border_radius=8)
            # text
            stat_txt = self.font.render(
                f"{fps:5.1f} FPS  |  {len(self.particles)} P  {len(self.springs)} S",
                True,
                (220, 230, 240),
            )
            mode_txt = self.font.render(f"Mode: {self.mode}", True, (150, 200, 255))
            hud.blit(stat_txt, (12, 10))
            hud.blit(mode_txt, (12, 36))
            self.screen.blit(hud, (12, 12))
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    app = BuilderApp()
    app.run()
