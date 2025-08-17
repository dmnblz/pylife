"""Linear spring obeying Hooke's law with optional break force."""

import pygame
from particle import Particle


class Spring:
    def __init__(self, p1: Particle, p2: Particle, rest_length: float, stiffness: float, max_force: float = None,
                 invisible: bool = False):
        self.p1 = p1
        self.p2 = p2
        self.rest_length = rest_length
        self.stiffness = stiffness
        self.max_force = max_force
        self.broken = False
        self.invisible = invisible
        self.stretch_factor = 0.0  # 0 means at rest, positive means stretched, negative means compressed

    def apply(self):
        if self.broken:
            return
        delta = self.p2.pos - self.p1.pos
        dist = delta.length()
        if dist == 0:
            return
        # Hooke's law force
        diff = (dist - self.rest_length) / dist
        # Update stretch factor: normalized difference between current and rest length
        self.stretch_factor = (dist - self.rest_length) / self.rest_length
        
        force = delta * (self.stiffness * diff * 0.5)
        # break spring if force exceeds threshold
        if self.max_force is not None and force.length() > self.max_force:
            self.broken = True
            return
        self.p1.apply_force(force)
        self.p2.apply_force(-force)

    def potential_energy(self):
        return 0.5 * self.stiffness * ((self.p2.pos - self.p1.pos).length() - self.rest_length) ** 2
        
    def get_color(self):
        """
        Returns a color based on the spring's stretch factor:
        - Blue when compressed
        - White/gray when at rest
        - Red when stretched
        """
        if self.broken:
            return (100, 100, 100)  # Dark gray for broken springs
            
        # Define color limits
        max_stretch = 0.5  # 50% stretch will be full red
        max_compress = -0.3  # 30% compression will be full blue
        
        # Clamp stretch factor to our defined limits
        clamped_stretch = max(min(self.stretch_factor, max_stretch), max_compress)
        
        # Calculate color components
        if clamped_stretch > 0:  # Stretched (white to red)
            red = 200 + int(55 * (clamped_stretch / max_stretch))
            green = 200 - int(200 * (clamped_stretch / max_stretch))
            blue = 200 - int(200 * (clamped_stretch / max_stretch))
        elif clamped_stretch < 0:  # Compressed (white to blue)
            red = 200 - int(200 * (clamped_stretch / max_compress))
            green = 200 - int(200 * (clamped_stretch / max_compress))
            blue = 200 + int(55 * (clamped_stretch / max_compress))
        else:  # At rest
            red, green, blue = 200, 200, 200
            
        return (red, green, blue)
