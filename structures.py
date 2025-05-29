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
