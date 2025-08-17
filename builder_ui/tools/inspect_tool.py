"""Tool for inspecting and editing existing particles, springs and bends."""

import math
import pygame
from .. import theme

from particle import Particle
from variable_particle import VariableParticle
from spring import Spring
from variable_spring import VariableSpring
from ..fields import SliderField, ColorField, KeyField, ButtonField
from .base import Tool


class InspectTool(Tool):
    """Select a particle or spring and edit its properties from the sidebar."""

    def __init__(self, sidebar: 'SidebarUI'):
        """Prepare fields for inspecting particles, springs and bends."""

        super().__init__(sidebar)
        self.particle = None
        self.spring = None
        self.bend = None

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        base_y = sidebar.extra_start_y

        # particle fields
        y = base_y
        self.color_field = ColorField(
            "P Color", self._get_color, self._set_color, x, y, width
        )
        y += 40
        self.mass_field = SliderField(
            "P Mass", 0.1, 10.0, self._get_mass, self._set_mass, x, y, width
        )
        y += 40
        self.radius_field = SliderField(
            "P Radius", 1, 50, self._get_radius, self._set_radius, x, y, width
        )
        y += 40
        self.elastic_field = SliderField(
            "P Elast", 0, 1, self._get_elasticity, self._set_elasticity, x, y, width
        )
        y += 40
        self.drag_field = SliderField(
            "P Drag", 1, 500, self._get_drag, self._set_drag, x, y, width
        )
        y += 40
        self.alt_drag_field = SliderField(
            "V Drag", 1, 500, self._get_alt_drag, self._set_alt_drag, x, y, width
        )
        y += 40
        self.vspeed_field = SliderField(
            "V Speed", 50, 1000, self._get_vspeed, self._set_vspeed, x, y, width
        )
        y += 40
        self.vkey_field = KeyField("V Key", self._get_vkey, self._set_vkey, x, y, width)
        y += 40
        self.vmode_btn = ButtonField(
            lambda: f"Mode: {self.particle.mode}" if isinstance(self.particle, VariableParticle) else "Mode",
            self._toggle_vmode,
            x,
            y,
            width,
            active=lambda: isinstance(self.particle, VariableParticle) and self.particle.mode == "toggle",
        )
        y += 40
        self.ptype_btn = ButtonField(
            lambda: "Normal" if isinstance(self.particle, VariableParticle) else "Variable",
            self._convert_particle,
            x,
            y,
            width,
            active=lambda: isinstance(self.particle, VariableParticle),
        )

        # spring fields
        y = base_y
        self.rest_field = SliderField(
            "S Rest", 1, 400, self._get_rest, self._set_rest, x, y, width
        )
        y += 40
        self.stiff_field = SliderField(
            "S Stiff", 10, 1000, self._get_stiff, self._set_stiff, x, y, width
        )
        y += 40
        self.max_field = SliderField(
            "S MaxF", 0, 2000, self._get_max, self._set_max, x, y, width
        )
        y += 40
        self.alt_field = SliderField(
            "V Rest2", 1, 400, self._get_alt_rest, self._set_alt_rest, x, y, width
        )
        y += 40
        self.speed_field = SliderField(
            "V Speed", 10, 1000, self._get_speed, self._set_speed, x, y, width
        )
        y += 40
        self.key_field = KeyField("V Key", self._get_key, self._set_key, x, y, width)
        y += 40
        self.mode_btn = ButtonField(
            lambda: f"Mode: {self.spring.mode}" if isinstance(self.spring, VariableSpring) else "Mode",
            self._toggle_mode,
            x,
            y,
            width,
            active=lambda: isinstance(self.spring, VariableSpring) and self.spring.mode == "toggle",
        )
        y += 40
        self.type_btn = ButtonField(
            lambda: "Normal" if isinstance(self.spring, VariableSpring) else "Variable",
            self._convert_spring,
            x,
            y,
            width,
            active=lambda: isinstance(self.spring, VariableSpring),
        )
        y += 40
        self.invis_btn = ButtonField(
            lambda: "Show" if self.spring and self.spring.invisible else "Hide",
            self._toggle_invisible,
            x,
            y,
            width,
            active=lambda: bool(self.spring and self.spring.invisible),
        )

        # bend fields
        y = base_y
        self.bangle_field = SliderField(
            "B Ang", 0, 180, self._get_bangle, self._set_bangle, x, y, width
        )
        y += 40
        self.bstiff_field = SliderField(
            "B Stiff", 10, 1000, self._get_bstiff, self._set_bstiff, x, y, width
        )

    # ---------------- helpers
    def _get_color(self) -> tuple[int, int, int]:
        """Return the selected particle colour or white."""
        return self.particle.color if self.particle else (255, 255, 255)

    def _set_color(self, color: tuple[int, int, int]) -> None:
        """Update the selected particle colour."""
        if self.particle:
            self.particle.color = color

    def _get_mass(self) -> float:
        """Return selected particle mass."""
        return self.particle.mass if self.particle else 0

    def _set_mass(self, value: float):
        """Set selected particle mass."""
        if self.particle:
            self.particle.mass = max(0.1, value)

    def _get_radius(self) -> float:
        """Return selected particle radius."""
        return self.particle.radius if self.particle else 0

    def _set_radius(self, value: float):
        """Set selected particle radius."""
        if self.particle:
            self.particle.radius = max(1, int(value))

    def _get_elasticity(self) -> float:
        """Return collision elasticity for the selected particle."""
        return self.particle.elasticity if self.particle else 0

    def _set_elasticity(self, value: float) -> None:
        """Set collision elasticity for the selected particle."""
        if self.particle:
            self.particle.elasticity = max(0.0, min(1.0, value))

    def _get_drag(self) -> float:
        """Return the base drag for the selected particle."""
        if isinstance(self.particle, VariableParticle):
            return self.particle.base_drag
        return self.particle.drag if self.particle else 0

    def _set_drag(self, value: float) -> None:
        """Set the base drag for the selected particle."""
        if isinstance(self.particle, VariableParticle):
            self.particle.base_drag = max(1, value)
        elif self.particle:
            self.particle.drag = max(1, value)

    def _get_alt_drag(self) -> float:
        """Return alternate drag for variable particles."""
        if isinstance(self.particle, VariableParticle):
            return self.particle.alt_drag
        return 0

    def _set_alt_drag(self, value: float) -> None:
        """Set alternate drag for variable particles."""
        if isinstance(self.particle, VariableParticle):
            self.particle.alt_drag = max(1, value)

    def _get_vspeed(self) -> float:
        """Return drag change speed for variable particles."""
        if isinstance(self.particle, VariableParticle):
            return self.particle.change_speed
        return 0

    def _set_vspeed(self, value: float) -> None:
        """Set drag change speed for variable particles."""
        if isinstance(self.particle, VariableParticle):
            self.particle.change_speed = max(10, value)

    def _get_vkey(self) -> int | None:
        """Return control key for variable particles."""
        if isinstance(self.particle, VariableParticle):
            return self.particle.key
        return None

    def _set_vkey(self, value: int | None) -> None:
        """Set control key for variable particles."""
        if isinstance(self.particle, VariableParticle):
            self.app.update_vparticle_key(self.particle, value)

    def _toggle_vmode(self) -> None:
        """Cycle the selected variable particle between hold and toggle."""
        if isinstance(self.particle, VariableParticle):
            self.particle.mode = "toggle" if self.particle.mode == "hold" else "hold"

    def _convert_particle(self) -> None:
        """Toggle the selected particle between variable and normal types."""
        if not self.particle:
            return
        if isinstance(self.particle, VariableParticle):
            old = self.particle
            self.app.update_vparticle_key(old, None)
            if old in self.app.variable_particles:
                self.app.variable_particles.remove(old)
            try:
                del old.base_drag, old.alt_drag, old.change_speed, old.key, old.mode, old.active
            except AttributeError:
                pass
            old.__class__ = Particle
        else:
            p = self.particle
            cfg = self.app.vparticle
            p.__class__ = VariableParticle
            p.base_drag = p.drag
            p.alt_drag = cfg.alt_drag
            p.change_speed = cfg.speed
            p.key = cfg.key
            p.mode = cfg.mode
            p.active = False
            self.app.variable_particles.append(p)
            self.app.register_variable_particle(p)

    def _layout_particle_fields(self) -> None:
        """Position particle widgets based on particle type."""
        y = self.sidebar.extra_start_y
        self.color_field.color_rect.y = y + 14
        self.color_field.box_rect.y = y + 10
        y += 40
        self.mass_field.slider_rect.y = y + 18
        self.mass_field.box_rect.y = y + 10
        y += 40
        self.radius_field.slider_rect.y = y + 18
        self.radius_field.box_rect.y = y + 10
        y += 40
        self.elastic_field.slider_rect.y = y + 18
        self.elastic_field.box_rect.y = y + 10
        y += 40
        self.drag_field.slider_rect.y = y + 18
        self.drag_field.box_rect.y = y + 10
        y += 40
        if isinstance(self.particle, VariableParticle):
            self.alt_drag_field.slider_rect.y = y + 18
            self.alt_drag_field.box_rect.y = y + 10
            y += 40
            self.vspeed_field.slider_rect.y = y + 18
            self.vspeed_field.box_rect.y = y + 10
            y += 40
            self.vkey_field.box_rect.y = y + 10
            y += 40
            self.vmode_btn.rect.y = y
            y += 40
        self.ptype_btn.rect.y = y

    def _get_rest(self) -> float:
        """Return spring rest length."""
        if isinstance(self.spring, VariableSpring):
            return self.spring.base_rest_length
        return self.spring.rest_length if self.spring else 0

    def _set_rest(self, value: float):
        """Update spring rest length."""
        if isinstance(self.spring, VariableSpring):
            self.spring.set_base_rest_length(value)
        elif self.spring:
            self.spring.rest_length = max(1, value)

    def _get_stiff(self) -> float:
        """Return spring stiffness."""
        return self.spring.stiffness if self.spring else 0

    def _set_stiff(self, value: float):
        """Set spring stiffness."""
        if self.spring:
            self.spring.stiffness = max(10, value)

    def _get_alt_rest(self) -> float:
        """Return alternate rest length for variable springs."""
        if isinstance(self.spring, VariableSpring):
            return self.spring.alt_rest_length
        return 0

    def _set_alt_rest(self, value: float) -> None:
        """Set alternate rest length for variable springs."""
        if isinstance(self.spring, VariableSpring):
            self.spring.set_alt_rest_length(value)

    def _get_speed(self) -> float:
        """Return change speed for variable springs."""
        if isinstance(self.spring, VariableSpring):
            return self.spring.change_speed
        return 0

    def _set_speed(self, value: float) -> None:
        """Set change speed for variable springs."""
        if isinstance(self.spring, VariableSpring):
            self.spring.change_speed = max(10, value)

    def _get_key(self) -> int | None:
        """Return control key for variable springs."""
        if isinstance(self.spring, VariableSpring):
            return self.spring.key
        return None

    def _set_key(self, value: int | None) -> None:
        """Set control key for variable springs."""
        if isinstance(self.spring, VariableSpring):
            self.sidebar.app.update_vspring_key(self.spring, value)

    def _toggle_mode(self) -> None:
        """Cycle the selected variable spring between hold and toggle modes."""
        if isinstance(self.spring, VariableSpring):
            self.spring.mode = "toggle" if self.spring.mode == "hold" else "hold"

    def _convert_spring(self) -> None:
        """Toggle the selected spring between variable and normal types."""
        if not self.spring:
            return
        if isinstance(self.spring, VariableSpring):
            old = self.spring
            self.sidebar.app.update_vspring_key(old, None)
            new = Spring(
                old.p1,
                old.p2,
                old.base_rest_length,
                old.stiffness,
                max_force=old.max_force,
                invisible=old.invisible,
            )
            idx = self.app.springs.index(old)
            self.app.springs[idx] = new
            if old in self.app.variable_springs:
                self.app.variable_springs.remove(old)
            self.spring = new
        else:
            old = self.spring
            cfg = self.app.vspring
            new = VariableSpring(
                old.p1,
                old.p2,
                old.rest_length,
                old.rest_length * cfg.alt_factor,
                old.stiffness,
                key=cfg.key,
                mode=cfg.mode,
                change_speed=cfg.speed,
                max_force=old.max_force,
                invisible=old.invisible,
            )
            idx = self.app.springs.index(old)
            self.app.springs[idx] = new
            self.app.variable_springs.append(new)
            self.sidebar.app.register_variable_spring(new)
            self.spring = new

    def _layout_spring_fields(self) -> None:
        """Position spring widgets based on spring type."""

        def place_slider(field, top):
            """Align ``field`` so its label starts at ``top``."""
            field.slider_rect.y = top + 18
            field.box_rect.y = top + 10
            return top + 40

        y = self.sidebar.extra_start_y
        y = place_slider(self.rest_field, y)
        y = place_slider(self.stiff_field, y)
        y = place_slider(self.max_field, y)
        if isinstance(self.spring, VariableSpring):
            y = place_slider(self.alt_field, y)
            y = place_slider(self.speed_field, y)
            self.key_field.box_rect.y = y + 10
            y += 40
            self.mode_btn.rect.y = y
            y += 40
        self.type_btn.rect.y = y
        y += 40
        self.invis_btn.rect.y = y

    def _get_bangle(self) -> float:
        """Return bend rest angle in degrees."""
        return math.degrees(self.bend.rest_angle) if self.bend else 0

    def _set_bangle(self, value: float):
        """Set bend rest angle in degrees."""
        if self.bend:
            self.bend.rest_angle = math.radians(max(0, value))

    def _get_bstiff(self) -> float:
        """Return bend stiffness."""
        return self.bend.stiffness if self.bend else 0

    def _set_bstiff(self, value: float):
        """Set bend stiffness."""
        if self.bend:
            self.bend.stiffness = max(10, value)

    def _get_max(self) -> float:
        """Return spring max force or ``0`` if unlimited."""
        if not self.spring:
            return 0
        return self.spring.max_force if self.spring.max_force is not None else 0

    def _set_max(self, value: float):
        """Set spring max force, using ``None`` for no limit."""
        if self.spring:
            self.spring.max_force = None if value == 0 else value

    def _toggle_invisible(self):
        """Toggle visibility of the selected spring."""
        if self.spring:
            self.spring.invisible = not self.spring.invisible

    # ---------------- control
    def start(self):
        """Activate the tool and clear previous selection."""
        super().start()
        self.particle = None
        self.spring = None
        self.bend = None

    def cancel(self):
        """Deactivate the tool and clear selection."""
        super().cancel()
        self.particle = None
        self.spring = None
        self.bend = None

    def draw_ui(self, offset: int = 0):
        """Render fields for the currently selected object."""
        if not super().draw_ui(offset):
            return
        if self.particle:
            self._layout_particle_fields()
            self.color_field.draw(self.sidebar.screen, offset)
            self.mass_field.draw(self.sidebar.screen, offset)
            self.radius_field.draw(self.sidebar.screen, offset)
            self.elastic_field.draw(self.sidebar.screen, offset)
            self.drag_field.draw(self.sidebar.screen, offset)
            if isinstance(self.particle, VariableParticle):
                self.alt_drag_field.draw(self.sidebar.screen, offset)
                self.vspeed_field.draw(self.sidebar.screen, offset)
                self.vkey_field.draw(self.sidebar.screen, offset)
                self.vmode_btn.draw(self.sidebar.screen, offset)
            self.ptype_btn.draw(self.sidebar.screen, offset)
        elif self.spring:
            self._layout_spring_fields()
            self.rest_field.draw(self.sidebar.screen, offset)
            self.stiff_field.draw(self.sidebar.screen, offset)
            self.max_field.draw(self.sidebar.screen, offset)
            if isinstance(self.spring, VariableSpring):
                self.alt_field.draw(self.sidebar.screen, offset)
                self.speed_field.draw(self.sidebar.screen, offset)
                self.key_field.draw(self.sidebar.screen, offset)
                self.mode_btn.draw(self.sidebar.screen, offset)
            self.type_btn.draw(self.sidebar.screen, offset)
            self.invis_btn.draw(self.sidebar.screen, offset)
        elif self.bend:
            self.bangle_field.draw(self.sidebar.screen, offset)
            self.bstiff_field.draw(self.sidebar.screen, offset)

    def draw_preview(self):
        """Highlight the currently selected object."""
        if not super().draw_preview():
            return
        if self.particle:
            # Accent glow + AA ring to match renderer selection
            c = self.app.renderer.world_to_screen(self.particle.pos)
            cx, cy = int(c.x), int(c.y)
            base_r = (self.particle.radius or 10)
            rr = max(1, int(base_r * self.app.renderer.zoom))
            glow_r = rr + 10
            glow = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*theme.ACCENT, 70), (glow_r + 2, glow_r + 2), glow_r)
            self.sidebar.screen.blit(glow, (cx - glow_r - 2, cy - glow_r - 2))
            try:
                import pygame.gfxdraw as gfx
                gfx.aacircle(self.sidebar.screen, cx, cy, rr + 6, theme.ACCENT)
                gfx.aacircle(self.sidebar.screen, cx, cy, rr + 7, theme.ACCENT)
            except Exception:
                pygame.draw.circle(self.sidebar.screen, theme.ACCENT, (cx, cy), rr + 7, 2)
        elif self.spring:
            p1 = self.app.world_to_screen(self.spring.p1.pos)
            p2 = self.app.world_to_screen(self.spring.p2.pos)
            pygame.draw.line(self.sidebar.screen, theme.ACCENT, p1, p2, 8)
            pygame.draw.line(self.sidebar.screen, (255, 255, 255), p1, p2, 2)
        elif self.bend:
            p1 = self.app.world_to_screen(self.bend.p1.pos)
            p2 = self.app.world_to_screen(self.bend.p2.pos)
            p3 = self.app.world_to_screen(self.bend.p3.pos)
            pygame.draw.line(self.sidebar.screen, theme.ACCENT, p1, p2, 8)
            pygame.draw.line(self.sidebar.screen, (255, 255, 255), p1, p2, 2)
            pygame.draw.line(self.sidebar.screen, theme.ACCENT, p2, p3, 8)
            pygame.draw.line(self.sidebar.screen, (255, 255, 255), p2, p3, 2)

    # ---------------- event handling
    def handle_event(self, event, offset: int = 0):
        """Process selection and slider events."""
        if not super().handle_event(event, offset):
            return False
        if self.particle:
            self._layout_particle_fields()
            if self.color_field.handle_event(event, offset):
                return True
            if self.mass_field.handle_event(event, offset):
                return True
            if self.radius_field.handle_event(event, offset):
                return True
            if self.elastic_field.handle_event(event, offset):
                return True
            if self.drag_field.handle_event(event, offset):
                return True
            if isinstance(self.particle, VariableParticle):
                if self.alt_drag_field.handle_event(event, offset):
                    return True
                if self.vspeed_field.handle_event(event, offset):
                    return True
                if self.vkey_field.handle_event(event, offset):
                    return True
                if self.vmode_btn.handle_event(event, offset):
                    return True
            if self.ptype_btn.handle_event(event, offset):
                return True
        elif self.spring:
            self._layout_spring_fields()
            if self.rest_field.handle_event(event, offset):
                return True
            if self.stiff_field.handle_event(event, offset):
                return True
            if self.max_field.handle_event(event, offset):
                return True
            if isinstance(self.spring, VariableSpring):
                if self.alt_field.handle_event(event, offset):
                    return True
                if self.speed_field.handle_event(event, offset):
                    return True
                if self.key_field.handle_event(event, offset):
                    return True
                if self.mode_btn.handle_event(event, offset):
                    return True
            if self.type_btn.handle_event(event, offset):
                return True
            if self.invis_btn.handle_event(event, offset):
                return True
        elif self.bend:
            if self.bangle_field.handle_event(event, offset):
                return True
            if self.bstiff_field.handle_event(event, offset):
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                mouse = self.app.screen_to_world(event.pos)
                dist_p = float("inf")
                dist_s = float("inf")
                dist_b = float("inf")
                nearest_p = None
                nearest_s = None
                nearest_b = None
                if self.app.particles:
                    nearest_p = min(self.app.particles, key=lambda p: (p.pos - mouse).length())
                    dist_p = (nearest_p.pos - mouse).length()
                if self.app.springs:
                    def seg_dist(s):
                        a = s.p1.pos
                        b = s.p2.pos
                        d = b - a
                        if d.length_squared() == 0:
                            return (mouse - a).length()
                        t = max(0, min(1, (mouse - a).dot(d) / d.length_squared()))
                        proj = a + d * t
                        return (mouse - proj).length()
                    nearest_s = min(self.app.springs, key=seg_dist)
                    dist_s = seg_dist(nearest_s)
                if self.app.bending_springs:
                    def seg_dist_b(bs):
                        def seg(a, b):
                            d = b - a
                            if d.length_squared() == 0:
                                return (mouse - a).length()
                            t = max(0, min(1, (mouse - a).dot(d) / d.length_squared()))
                            proj = a + d * t
                            return (mouse - proj).length()
                        return min(seg(bs.p1.pos, bs.p2.pos), seg(bs.p2.pos, bs.p3.pos))
                    nearest_b = min(self.app.bending_springs, key=seg_dist_b)
                    dist_b = seg_dist_b(nearest_b)
                if dist_p <= dist_s and dist_p <= dist_b:
                    if nearest_p is not None:
                        self.particle = nearest_p
                        self.spring = None
                        self.bend = None
                        return True
                elif dist_s <= dist_b:
                    if nearest_s is not None:
                        self.spring = nearest_s
                        self.particle = None
                        self.bend = None
                        return True
                else:
                    if nearest_b is not None:
                        self.bend = nearest_b
                        self.particle = None
                        self.spring = None
                        return True

        return False
