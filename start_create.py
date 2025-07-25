import pygame

from particle import Particle
from spring import Spring
from physics import PhysicsEngine
from renderer import Renderer
from builder_ui import SidebarUI

SCREEN_SIZE = (1300, 900)
FPS = 120


class BuilderApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("Particle Builder")
        self.clock = pygame.time.Clock()
        self.particles: list[Particle] = []
        self.springs: list[Spring] = []
        self.selected = None
        self.spring_first = None
        self.paused = False

        # parameters for creation
        self.mode = "drag"  # drag, particle, spring
        self.mass = 1.0
        self.radius = 10
        self.color_cycle = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 255),
            (255, 255, 0),
            (0, 255, 255),
        ]
        self.color_index = 0
        self.color = self.color_cycle[self.color_index]
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
        self.mode = mode
        if mode != "spring":
            self.spring_first = None
        if self.selected and mode != "drag":
            self.selected.fixed = False
            self.selected = None

    def cycle_color(self):
        self.color_index = (self.color_index + 1) % len(self.color_cycle)
        self.color = self.color_cycle[self.color_index]

    def adjust_mass(self, delta: float):
        self.mass = max(0.1, self.mass + delta)

    def adjust_radius(self, delta: int):
        self.radius = max(1, self.radius + delta)

    def adjust_stiffness(self, delta: float):
        self.stiffness = max(10, self.stiffness + delta)

    def adjust_temperature(self, delta: float):
        self.physics.temperature = max(0, self.physics.temperature + delta)

    def toggle_pause(self):
        self.paused = not self.paused

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
                    elif e.key == pygame.K_c:
                        self.cycle_color()
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

                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    if self.selected:
                        self.selected.fixed = False
                        self.selected = None

            if self.selected:
                self.selected.pos = pygame.Vector2(pygame.mouse.get_pos())
                self.selected.prev_pos = self.selected.pos.copy()

            if not self.paused:
                self.physics.update(dt)

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
