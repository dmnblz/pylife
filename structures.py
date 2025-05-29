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
               max_force: float = None, color=(255, 0, 0)):
    """
    Create a capsule (rod) with uniform spacing: a rectangle length `length` and width 2*radius,
    capped by semicircles at ends. Returns (particles, springs).
    """
    particles = []
    springs = []
    # precompute
    total_length = 2 * length + 2 * math.pi * radius
    step = total_length / segments
    center_left = center + pygame.Vector2(-length / 2, 0)
    center_right = center + pygame.Vector2(length / 2, 0)

    for i in range(segments):
        s = i * step
        # left semicircle (top->bottom)
        if s < math.pi * radius:
            theta = math.pi/2 + (s / (math.pi * radius)) * math.pi
            pos = center_left + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
        # bottom side
        elif s < math.pi * radius + length:
            s2 = s - math.pi * radius
            pos = pygame.Vector2(center_left.x + s2, center.y - radius)
        # right semicircle (bottom->top)
        elif s < math.pi * radius + length + math.pi * radius:
            s3 = s - (math.pi * radius + length)
            theta = 3*math.pi/2 + (s3 / (math.pi * radius)) * math.pi
            pos = center_right + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
        # top side
        else:
            s4 = s - (2 * math.pi * radius + length)
            pos = pygame.Vector2(center_right.x - s4, center.y + radius)
        p = Particle(position=pos, tag=tag, color=color)
        particles.append(p)

    # connect springs between adjacent particles
    count = len(particles)
    for idx in range(count):
        p1 = particles[idx]
        p2 = particles[(idx + 1) % count]
        rest = (p2.pos - p1.pos).length()
        springs.append(Spring(p1, p2, rest, stiffness=stiffness, max_force=max_force))

    return particles, springs
