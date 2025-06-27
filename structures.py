# structures.py
import math
import pygame
from particle import Particle
from spring import Spring
from bending_spring import BendingSpring


def create_wall(center: pygame.Vector2, radius: float = 100, segments: int = 20,
                tag: str = "wall", stiffness: float = 200, max_force: float = None, color=(255, 0, 0)):
    """
    Create a circular wall of particles and connecting springs.
    Returns two lists: [Particle, ...], [Spring, ...].
    """
    particles = []
    springs = []
    # create particles in a circle
    for i in range(segments):
        theta = (i / segments) * 2 * math.pi
        pos = center + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
        a = round(math.sin(i / segments * math.pi) * 255)
        p = Particle(position=pos, tag=tag, color=(a, 0, 255 - a))
        particles.append(p)
    # connect adjacent with springs (wrap within this wall only)
    for i in range(segments):
        p1 = particles[i]
        p2 = particles[(i + 1) % segments]
        rest_length = (p2.pos - p1.pos).length()
        springs.append(Spring(p1, p2, rest_length, stiffness=stiffness, max_force=max_force))
    return particles, springs


def create_bending_wall(center: pygame.Vector2, radius: float = 100, segments: int = 20,
                        tag: str = "wall", stiffness: float = 200, max_force: float = None,
                        color=(255, 0, 0), bending_stiffness: float = 100.0):
    """
    Create a circular wall of particles with linear springs and perpendicular bending springs.
    Returns three lists: particles, linear springs, bending springs.
    """
    # First build the linear wall
    particles, springs = create_wall(center, radius, segments,
                                     tag=tag, stiffness=stiffness,
                                     max_force=max_force, color=color)
    # Desired rest angle between segments in radians
    rest_angle = 2 * math.pi / segments
    # rest_angle = 90 / 180 * math.pi
    # print(rest_angle * 180 / math.pi)

    bending_springs = []
    # Create a bending spring at each vertex
    for i in range(segments):
        p_prev = particles[(i - 1) % segments]
        p_curr = particles[i]
        p_next = particles[(i + 1) % segments]
        bending_springs.append(
            BendingSpring(p_prev, p_curr, p_next,
                          rest_angle=rest_angle,
                          stiffness=bending_stiffness)
        )
    return particles, springs, bending_springs


