import pygame
import math
from typing import Callable

from particle import Particle
from spring import Spring
from physics import PhysicsEngine
from bending_spring import BendingSpring
from renderer import Renderer
from builder_ui.sidebar import SidebarUI
from builder_ui.config import (
    ParticleParams,
    SpringParams,
    EnvironmentParams,
)
import builder_io
from structures import create_rod as structure_create_rod
from hook_arm import HookArm

SCREEN_SIZE = (1300, 900)
FPS = 120


class BuilderApp:
    """Main application class for the particle builder demo."""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("Particle Builder")
        self.clock = pygame.time.Clock()
        self.particles: list[Particle] = []
        self.springs: list[Spring] = []
        self.bending_springs: list[BendingSpring] = []
        self.arms: list[HookArm] = []
        self.cycle_keys: dict[int, list[HookArm]] = {}
        self.selected = None
        self.spring_first = None
        self.paused = False

        # configuration dataclasses for creation
        self.mode = "drag"  # drag, particle, spring, rod
        self.particle = ParticleParams()
        self.spring = SpringParams()
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
        self.renderer = Renderer(self.screen)
        self.ui = SidebarUI(self.screen, self)
        self.history: list[callable] = []
        self.mode_handlers: dict[str, Callable[[pygame.event.Event], None]] = {
            "drag": self.handle_drag_event,
            "particle": self.handle_particle_event,
            "spring": self.handle_spring_event,
            "delete": self.handle_delete_event,
        }

    # ------------------------------------------------------------------ parameter helpers
    def set_mode(self, mode: str):
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
        if mode == "bend":
            self.ui.bend_tool.start()
        if mode == "env":
            self.ui.env_tool.start()
        if mode == "grid":
            self.ui.grid_tool.start()
        if mode != "spring":
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
        self.particle.mass = max(0.1, self.particle.mass + delta)

    def adjust_radius(self, delta: int):
        self.particle.radius = max(1, self.particle.radius + delta)

    def adjust_stiffness(self, delta: float):
        self.spring.stiffness = max(10, self.spring.stiffness + delta)

    def adjust_temperature(self, delta: float):
        self.environment.temperature = max(0, self.environment.temperature + delta)
        self.physics.temperature = self.environment.temperature

    def toggle_pause(self):
        self.paused = not self.paused

    def toggle_grid(self):
        """Enable or disable the placement grid."""
        self.grid_enabled = not self.grid_enabled

    def set_grid_size(self, value: float):
        """Set the grid spacing in pixels."""
        self.grid_size = max(5.0, value)

    def snap_to_grid(self, vec: pygame.Vector2) -> pygame.Vector2:
        """Return ``vec`` snapped to the nearest grid intersection."""
        if not self.grid_enabled:
            return vec
        x = round(vec.x / self.grid_size) * self.grid_size
        y = round(vec.y / self.grid_size) * self.grid_size
        return pygame.Vector2(x, y)

    # ------------------------------------------------------------------ undo support
    def push_undo(self, action: Callable[[], None]):
        """Record a callable capable of undoing the last change."""
        self.history.append(action)

    def undo(self):
        """Undo the most recent change if any exist."""
        if self.history:
            self.history.pop()()

    def _remove_particle(self, p: Particle):
        """Remove ``p`` and any constraints or arms using it."""
        if p in self.particles:
            self.particles.remove(p)
        self.springs = [s for s in self.springs if s.p1 != p and s.p2 != p]
        self.bending_springs = [
            bs for bs in self.bending_springs if p not in (bs.p1, bs.p2, bs.p3)
        ]
        for arm in list(self.arms):
            if p in arm.particles:
                self._remove_arm(arm)

    def _remove_spring(self, s: Spring):
        """Remove ``s`` from the simulation."""
        if s in self.springs:
            self.springs.remove(s)

    def _remove_bending(self, bs: BendingSpring):
        """Remove a bending spring from the simulation."""
        if bs in self.bending_springs:
            self.bending_springs.remove(bs)

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

    def _restore_spring(self, s: Spring):
        """Reinsert ``s`` into the simulation."""
        self.springs.append(s)

    def _remove_group(
        self,
        particles: list[Particle],
        springs: list[Spring],
        bends: list[BendingSpring],
        arms: list[HookArm] | None = None,
    ):
        """Remove batches of objects from the simulation."""
        arms = arms or []
        for arm in arms:
            self._remove_arm(arm)
        for bs in bends:
            self._remove_bending(bs)
        for s in springs:
            self._remove_spring(s)
        for p in particles:
            self._remove_particle(p)

    # ------------------------------------------------------------------ save/load
    def save_state_dialog(self):
        """Export the current scene through a save dialog."""
        builder_io.save_state_dialog(self._build_state())

    def load_state_dialog(self):
        """Import a scene from a chosen file path."""
        data = builder_io.load_state_dialog()
        if data:
            self._apply_state(data)

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
                }
                for p in self.particles
            ],
            "springs": [
                {
                    "p1": self.particles.index(s.p1),
                    "p2": self.particles.index(s.p2),
                    "rest": s.rest_length,
                    "stiff": s.stiffness,
                    "max": s.max_force,
                    "invis": s.invisible,
                }
                for s in self.springs
            ],
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
        for pd in data.get("particles", []):
            p = Particle(
                pd["pos"],
                mass=pd.get("mass", 1.0),
                color=tuple(pd["color"]) if pd.get("color") else None,
                radius=pd.get("radius"),
                tag=pd.get("tag"),
            )
            p.prev_pos = pygame.Vector2(pd.get("prev", pd["pos"]))
            p.fixed = pd.get("fixed", False)
            self.particles.append(p)

        self.springs = []
        for sd in data.get("springs", []):
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
            arm.cycle_speed = ad.get("cycle_speed", 240.0)
            arm.rest_lengths = ad.get("rest_lengths", [s.rest_length for s in arm.springs])
            arm.max_lengths = ad.get("max_lengths", [r * 4 for r in arm.rest_lengths])
            arm.tip = arm.particles[-1]
            arm._orig_mass = ad.get("orig_mass", arm.tip.mass)
            arm.extend_held = False
            arm.contract_held = False
            arm.cycle_held = False
            arm.cycle_active = False
            arm.cycle_phase = 0
            arm.cycle_key = ad.get("cycle_key")
            if arm.cycle_key is not None:
                self.cycle_keys.setdefault(arm.cycle_key, []).append(arm)
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
            lambda parts=particles, sprs=springs, bends=bends: self._remove_group(parts, sprs, bends)
        )

    # ------------------------------------------------------------------ mode handlers
    def handle_drag_event(self, event: pygame.event.Event):
        """Handle interactions while in *drag* mode."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse = pygame.Vector2(event.pos)
            if self.particles:
                self.selected = min(
                    self.particles, key=lambda p: (p.pos - mouse).length()
                )
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
            self.push_undo(lambda p=p: self._remove_particle(p))

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
                    self.push_undo(lambda s=s: self._remove_spring(s))
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
                self.particles.remove(target_p)
                self.springs = [s for s in self.springs if s not in removed]
                self.push_undo(
                    lambda p=target_p, ss=removed: self._restore_particle(p, ss)
                )
            elif dist_s < 30 and target_s:
                self.springs.remove(target_s)
                self.push_undo(lambda s=target_s: self._restore_spring(s))

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
        if self.grid_enabled:
            for p in arm.particles:
                p.pos = self.snap_to_grid(p.pos)
                p.prev_pos = p.pos.copy()
        self.arms.append(arm)
        self.particles.extend(arm.particles)
        self.springs.extend(arm.springs)
        self.push_undo(lambda arm=arm: self._remove_arm(arm))

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
            lambda parts=particles, sprs=springs, bends=bends: self._remove_group(parts, sprs, bends)
        )

    # ------------------------------------------------------------------ main
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000

            for e in pygame.event.get():
                if self.ui.handle_event(e):
                    continue

                if e.type == pygame.QUIT:
                    running = False
                    continue

                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_1:
                        self.set_mode("drag")
                    elif e.key == pygame.K_2:
                        self.set_mode("particle")
                    elif e.key == pygame.K_3:
                        self.set_mode("spring")
                    elif e.key == pygame.K_9:
                        self.set_mode("bend")
                    elif e.key == pygame.K_4:
                        self.set_mode("delete")
                    elif e.key == pygame.K_5:
                        self.set_mode("rod")
                    elif e.key == pygame.K_6:
                        self.set_mode("arm")
                    elif e.key == pygame.K_7:
                        self.set_mode("inspect")
                    elif e.key == pygame.K_8:
                        self.set_mode("env")
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
                    else:
                        arms = self.cycle_keys.get(e.key, [])
                        for arm in arms:
                            arm.cycle_held = True

                elif e.type == pygame.KEYUP:
                    arms = self.cycle_keys.get(e.key, [])
                    for arm in arms:
                        arm.cycle_held = False
                        arm.reset_inert()

                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    if self.selected:
                        self.selected.fixed = False
                        self.selected = None

                handler = self.mode_handlers.get(self.mode)
                if handler:
                    handler(e)

            if self.selected:
                self.selected.pos = pygame.Vector2(pygame.mouse.get_pos())
                self.selected.prev_pos = self.selected.pos.copy()

            if not self.paused:
                self.physics.update(dt)
                for arm in self.arms:
                    arm.update(dt)

            # keep particles inside the window and out of the sidebar
            max_x = self.screen.get_width() - self.ui.visible_width()
            max_y = self.screen.get_height()
            for p in self.particles:
                if p.pos.x < 0:
                    p.pos.x = 0
                    p.prev_pos.x = p.pos.x
                elif p.pos.x > max_x:
                    p.pos.x = max_x
                    p.prev_pos.x = p.pos.x
                if p.pos.y < 0:
                    p.pos.y = 0
                    p.prev_pos.y = p.pos.y
                elif p.pos.y > max_y:
                    p.pos.y = max_y
                    p.prev_pos.y = p.pos.y

            self.screen.fill((30, 30, 30))
            if self.grid_enabled:
                max_x = self.screen.get_width() - self.ui.visible_width()
                max_y = self.screen.get_height()
                for gx in range(0, int(max_x) + 1, int(self.grid_size)):
                    pygame.draw.line(self.screen, (60, 60, 60), (gx, 0), (gx, max_y))
                for gy in range(0, int(max_y) + 1, int(self.grid_size)):
                    pygame.draw.line(self.screen, (60, 60, 60), (0, gy), (max_x, gy))
            self.renderer.draw(self.particles, self.springs, self.bending_springs)
            self.ui.draw()
            # highlight first spring particle
            if self.spring_first is not None and self.mode == "spring":
                pygame.draw.circle(
                    self.screen,
                    (255, 255, 0),
                    (int(self.spring_first.pos.x), int(self.spring_first.pos.y)),
                    self.spring_first.radius + 4,
                    2,
                )
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    app = BuilderApp()
    app.run()
