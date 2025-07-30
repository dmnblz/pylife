import pygame
import math

from particle import Particle
from spring import Spring
from physics import PhysicsEngine
from renderer import Renderer
from builder_ui import SidebarUI
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
        self.arms: list[HookArm] = []
        self.cycle_keys: dict[int, HookArm] = {}
        self.selected = None
        self.spring_first = None
        self.paused = False

        # parameters for creation
        self.mode = "drag"  # drag, particle, spring, rod
        self.mass = 1.0
        self.radius = 10
        self.color = (255, 0, 0)
        self.stiffness = 200.0

        self.font = pygame.font.SysFont(None, 24)
        self.physics = PhysicsEngine(
            self.particles,
            self.springs,
            gravity=(0, 0),
            repulsion_radius=30,
            repulsion_strength=1000,
            temperature=0,
            damping_coeff=1,
        )
        self.renderer = Renderer(self.screen)
        self.ui = SidebarUI(self.screen, self)

    # ------------------------------------------------------------------ parameter helpers
    def set_mode(self, mode: str):
        if self.mode == "circle" and mode != "circle":
            self.ui.circle_tool.cancel()
        if self.mode == "rod" and mode != "rod":
            self.ui.rod_tool.cancel()
        if self.mode == "arm" and mode != "arm":
            self.ui.arm_tool.cancel()

        self.mode = mode
        if mode == "circle":
            self.ui.circle_tool.start()
        if mode == "rod":
            self.ui.rod_tool.start()
        if mode == "arm":
            self.ui.arm_tool.start()
        if mode != "spring":
            self.spring_first = None
        if self.selected and mode != "drag":
            self.selected.fixed = False
            self.selected = None

    def choose_color(self):
        """Open the color chooser in a separate process and update the color."""
        from color_picker import choose_color

        rgb = choose_color(self.color)
        if rgb:
            self.color = rgb

    def set_color(self, color):
        self.color = color

    def get_color_hex(self) -> str:
        r, g, b = self.color
        return f"#{r:02X}{g:02X}{b:02X}"

    def set_color_hex(self, value: str):
        value = value.lstrip("#")
        if len(value) != 6:
            return
        try:
            r = int(value[0:2], 16)
            g = int(value[2:4], 16)
            b = int(value[4:6], 16)
            self.color = (r, g, b)
        except ValueError:
            pass

    def adjust_mass(self, delta: float):
        self.mass = max(0.1, self.mass + delta)

    def set_mass(self, value: float):
        self.mass = max(0.1, value)

    def adjust_radius(self, delta: int):
        self.radius = max(1, self.radius + delta)

    def set_radius(self, value: float):
        self.radius = max(1, int(value))

    def adjust_stiffness(self, delta: float):
        self.stiffness = max(10, self.stiffness + delta)

    def set_stiffness(self, value: float):
        self.stiffness = max(10, value)

    def adjust_temperature(self, delta: float):
        self.physics.temperature = max(0, self.physics.temperature + delta)

    def set_temperature(self, value: float):
        self.physics.temperature = max(0, value)

    def toggle_pause(self):
        self.paused = not self.paused

    # ------------------------------------------------------------------ circle creation
    def create_circle(self, center: pygame.Vector2, radius: float, segments: int):
        particles = []
        springs = []
        for i in range(segments):
            theta = (i / segments) * 2 * math.pi
            pos = center + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
            p = Particle(pos, mass=self.mass, color=self.color, radius=self.radius)
            particles.append(p)
        for i in range(segments):
            p1 = particles[i]
            p2 = particles[(i + 1) % segments]
            rest = (p2.pos - p1.pos).length()
            springs.append(Spring(p1, p2, rest_length=rest, stiffness=self.stiffness))
        self.particles.extend(particles)
        self.springs.extend(springs)

    def create_hook_arm(
        self,
        base: Particle,
        direction: pygame.Vector2,
        segments: int,
        spacing: float,
        cycle_key: int | None,
    ):
        """Attach a new :class:`HookArm` to ``base`` and register its cycle key."""
        arm = HookArm(
            base,
            direction if direction.length() > 0 else pygame.Vector2(1, 0),
            segments=segments,
            spacing=spacing,
            stiffness=self.stiffness,
            color=self.color,
        )
        arm.cycle_key = cycle_key
        if cycle_key is not None:
            self.cycle_keys[cycle_key] = arm
        self.arms.append(arm)
        self.particles.extend(arm.particles)
        self.springs.extend(arm.springs)

    def create_rod(
        self,
        center: pygame.Vector2,
        radius: float,
        length: float,
        segments: int,
        include_cytoskeleton: bool,
        include_skeleton: bool,
        skeleton_count: int,
    ):
        particles, springs = structure_create_rod(
            center,
            radius=radius,
            length=length,
            segments=segments,
            stiffness=self.stiffness,
            max_force=None,
            color=self.color,
            include_cytoskeleton=include_cytoskeleton,
            cyto_stiffness=self.stiffness,
            include_skeleton=include_skeleton,
            skeleton_count=skeleton_count,
            skeleton_stiffness=self.stiffness,
        )
        for p in particles:
            p.mass = self.mass
            p.radius = self.radius
            p.color = self.color
        self.particles.extend(particles)
        self.springs.extend(springs)

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

                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_1:
                        self.set_mode("drag")
                    elif e.key == pygame.K_2:
                        self.set_mode("particle")
                    elif e.key == pygame.K_3:
                        self.set_mode("spring")
                    elif e.key == pygame.K_4:
                        self.set_mode("delete")
                    elif e.key == pygame.K_5:
                        self.set_mode("rod")
                    elif e.key == pygame.K_6:
                        self.set_mode("arm")
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
                    elif e.key == pygame.K_ESCAPE:
                        self.spring_first = None
                    else:
                        arm = self.cycle_keys.get(e.key)
                        if arm:
                            arm.cycle_held = True

                elif e.type == pygame.KEYUP:
                    arm = self.cycle_keys.get(e.key)
                    if arm:
                        arm.cycle_held = False
                        arm.reset_inert()

                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    mouse = pygame.Vector2(e.pos)
                    if self.mode == "drag":
                        if self.particles:
                            self.selected = min(
                                self.particles, key=lambda p: (p.pos - mouse).length()
                            )
                            self.selected.fixed = True
                    elif self.mode == "particle":
                        p = Particle(mouse, mass=self.mass, color=self.color, radius=self.radius)
                        self.particles.append(p)
                    elif self.mode == "spring":
                        if self.particles:
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
                                    stiffness=self.stiffness,
                                )
                                self.springs.append(s)
                                self.spring_first = None
                    elif self.mode == "delete":
                        # remove closest particle or spring
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
                            self.particles.remove(target_p)
                            self.springs = [s for s in self.springs if s.p1 != target_p and s.p2 != target_p]
                        elif dist_s < 30 and target_s:
                            self.springs.remove(target_s)
                    elif self.mode == "rod":
                        pass  # handled by rod tool
                    elif self.mode == "arm":
                        pass  # handled by arm tool

                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    if self.selected:
                        self.selected.fixed = False
                        self.selected = None

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
            self.renderer.draw(self.particles, self.springs)
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