def create_wall_rod(center: pygame.Vector2, radius: float = 100, segments: int = 20,
                    tag: str = "wall", stiffness: float = 200, max_force: float = None, color=(255, 0, 0)):
    """
    Create a circular wall of particles and connecting springs.
    Returns two lists: [Particle, ...], [Spring, ...].
    """
    particles = []
    springs = []
    # create particles in a circle
    for i in range(segments):
        theta = (i / segments) * 2 * math.pi
        pos = center + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
        a = round(math.sin(i / segments * math.pi) * 255)
        p = Particle(position=pos, tag=tag, color=(a, 0, 255 - a))
        particles.append(p)
    # connect adjacent with springs (wrap within this wall only)
    for i in range(segments):
        p1 = particles[i]
        p2 = particles[(i + 1) % segments]
        rest_length = (p2.pos - p1.pos).length()
        springs.append(Spring(p1, p2, rest_length, stiffness=stiffness, max_force=max_force))

        # if i % 20 == 0:
        # if 40 < i < 60:
        #     p1 = particles[i]
        #     p2 = particles[segments//2 - i]
        #     rest_length = radius * 2
        #     springs.append(Spring(p1, p2, rest_length, stiffness=stiffness/100, max_force=max_force))
        #

        if i <= segments // 2 and i % 2 == 0:
            p1 = particles[i]
            p2 = particles[-i]

            rest_length = abs(math.sin(i / segments * math.pi * 4)) * 2 * radius
            if segments // 8 <= i <= (segments // 2 - segments // 8):
                rest_length = 2 * radius

            springs.append(Spring(p1, p2, rest_length, stiffness=stiffness // 100, max_force=max_force))

        # if i <= segments//2 and i % 2 == 0:
        #     p1 = particles[i]
        #     p2 = particles[-i+5]
        #
        #     rest_length = abs(math.sin(i/segments*math.pi*4)) * 2 * radius
        #     if segments//8 <= i <= (segments//2 - segments//8):
        #         rest_length = 2 * radius
        #
        #         springs.append(Spring(p1, p2, rest_length, stiffness=stiffness//100, max_force=max_force))

        # if i == 0:
        #     p1 = particles[i]
        #     p2 = particles[segments//2]
        #     rest_length = 5.5 * radius
        #     springs.append(Spring(p1, p2, rest_length, stiffness=stiffness//10, max_force=max_force))

    return particles, springs


def coccus(center: pygame.Vector2, radius: float = 100, segments: int = 20,
           tag: str = "wall", stiffness: float = 200, max_force: float = None, color=(255, 0, 0)):
    """
    Create a circular wall of particles and connecting springs.
    Returns two lists: [Particle, ...], [Spring, ...].
    """
    particles = []
    springs = []
    # create particles in a circle
    for i in range(segments):
        theta = (i / segments) * 2 * math.pi
        pos = center + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
        a = round(math.sin(i / segments * math.pi) * 255)
        p = Particle(position=pos, tag=tag, color=(a, 0, 255 - a))
        particles.append(p)
    # connect adjacent with springs (wrap within this wall only)
    for i in range(segments):
        p1 = particles[i]
        p2 = particles[(i + 1) % segments]
        rest_length = (p2.pos - p1.pos).length()
        springs.append(Spring(p1, p2, rest_length, stiffness=stiffness, max_force=max_force))

        if i <= segments // 2 - 1 and i % 2 == 0:
            p1 = particles[i]
            p2 = particles[i + segments//2]

            rest_length = 3 * radius

            springs.append(Spring(p1, p2, rest_length, stiffness=stiffness/200, max_force=max_force, invisible=False))

    return particles, springs


# Capsule/rod shape: rectangle with semicircular ends
def create_rod(center: pygame.Vector2, radius: float = 100, length: float = 200,
               segments: int = 100, tag: str = "rod", stiffness: float = 200,
               max_force: float = None, color=(255, 0, 0),
               include_cytoskeleton: bool = False, cyto_stiffness: float = None,
               include_skeleton: bool = False, skeleton_count: int = 5, skeleton_stiffness: float = None):
    """
    Create a capsule (rod) with uniform spacing: a rectangle of given length and width 2*radius,
    capped by semicircles at ends. Returns (particles, springs).
    """
    particles = []
    springs = []

    # precompute spacing and segment counts
    total_length = 2 * length + 2 * math.pi * radius
    step = total_length / segments
    n_arc = int(round((math.pi * radius) / step))
    n_side = segments - 2 * n_arc
    center_left = center + pygame.Vector2(-length / 2, 0)
    center_right = center + pygame.Vector2(length / 2, 0)

    # generate perimeter particles
    for i in range(segments):
        s = i * step
        if s < math.pi * radius:
            # left semicircle (top->bottom)
            theta = math.pi/2 + (s / (math.pi * radius)) * math.pi
            pos = center_left + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
        elif s < math.pi * radius + length:
            # bottom side
            pos = pygame.Vector2(center_left.x + (s - math.pi * radius), center.y - radius)
        elif s < 2 * math.pi * radius + length:
            # right semicircle (bottom->top)
            theta = 3*math.pi/2 + ((s - math.pi * radius - length) / (math.pi * radius)) * math.pi
            pos = center_right + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
        else:
            # top side
            pos = pygame.Vector2(center_right.x - (s - 2*math.pi*radius - length), center.y + radius)
        p = Particle(position=pos, tag=tag, color=color)
        particles.append(p)

    # perimeter springs
    for idx in range(segments):
        p1 = particles[idx]
        p2 = particles[(idx + 1) % segments]
        rest = (p2.pos - p1.pos).length()
        springs.append(Spring(p1, p2, rest, stiffness=stiffness, max_force=max_force))

    # radial cytoskeleton on caps
    if include_cytoskeleton:
        cs = cyto_stiffness or stiffness
        bottom_y = center.y - radius
        top_y = center.y + radius
        bottom_nodes = [
            p for p in particles
            if abs(p.pos.y - bottom_y) < 1e-6 and center_left.x < p.pos.x < center_right.x
        ]
        top_nodes = [
            p for p in particles
            if abs(p.pos.y - top_y) < 1e-6 and center_left.x < p.pos.x < center_right.x
        ]
        bottom_nodes.sort(key=lambda p: p.pos.x)
        top_nodes.sort(key=lambda p: p.pos.x)
        for pb, pt in zip(bottom_nodes, top_nodes):
            rest = (pt.pos - pb.pos).length()
            springs.append(Spring(pb, pt, rest, stiffness=cs, max_force=max_force))
        # left cap radial
        for i in range(n_arc//2):
            p1 = particles[i]
            p2 = particles[n_arc-1-i]
            rest = (p2.pos - p1.pos).length()
            springs.append(Spring(p1, p2, rest, stiffness=cs, max_force=max_force))
        # right cap radial
        start = n_arc + n_side
        for i in range(n_arc//2):
            p1 = particles[start + i]
            p2 = particles[start + n_arc - 1 - i]
            rest = (p2.pos - p1.pos).length()
            springs.append(Spring(p1, p2, rest, stiffness=cs, max_force=max_force))

    # internal skeleton
    if include_skeleton:
        # create skeleton line
        skeleton_particles = []
        for k in range(skeleton_count):
            t = k / (skeleton_count - 1) if skeleton_count > 1 else 0.5
            pos = center_left + pygame.Vector2(length * t, 0)
            sp = Particle(position=pos, tag=tag + "_skel", color=color)
            particles.append(sp)
            skeleton_particles.append(sp)
        ss = skeleton_stiffness or stiffness
        # connect skeleton spine
        for i in range(len(skeleton_particles)-1):
            p1 = skeleton_particles[i]
            p2 = skeleton_particles[i+1]
            rest = (p2.pos - p1.pos).length()
            springs.append(Spring(p1, p2, rest, stiffness=ss, max_force=max_force))
            # springs.append(Spring(p1, p2, rest, stiffness=stiffness, max_force=max_force))
        # connect outer perimeter to skeleton:
        # straight sides → two nearest skeleton particles; arcs → single nearest
        perimeter = particles[:segments]
        eps = 1e-6
        for p in perimeter:
            # straight side detection by y-coordinate
            if abs(p.pos.y - (center.y - radius)) < eps or abs(p.pos.y - (center.y + radius)) < eps:
                # straight side: connect to two nearest skeleton particles
                dists = sorted(((sp.pos - p.pos).length(), sp) for sp in skeleton_particles)
                for _, sp in dists[:2]:
                    rest = (sp.pos - p.pos).length()
                    springs.append(Spring(p, sp, rest, stiffness=ss, max_force=max_force))
            else:
                # semicircle points: connect to single nearest skeleton particle
                sp = min(skeleton_particles, key=lambda sp: (sp.pos - p.pos).length())
                rest = (sp.pos - p.pos).length()
                springs.append(Spring(p, sp, rest, stiffness=ss, max_force=max_force))

    return particles, springs


