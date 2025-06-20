import math
import random
import pygame

from particle import Particle
from physics import PhysicsEngine
from renderer import Renderer
from spring import Spring
from structures import create_rod

SCREEN_SIZE = (1300, 900)
FPS = 120

def get_gradient_color(t):
    """Return an RGB color from a smooth HSV gradient for t in [0, 1]."""
    # HSV to RGB conversion
    i = int(t * 6)
    f = t * 6 - i
    q = 1 - f
    if i % 6 == 0:
        r, g, b = 1, f, 0
    elif i % 6 == 1:
        r, g, b = q, 1, 0
    elif i % 6 == 2:
        r, g, b = 0, 1, f
    elif i % 6 == 3:
        r, g, b = 0, q, 1
    elif i % 6 == 4:
        r, g, b = f, 0, 1
    elif i % 6 == 5:
        r, g, b = 1, 0, q
    return (int(r * 255), int(g * 255), int(b * 255))

class CellWallApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        self.particles = []
        self.springs = []
        self.selected = None

        center = pygame.Vector2(SCREEN_SIZE) / 2
        rod_radius = 60
        rod_length = 200
        rod_segments = 50
        rod_distance = 300

        rods = []
        # North
        loc_north = center - pygame.Vector2((0, rod_distance))
        rods.append(('rod_north', loc_north))
        # East
        loc_east = center + pygame.Vector2((rod_distance, 0))
        rods.append(('rod_east', loc_east))
        # South
        loc_south = center + pygame.Vector2((0, rod_distance))
        rods.append(('rod_south', loc_south))
        # West
        loc_west = center - pygame.Vector2((rod_distance, 0))
        rods.append(('rod_west', loc_west))

        for idx, (tag, loc) in enumerate(rods):
            particles, springs = create_rod(
                loc, radius=rod_radius, length=rod_length, segments=rod_segments,
                tag=tag, stiffness=2500, max_force=50000,
                include_cytoskeleton=False, include_skeleton=True,
                skeleton_count=5, skeleton_stiffness=1000,
                color=(255, 255, 255)  # placeholder, will override below
            )
            # Apply gradient color along the rod
            n = len(particles)
            for i, p in enumerate(particles):
                t = i / max(n - 1, 1)
                p.color = get_gradient_color(t)
            self.particles.extend(particles)
            self.springs.extend(springs)

        self.physics = PhysicsEngine(
            self.particles, self.springs, gravity=(0, 0),
            repulsion_radius=30, repulsion_strength=10000,
            temperature=500, damping_coeff=1
        )

        self.renderer = Renderer(self.screen)
        self.clamp_to_window = True
        self.bouncy_clamp = False
        self.periodic_boundary = False

    def _loose_particles(self, count=20):
        center = pygame.Vector2(SCREEN_SIZE) / 2
        radius = 100 * 0.9
        for i in range(count):
            theta = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, radius)
            pos = center + pygame.Vector2(math.cos(theta), math.sin(theta)) * r
            p = Particle(pos, mass=0.1, color=(0, 255, 0), radius=5)
            p.tag = "loose"
            self.particles.append(p)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    mouse = pygame.Vector2(e.pos)
                    self.selected = min(self.particles, key=lambda p: (p.pos - mouse).length())
                    self.selected.fixed = True
                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    if self.selected:
                        self.selected.fixed = False
                    self.selected = None
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_o:
                    mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
                    p = Particle(mouse_pos, mass=0.1, color=(0, 255, 0), radius=5)
                    p.tag = "loose"
                    self.particles.append(p)
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_p:
                    mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
                    for _ in range(10):
                        p = Particle(mouse_pos, mass=0.1, color=(0, 255, 0), radius=5)
                        p.tag = "loose"
                        self.particles.append(p)
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_k:
                    for spring in self.springs:
                        spring.stiffness = max(spring.stiffness - 50, 0)
                    print(f"Spring Stiffness: {spring.stiffness}")
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_l:
                    for spring in self.springs:
                        spring.stiffness = spring.stiffness + 50
                    print(f"Spring Stiffness: {spring.stiffness}")
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_n:
                    self.physics.temperature = max(self.physics.temperature - 50, 0)
                    print(f"Temperature: {self.physics.temperature}")
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_m:
                    self.physics.temperature += 50
                    print(f"Temperature: {self.physics.temperature}")
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_q:
                    for p in self.particles:
                        if p.tag == "loose":
                            p.fixed = True
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_w:
                    for p in self.particles:
                        if p.tag == "loose":
                            p.fixed = False

            if self.selected:
                self.selected.pos = pygame.Vector2(pygame.mouse.get_pos())
                self.selected.prev_pos = self.selected.pos.copy()

            self.physics.update(dt)

            W, H = SCREEN_SIZE
            if self.periodic_boundary:
                for p in self.particles:
                    p.pos.x %= W
                    p.pos.y %= H
                    p.prev_pos.x %= W
                    p.prev_pos.y %= H
            elif self.clamp_to_window:
                if self.bouncy_clamp:
                    for p in self.particles:
                        v = p.pos - p.prev_pos
                        if p.pos.x < 0 or p.pos.x > W:
                            p.pos.x = max(0, min(p.pos.x, W))
                            p.prev_pos.x = p.pos.x + (-v.x)
                        if p.pos.y < 0 or p.pos.y > H:
                            p.pos.y = max(0, min(p.pos.y, H))
                            p.prev_pos.y = p.pos.y + (-v.y)
                else:
                    for p in self.particles:
                        if p.pos.x < 0:
                            p.pos.x = 0
                            p.prev_pos.x = p.pos.x
                        elif p.pos.x > W:
                            p.pos.x = W
                            p.prev_pos.x = p.pos.x
                        if p.pos.y < 0:
                            p.pos.y = 0
                            p.prev_pos.y = p.pos.y
                        elif p.pos.y > H:
                            p.pos.y = H
                            p.prev_pos.y = p.pos.y

            self.screen.fill((30, 30, 30))
            self.renderer.draw(self.particles, self.springs)
            pygame.display.flip()

        pygame.quit()

if __name__ == '__main__':
    CellWallApp().run()
