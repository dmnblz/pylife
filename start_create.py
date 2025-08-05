import pygame
import math
from typing import Callable, Iterable

from particle import Particle
from spring import Spring
from variable_spring import VariableSpring
from variable_particle import VariableParticle
from bending_spring import BendingSpring
from renderer import Renderer
from builder_ui.sidebar import SidebarUI
from builder_ui.config import (
    ParticleParams,
    SpringParams,
    VariableSpringParams,
    VariableParticleParams,
    EnvironmentParams,
)
import builder_io
from builder_core import SceneBuilder

SCREEN_SIZE = (1300, 900)
FPS = 120


class BuilderApp(SceneBuilder):
    """Main application class for the particle builder demo."""

    def __init__(self):
        """Initialise pygame, state containers and helper objects."""

        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("Particle Builder")
        self.clock = pygame.time.Clock()

        # core scene state shared with the CLI
        SceneBuilder.__init__(self)

        self.selected = None
        self.spring_first = None

        # configuration dataclasses for creation
        self.mode = "drag"  # drag, particle, spring, rod
        self.particle = ParticleParams()
        self.spring = SpringParams()
        self.vspring = VariableSpringParams()
        self.vparticle = VariableParticleParams()
        self.environment = EnvironmentParams()
        # sync environment values with the physics engine
        self.set_gravity(*self.environment.gravity)
        self.set_repulsion(
            self.environment.repulsion_radius, self.environment.repulsion_strength
        )
        self.set_temperature(self.environment.temperature)
        self.set_damping(self.environment.damping)

        self.font = pygame.font.SysFont(None, 24)
        self.renderer = Renderer(self.screen)
        self.ui = SidebarUI(self.screen, self)
        self.mode_handlers: dict[str, Callable[[pygame.event.Event], None]] = {
            "drag": self.handle_drag_event,
            "particle": self.handle_particle_event,
            "vparticle": self.handle_variable_particle_event,
            "spring": self.handle_spring_event,
            "vspring": self.handle_variable_spring_event,
            "delete": self.handle_delete_event,
        }

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
    # ------------------------------------------------------------------ save/load
    def save_state_dialog(self):
        """Export the current scene through a save dialog."""
        builder_io.save_state_dialog(self.build_state())

    def load_state_dialog(self):
        """Import a scene from a chosen file path."""
        data = builder_io.load_state_dialog()
        if data:
            self.apply_state(data)

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
        """Delegate to :class:`SceneBuilder`'s implementation."""
        super().create_hook_arm(
            base,
            direction,
            segments,
            spacing,
            mass,
            radius,
            stiffness,
            color,
            high_drag_color,
            adhesion_factor,
            cycle_key,
            cycle_speed,
        )

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
        """Delegate rod creation to :class:`SceneBuilder`."""
        super().create_rod(
            center,
            radius,
            length,
            segments,
            include_cytoskeleton,
            include_skeleton,
            skeleton_count,
            stiffness,
            add_bending,
            bend_stiffness,
            mass=self.particle.mass,
            color=self.particle.color,
            particle_radius=self.particle.radius,
        )

    # ------------------------------------------------------------------ main
    def run(self):
        """Main application loop."""
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
                    handler(e)

            if self.selected:
                self.selected.pos = pygame.Vector2(pygame.mouse.get_pos())
                self.selected.prev_pos = self.selected.pos.copy()

            if not self.paused:
                  self.physics.update(dt)
                  for arm in self.arms:
                      arm.update(dt)
                  for s in self.variable_springs:
                      s.update(dt)
                  for p in self.variable_particles:
                      p.update(dt)

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
            if self.spring_first is not None and self.mode in ("spring", "vspring"):
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
