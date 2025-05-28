# structures.py
import math
import pygame
from particle import Particle
from spring import Spring


def create_wall(center: pygame.Vector2, radius: float = 100, segments: int = 20,
                tag: str = "wall", stiffness: float = 200, max_force: float = None):
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
        p = Particle(position=pos, tag=tag, color=(round(i / segments * 255), 0, 255 - round(i / segments * 255)))
        particles.append(p)
    # connect adjacent with springs (wrap within this wall only)
    for i in range(segments):
        p1 = particles[i]
        p2 = particles[(i + 1) % segments]
        rest_length = (p2.pos - p1.pos).length()
        springs.append(Spring(p1, p2, rest_length, stiffness=stiffness, max_force=max_force))
    return particles, springs
