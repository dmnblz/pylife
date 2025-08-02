import pygame
import math
from color_picker import choose_color
from bending_spring import BendingSpring


class SliderField:
    """A simple horizontal slider with an editable numeric field."""

    BOX_WIDTH = 50

    def __init__(self, label, min_val, max_val, get_value, set_value, x, y, width):
        self.label = label
        self.min = min_val
        self.max = max_val
        self.get_value = get_value
        self.set_value = set_value
        self.font = pygame.font.SysFont(None, 22)

        slider_width = width - self.BOX_WIDTH - 10
        self.slider_rect = pygame.Rect(x, y + 18, slider_width, 6)
        self.box_rect = pygame.Rect(self.slider_rect.right + 5, y + 10, self.BOX_WIDTH, 22)

        self.dragging = False
        self.editing = False
        self.text = ""

    def _value_to_ratio(self, value):
        return max(0, min(1, (value - self.min) / (self.max - self.min)))

    def _ratio_to_value(self, ratio):
        return self.min + ratio * (self.max - self.min)

    def draw(self, screen):
        value = self.get_value()
        # label
        lbl = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(lbl, (self.slider_rect.x, self.slider_rect.y - 18))

        # slider track
        pygame.draw.rect(screen, (80, 80, 80), self.slider_rect)
        knob_x = int(self.slider_rect.x + self._value_to_ratio(value) * self.slider_rect.width)
        pygame.draw.rect(screen, (180, 180, 180), (knob_x - 3, self.slider_rect.y - 4, 6, self.slider_rect.height + 8))

        # textbox
        pygame.draw.rect(screen, (255, 255, 255), self.box_rect, 1)
        txt = self.text if self.editing else f"{value:.2f}"
        img = self.font.render(txt, True, (255, 255, 255))
        rect = img.get_rect(center=self.box_rect.center)
        screen.blit(img, rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.slider_rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value(event.pos[0])
                return True
            if self.box_rect.collidepoint(event.pos):
                self.editing = True
                self.text = ""
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_value(event.pos[0])
            return True
        elif event.type == pygame.KEYDOWN and self.editing:
            if event.key == pygame.K_RETURN:
                try:
                    val = float(self.text)
                    val = max(self.min, min(self.max, val))
                    self.set_value(val)
                except ValueError:
                    pass
                self.editing = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            else:
                ch = event.unicode
                if ch.isdigit() or ch in "-.":
                    self.text += ch
                    return True
        return False

    def _update_value(self, mouse_x):
        ratio = (mouse_x - self.slider_rect.x) / self.slider_rect.width
        ratio = max(0, min(1, ratio))
        self.set_value(self._ratio_to_value(ratio))


class ColorField:
    """Field allowing the user to pick a color or enter a hex value."""

    BOX_WIDTH = 70
    COLOR_SIZE = 24

    def __init__(self, label, get_color, set_color, x, y, width):
        self.label = label
        self.get_color = get_color
        self.set_color = set_color
        self.font = pygame.font.SysFont(None, 22)

        self.color_rect = pygame.Rect(x, y + 14, self.COLOR_SIZE, self.COLOR_SIZE)
        self.box_rect = pygame.Rect(
            self.color_rect.right + 5, y + 10, self.BOX_WIDTH, 22
        )

        self.editing = False
        self.text = ""

    def draw(self, screen):
        color = self.get_color()
        lbl = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(lbl, (self.color_rect.x, self.color_rect.y - 18))

        pygame.draw.rect(screen, color, self.color_rect)
        pygame.draw.rect(screen, (255, 255, 255), self.color_rect, 1)

        pygame.draw.rect(screen, (255, 255, 255), self.box_rect, 1)
        txt = self.text if self.editing else "#%02X%02X%02X" % color
        img = self.font.render(txt, True, (255, 255, 255))
        rect = img.get_rect(center=self.box_rect.center)
        screen.blit(img, rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.color_rect.collidepoint(event.pos):
                self._choose_color()
                return True
            if self.box_rect.collidepoint(event.pos):
                self.editing = True
                self.text = ""
                return True
        elif event.type == pygame.KEYDOWN and self.editing:
            if event.key == pygame.K_RETURN:
                self._set_color_hex(self.text)
                self.editing = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            else:
                ch = event.unicode.upper()
                if ch in "0123456789ABCDEF#":
                    self.text += ch
                    return True
        return False

    def _choose_color(self):
        """Launch the color picker in a separate process."""
        rgb = choose_color(self.get_color())
        if rgb:
            self.set_color(rgb)

    def _set_color_hex(self, value: str):
        value = value.lstrip("#")
        if len(value) != 6:
            return
        try:
            r = int(value[0:2], 16)
            g = int(value[2:4], 16)
            b = int(value[4:6], 16)
            self.set_color((r, g, b))
        except ValueError:
            pass


class KeyField:
    """Editable single-key input used for controlling hook arms."""

    BOX_WIDTH = 60

    def __init__(self, label, get_key, set_key, x, y, width):
        self.label = label
        self.get_key = get_key
        self.set_key = set_key
        self.font = pygame.font.SysFont(None, 22)

        self.box_rect = pygame.Rect(x, y + 10, self.BOX_WIDTH, 22)
        self.editing = False

    def draw(self, screen):
        key = self.get_key()
        text = pygame.key.name(key) if key is not None else "None"
        if self.editing:
            text = f"[{text}]"

        lbl = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(lbl, (self.box_rect.x, self.box_rect.y - 18))
        pygame.draw.rect(screen, (255, 255, 255), self.box_rect, 1)
        img = self.font.render(text, True, (255, 255, 255))
        rect = img.get_rect(center=self.box_rect.center)
        screen.blit(img, rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.box_rect.collidepoint(event.pos):
                self.editing = True
                return True
        elif event.type == pygame.KEYDOWN and self.editing:
            if event.key == pygame.K_ESCAPE:
                self.set_key(None)
            else:
                self.set_key(event.key)
            self.editing = False
            return True
        return False


class ParticleTool:
    """Handle options for creating new particles."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.color_field = ColorField(
            "Color", lambda: self.app.color, self.app.set_color, x, y, width
        )
        y += 40
        self.mass_field = SliderField(
            "Mass", 0.1, 10.0, lambda: self.app.mass, self.app.set_mass, x, y, width
        )
        y += 40
        self.radius_field = SliderField(
            "Radius", 1, 50, lambda: self.app.radius, self.app.set_radius, x, y, width
        )

    # ---------------- control
    def start(self):
        self.active = True

    def cancel(self):
        self.active = False

    # ---------------- drawing
    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        self.color_field.draw(self.sidebar.screen)
        self.mass_field.draw(self.sidebar.screen)
        self.radius_field.draw(self.sidebar.screen)

    def draw_preview(self):
        pass

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False
        if self.sidebar.visible:
            if self.color_field.handle_event(event):
                return True
            if self.mass_field.handle_event(event):
                return True
            if self.radius_field.handle_event(event):
                return True
        return False


class SpringTool:
    """Handle spring stiffness options when creating new springs."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.stiff_field = SliderField(
            "Stiff", 10, 1000, lambda: self.app.stiffness, self.app.set_stiffness, x, y, width
        )

    # ---------------- control
    def start(self):
        self.active = True

    def cancel(self):
        self.active = False

    # ---------------- drawing
    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        self.stiff_field.draw(self.sidebar.screen)

    def draw_preview(self):
        pass

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False
        if self.sidebar.visible:
            if self.stiff_field.handle_event(event):
                return True
        return False


class BendingSpringTool:
    """Create a bending spring by choosing three particles."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False
        self.angle = 90.0
        self.stiffness = 200.0
        self.auto_angle = False
        self.selected: list = []

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.angle_field = SliderField(
            "Angle", 0, 180, lambda: self.angle, self._set_angle, x, y, width
        )
        y += 40
        self.stiff_field = SliderField(
            "Stiff", 10, 1000, lambda: self.stiffness, self._set_stiff, x, y, width
        )
        y += 40
        self.auto_rect = pygame.Rect(x, y, width, SidebarUI.BUTTON_HEIGHT)
        y += SidebarUI.BUTTON_HEIGHT + 12
        self.create_rect = pygame.Rect(x, y, width, SidebarUI.BUTTON_HEIGHT)

    def _set_angle(self, val: float):
        self.angle = max(0, val)

    def _set_stiff(self, val: float):
        self.stiffness = max(10, val)

    # ---------------- control
    def start(self):
        self.active = True
        self.auto_angle = False
        self.selected.clear()

    def cancel(self):
        self.active = False
        self.selected.clear()

    # ---------------- drawing
    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        if not self.auto_angle:
            self.angle_field.draw(self.sidebar.screen)
        self.stiff_field.draw(self.sidebar.screen)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.auto_rect)
        label = "Auto" if not self.auto_angle else "Manual"
        txt = self.sidebar.font.render(label, True, (255, 255, 255))
        rect = txt.get_rect(center=self.auto_rect.center)
        self.sidebar.screen.blit(txt, rect)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.create_rect)
        txt = self.sidebar.font.render("Create", True, (255, 255, 255))
        rect = txt.get_rect(center=self.create_rect.center)
        self.sidebar.screen.blit(txt, rect)

    def draw_preview(self):
        if not self.active:
            return
        screen = self.sidebar.screen
        color = (150, 150, 150)
        for p in self.selected:
            pygame.draw.circle(screen, color, (int(p.pos.x), int(p.pos.y)), int(p.radius) + 4, 1)
        if len(self.selected) >= 2:
            pygame.draw.line(screen, color, self.selected[0].pos, self.selected[1].pos, 1)
        if len(self.selected) == 3:
            pygame.draw.line(screen, color, self.selected[1].pos, self.selected[2].pos, 1)

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False

        if self.sidebar.visible:
            if not self.auto_angle:
                if self.angle_field.handle_event(event):
                    return True
            if self.stiff_field.handle_event(event):
                return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.auto_rect.collidepoint(event.pos):
                    self.auto_angle = not self.auto_angle
                    return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.create_rect.collidepoint(event.pos) and len(self.selected) == 3:
                    from math import radians
                    if self.auto_angle:
                        v1 = self.selected[0].pos - self.selected[1].pos
                        v2 = self.selected[2].pos - self.selected[1].pos
                        if v1.length() == 0 or v2.length() == 0:
                            angle = 0
                        else:
                            dot = max(-1.0, min(1.0, v1.dot(v2) / (v1.length()*v2.length())))
                            angle = math.acos(dot)
                    else:
                        angle = radians(self.angle)
                    bs = BendingSpring(
                        self.selected[0],
                        self.selected[1],
                        self.selected[2],
                        angle,
                        self.stiffness,
                    )
                    self.app.bending_springs.append(bs)
                    self.cancel()
                    self.sidebar.app.set_mode("drag")
                    return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                if self.app.particles:
                    mouse = pygame.Vector2(event.pos)
                    particle = min(self.app.particles, key=lambda p: (p.pos - mouse).length())
                    if particle not in self.selected:
                        if len(self.selected) < 3:
                            self.selected.append(particle)
                        else:
                            self.selected.pop(0)
                            self.selected.append(particle)
                    return True

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.selected.clear()
            return True

        return False


class GridTool:
    """Toggle a grid overlay and adjust its spacing."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.toggle_rect = pygame.Rect(x, y, width, SidebarUI.BUTTON_HEIGHT)
        y += SidebarUI.BUTTON_HEIGHT + 12
        self.size_field = SliderField(
            "Spacing", 5, 200, lambda: self.app.grid_size, self.app.set_grid_size, x, y, width
        )

    # ---------------- control
    def start(self):
        self.active = True

    def cancel(self):
        self.active = False

    # ---------------- drawing
    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.toggle_rect)
        state = "On" if self.app.grid_enabled else "Off"
        txt = self.sidebar.font.render(f"Grid: {state}", True, (255, 255, 255))
        rect = txt.get_rect(center=self.toggle_rect.center)
        self.sidebar.screen.blit(txt, rect)
        self.size_field.draw(self.sidebar.screen)

    def draw_preview(self):
        pass

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False
        if self.sidebar.visible:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.toggle_rect.collidepoint(event.pos):
                    self.app.toggle_grid()
                    return True
            if self.size_field.handle_event(event):
                return True
        return False


class EnvironmentTool:
    """Expose global simulation options such as gravity and temperature."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.gx_field = SliderField(
            "Grav X", -2000, 2000,
            lambda: self.app.physics.gravity.x,
            self.app.set_gravity_x,
            x, y, width,
        )
        y += 40
        self.gy_field = SliderField(
            "Grav Y", -2000, 2000,
            lambda: self.app.physics.gravity.y,
            self.app.set_gravity_y,
            x, y, width,
        )
        y += 40
        self.rep_rad_field = SliderField(
            "Rep Rad", 0, 200,
            lambda: self.app.physics.repulsion_radius,
            self.app.set_repulsion_radius,
            x, y, width,
        )
        y += 40
        self.rep_str_field = SliderField(
            "Rep Str", 0, 10000,
            lambda: self.app.physics.repulsion_strength,
            self.app.set_repulsion_strength,
            x, y, width,
        )
        y += 40
        self.damp_field = SliderField(
            "Damp", 0, 5,
            lambda: self.app.physics.damping_coeff,
            self.app.set_damping,
            x, y, width,
        )
        y += 40
        self.temp_field = SliderField(
            "Temp", 0, 1000,
            lambda: self.app.physics.temperature,
            self.app.set_temperature,
            x, y, width,
        )

    # ---------------- control
    def start(self):
        self.active = True

    def cancel(self):
        self.active = False

    # ---------------- drawing
    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        self.gx_field.draw(self.sidebar.screen)
        self.gy_field.draw(self.sidebar.screen)
        self.rep_rad_field.draw(self.sidebar.screen)
        self.rep_str_field.draw(self.sidebar.screen)
        self.damp_field.draw(self.sidebar.screen)
        self.temp_field.draw(self.sidebar.screen)

    def draw_preview(self):
        pass

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False
        if self.sidebar.visible:
            if self.gx_field.handle_event(event):
                return True
            if self.gy_field.handle_event(event):
                return True
            if self.rep_rad_field.handle_event(event):
                return True
            if self.rep_str_field.handle_event(event):
                return True
            if self.damp_field.handle_event(event):
                return True
            if self.temp_field.handle_event(event):
                return True
        return False


class CircleTool:
    """Handle circle preview creation with sliders and dragging."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False
        self.center = None
        self.radius = 50.0
        self.segments = 8
        self.dragging = False
        self.stiffness = 200.0
        self.bend_stiffness = 200.0
        self.include_bend = False

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.radius_field = SliderField(
            "C Radius", 5, 400, lambda: self.radius, self._set_radius, x, y, width
        )
        y += 40
        self.segments_field = SliderField(
            "Segments", 3, 60, lambda: self.segments, self._set_segments, x, y, width
        )
        y += 40
        self.stiff_field = SliderField(
            "Stiff", 10, 1000, lambda: self.stiffness, self._set_stiff, x, y, width
        )
        y += 40
        self.bend_rect = pygame.Rect(x, y, width, SidebarUI.BUTTON_HEIGHT)
        y += SidebarUI.BUTTON_HEIGHT + 4
        self.bstiff_field = SliderField(
            "BStiff", 10, 1000, lambda: self.bend_stiffness, self._set_bstiff, x, y, width
        )
        y += 40
        self.create_rect = pygame.Rect(x, y, width, SidebarUI.BUTTON_HEIGHT)

    # ---------------- value setters
    def _set_radius(self, value: float):
        self.radius = max(1, value)

    def _set_segments(self, value: float):
        self.segments = max(3, int(value))

    def _set_stiff(self, value: float):
        self.stiffness = max(10, value)

    def _set_bstiff(self, value: float):
        self.bend_stiffness = max(10, value)

    # ---------------- control
    def start(self):
        self.active = True
        self.center = None
        self.stiffness = self.app.stiffness
        self.bend_stiffness = self.app.stiffness
        self.include_bend = False
        self.stiffness = self.app.stiffness
        self.bend_stiffness = self.app.stiffness

    def cancel(self):
        self.active = False
        self.dragging = False

    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        self.radius_field.draw(self.sidebar.screen)
        self.segments_field.draw(self.sidebar.screen)
        self.stiff_field.draw(self.sidebar.screen)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.bend_rect)
        bend_txt = "Bend: On" if self.include_bend else "Bend: Off"
        txt = self.sidebar.font.render(bend_txt, True, (255, 255, 255))
        rect = txt.get_rect(center=self.bend_rect.center)
        self.sidebar.screen.blit(txt, rect)
        if self.include_bend:
            self.bstiff_field.draw(self.sidebar.screen)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.create_rect)
        txt = self.sidebar.font.render("Create", True, (255, 255, 255))
        rect = txt.get_rect(center=self.create_rect.center)
        self.sidebar.screen.blit(txt, rect)

    def draw_preview(self):
        if not self.active or self.center is None:
            return
        screen = self.sidebar.screen
        color = (150, 150, 150)
        center = self.app.snap_to_grid(self.center)
        pygame.draw.circle(screen, color, (int(center.x), int(center.y)), int(self.radius), 1)
        for i in range(self.segments):
            theta1 = (i / self.segments) * 2 * math.pi
            theta2 = ((i + 1) % self.segments) / self.segments * 2 * math.pi
            p1 = self.app.snap_to_grid(
                self.center + pygame.Vector2(math.cos(theta1), math.sin(theta1)) * self.radius
            )
            p2 = self.app.snap_to_grid(
                self.center + pygame.Vector2(math.cos(theta2), math.sin(theta2)) * self.radius
            )
            pygame.draw.line(screen, color, p1, p2, 1)
            pygame.draw.circle(screen, color, (int(p1.x), int(p1.y)), self.app.radius, 1)

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False

        if self.sidebar.visible:
            if self.radius_field.handle_event(event):
                return True
            if self.segments_field.handle_event(event):
                return True
            if self.stiff_field.handle_event(event):
                return True
            if self.include_bend and self.bstiff_field.handle_event(event):
                return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.bend_rect.collidepoint(event.pos):
                    self.include_bend = not self.include_bend
                    return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.create_rect.collidepoint(event.pos) and self.center:
                    self.app.create_circle(
                        self.center,
                        self.radius,
                        self.segments,
                        self.stiffness,
                        self.include_bend,
                        self.bend_stiffness,
                    )
                    self.cancel()
                    self.sidebar.app.set_mode("drag")
                    return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # click in world area to set center
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                self.center = self.app.snap_to_grid(pygame.Vector2(event.pos))
                self.dragging = True
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse = self.app.snap_to_grid(pygame.Vector2(event.pos))
            self.radius = (mouse - self.center).length()
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return True

        return False


class RodTool:
    """Handle rod preview creation with sliders and click placement."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False
        self.center = None
        self.radius = 30.0
        self.length = 100.0
        self.segments = 20
        self.skeleton_count = 5
        self.include_cytoskeleton = False
        self.include_skeleton = False
        self.dragging = False
        self.stiffness = 200.0
        self.bend_stiffness = 200.0
        self.include_bend = False

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.radius_field = SliderField(
            "R Radius", 5, 200, lambda: self.radius, self._set_radius, x, y, width
        )
        y += 40
        self.length_field = SliderField(
            "Length", 10, 600, lambda: self.length, self._set_length, x, y, width
        )
        y += 40
        self.segments_field = SliderField(
            "Segments", 4, 200, lambda: self.segments, self._set_segments, x, y, width
        )
        y += 40
        self.skel_count_field = SliderField(
            "Skeleton", 1, 20, lambda: self.skeleton_count, self._set_skel_count, x, y, width
        )
        y += 40
        self.stiff_field = SliderField(
            "Stiff", 10, 1000, lambda: self.stiffness, self._set_stiff, x, y, width
        )
        y += 40
        self.bend_rect = pygame.Rect(x, y, width, SidebarUI.BUTTON_HEIGHT)
        y += SidebarUI.BUTTON_HEIGHT + 4
        self.bstiff_field = SliderField(
            "BStiff", 10, 1000, lambda: self.bend_stiffness, self._set_bstiff, x, y, width
        )
        y += 40
        self.cyto_rect = pygame.Rect(x, y, width, SidebarUI.BUTTON_HEIGHT)
        y += SidebarUI.BUTTON_HEIGHT + 4
        self.skeleton_rect = pygame.Rect(x, y, width, SidebarUI.BUTTON_HEIGHT)
        y += SidebarUI.BUTTON_HEIGHT + 4
        self.create_rect = pygame.Rect(x, y, width, SidebarUI.BUTTON_HEIGHT)

    # ---------------- value setters
    def _set_radius(self, value: float):
        self.radius = max(1, value)

    def _set_length(self, value: float):
        self.length = max(1, value)

    def _set_segments(self, value: float):
        self.segments = max(4, int(value))

    def _set_skel_count(self, value: float):
        self.skeleton_count = max(1, int(value))

    def _set_stiff(self, value: float):
        self.stiffness = max(10, value)

    def _set_bstiff(self, value: float):
        self.bend_stiffness = max(10, value)

    # ---------------- control
    def start(self):
        self.active = True
        self.center = None

    def cancel(self):
        self.active = False
        self.dragging = False

    # ---------------- helpers
    def _generate_points(self):
        center = self.center
        if center is None:
            return []
        radius = self.radius
        length = self.length
        segments = self.segments
        pts = []
        total_length = 2 * length + 2 * math.pi * radius
        step = total_length / segments
        center_left = center + pygame.Vector2(-length / 2, 0)
        center_right = center + pygame.Vector2(length / 2, 0)
        for i in range(segments):
            s = i * step
            if s < math.pi * radius:
                theta = math.pi / 2 + (s / (math.pi * radius)) * math.pi
                pos = center_left + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
            elif s < math.pi * radius + length:
                pos = pygame.Vector2(center_left.x + (s - math.pi * radius), center.y - radius)
            elif s < 2 * math.pi * radius + length:
                theta = 3 * math.pi / 2 + ((s - math.pi * radius - length) / (math.pi * radius)) * math.pi
                pos = center_right + pygame.Vector2(math.cos(theta), math.sin(theta)) * radius
            else:
                pos = pygame.Vector2(
                    center_right.x - (s - 2 * math.pi * radius - length), center.y + radius
                )
            pts.append(self.app.snap_to_grid(pos))
        return pts

    # ---------------- drawing
    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        self.radius_field.draw(self.sidebar.screen)
        self.length_field.draw(self.sidebar.screen)
        self.segments_field.draw(self.sidebar.screen)
        self.skel_count_field.draw(self.sidebar.screen)
        self.stiff_field.draw(self.sidebar.screen)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.bend_rect)
        bend_txt = "Bend: On" if self.include_bend else "Bend: Off"
        txt = self.sidebar.font.render(bend_txt, True, (255, 255, 255))
        rect = txt.get_rect(center=self.bend_rect.center)
        self.sidebar.screen.blit(txt, rect)
        if self.include_bend:
            self.bstiff_field.draw(self.sidebar.screen)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.cyto_rect)
        cyto_txt = "Cyto: On" if self.include_cytoskeleton else "Cyto: Off"
        txt = self.sidebar.font.render(cyto_txt, True, (255, 255, 255))
        rect = txt.get_rect(center=self.cyto_rect.center)
        self.sidebar.screen.blit(txt, rect)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.skeleton_rect)
        skel_txt = "Skel: On" if self.include_skeleton else "Skel: Off"
        txt = self.sidebar.font.render(skel_txt, True, (255, 255, 255))
        rect = txt.get_rect(center=self.skeleton_rect.center)
        self.sidebar.screen.blit(txt, rect)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.create_rect)
        txt = self.sidebar.font.render("Create", True, (255, 255, 255))
        rect = txt.get_rect(center=self.create_rect.center)
        self.sidebar.screen.blit(txt, rect)

    def draw_preview(self):
        if not self.active or self.center is None:
            return
        screen = self.sidebar.screen
        color = (150, 150, 150)
        pts = self._generate_points()
        for i in range(len(pts)):
            p1 = pts[i]
            p2 = pts[(i + 1) % len(pts)]
            pygame.draw.line(screen, color, p1, p2, 1)
            pygame.draw.circle(screen, color, (int(p1.x), int(p1.y)), self.app.radius, 1)

        # draw cytoskeleton preview
        if self.include_cytoskeleton:
            total_length = 2 * self.length + 2 * math.pi * self.radius
            step = total_length / self.segments
            n_arc = int(round((math.pi * self.radius) / step))
            n_side = self.segments - 2 * n_arc

            bottom_y = self.center.y - self.radius
            top_y = self.center.y + self.radius
            bottom_nodes = [
                p
                for p in pts
                if abs(p.y - bottom_y) < 1e-6
                and (self.center.x - self.length / 2) < p.x < (self.center.x + self.length / 2)
            ]
            top_nodes = [
                p
                for p in pts
                if abs(p.y - top_y) < 1e-6
                and (self.center.x - self.length / 2) < p.x < (self.center.x + self.length / 2)
            ]
            bottom_nodes.sort(key=lambda p: p.x)
            top_nodes.sort(key=lambda p: p.x)
            for b, t in zip(bottom_nodes, top_nodes):
                pygame.draw.line(screen, color, b, t, 1)

            for i in range(n_arc // 2):
                pygame.draw.line(screen, color, pts[i], pts[n_arc - 1 - i], 1)

            start = n_arc + n_side
            for i in range(n_arc // 2):
                pygame.draw.line(screen, color, pts[start + i], pts[start + n_arc - 1 - i], 1)

        # draw skeleton preview
        if self.include_skeleton:
            skeleton_pts = []
            center_left = self.center + pygame.Vector2(-self.length / 2, 0)
            for k in range(self.skeleton_count):
                t = k / (self.skeleton_count - 1) if self.skeleton_count > 1 else 0.5
                pos = center_left + pygame.Vector2(self.length * t, 0)
                skeleton_pts.append(pos)

            for i in range(len(skeleton_pts) - 1):
                pygame.draw.line(screen, color, skeleton_pts[i], skeleton_pts[i + 1], 1)

            eps = 1e-6
            for p in pts:
                if abs(p.y - (self.center.y - self.radius)) < eps or abs(p.y - (self.center.y + self.radius)) < eps:
                    dists = sorted(((sp - p).length(), sp) for sp in skeleton_pts)
                    for _, sp in dists[:2]:
                        pygame.draw.line(screen, color, p, sp, 1)
                else:
                    sp = min(skeleton_pts, key=lambda sp: (sp - p).length())
                    pygame.draw.line(screen, color, p, sp, 1)

            for sp in skeleton_pts:
                pygame.draw.circle(screen, color, (int(sp.x), int(sp.y)), self.app.radius, 1)

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False

        if self.sidebar.visible:
            if self.radius_field.handle_event(event):
                return True
            if self.length_field.handle_event(event):
                return True
            if self.segments_field.handle_event(event):
                return True
            if self.skel_count_field.handle_event(event):
                return True
            if self.stiff_field.handle_event(event):
                return True
            if self.include_bend and self.bstiff_field.handle_event(event):
                return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.bend_rect.collidepoint(event.pos):
                    self.include_bend = not self.include_bend
                    return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.cyto_rect.collidepoint(event.pos):
                    self.include_cytoskeleton = not self.include_cytoskeleton
                    return True
                if self.skeleton_rect.collidepoint(event.pos):
                    self.include_skeleton = not self.include_skeleton
                    return True
                if self.create_rect.collidepoint(event.pos) and self.center:
                    self.app.create_rod(
                        self.center,
                        self.radius,
                        self.length,
                        self.segments,
                        self.include_cytoskeleton,
                        self.include_skeleton,
                        self.skeleton_count,
                        self.stiffness,
                        self.include_bend,
                        self.bend_stiffness,
                    )
                    self.cancel()
                    self.sidebar.app.set_mode("drag")
                    return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                self.center = self.app.snap_to_grid(pygame.Vector2(event.pos))
                self.dragging = True
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse = self.app.snap_to_grid(pygame.Vector2(event.pos))
            self.length = abs(mouse.x - self.center.x) * 2
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return True

        return False


class HookArmTool:
    """Preview and creation helper for :class:`HookArm` instances.

    The tool lets the user configure segment count, spacing, particle
    mass/radius, spring stiffness, cycle speed, colours, adhesion factor and
    the key used for cycling the arm.
    """

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False
        self.base = None
        self.direction = pygame.Vector2(1, 0)
        self.segments = 3
        self.spacing = 20.0
        self.mass = 0.5
        self.radius = 8.0
        self.stiffness = 500.0
        self.cycle_speed = 240.0
        self.color = (0, 150, 255)
        self.high_drag_color = (255, 50, 50)
        self.adhesion_factor = 10.0
        self.cycle_key = pygame.K_h
        self.dragging = False

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.seg_field = SliderField(
            "Segments", 1, 10, lambda: self.segments, self._set_segments, x, y, width
        )
        y += 40
        self.space_field = SliderField(
            "Spacing", 5, 60, lambda: self.spacing, self._set_spacing, x, y, width
        )
        y += 40
        self.mass_field = SliderField(
            "Mass", 0.1, 10.0, lambda: self.mass, self._set_mass, x, y, width
        )
        y += 40
        self.radius_field = SliderField(
            "Radius", 1, 50, lambda: self.radius, self._set_radius, x, y, width
        )
        y += 40
        self.stiff_field = SliderField(
            "Stiff", 10, 1000, lambda: self.stiffness, self._set_stiffness, x, y, width
        )
        y += 40
        self.speed_field = SliderField(
            "Speed", 50, 1000, lambda: self.cycle_speed, self._set_speed, x, y, width
        )
        y += 40
        self.color_field = ColorField("Color", lambda: self.color, self._set_color, x, y, width)
        y += 40
        self.high_field = ColorField(
            "HDrag", lambda: self.high_drag_color, self._set_high_color, x, y, width
        )
        y += 40
        self.adh_field = SliderField(
            "AdhesMF", 1, 20, lambda: self.adhesion_factor, self._set_adhesion, x, y, width
        )
        y += 40
        self.key_field = KeyField("Cycle", lambda: self.cycle_key, self._set_key, x, y, width)
        y += 40
        self.create_rect = pygame.Rect(x, y, width, SidebarUI.BUTTON_HEIGHT)

    # ---------------- value setters
    def _set_segments(self, value: float):
        self.segments = max(1, int(value))

    def _set_spacing(self, value: float):
        self.spacing = max(1, value)

    def _set_mass(self, value: float):
        self.mass = max(0.1, value)

    def _set_radius(self, value: float):
        self.radius = max(1, value)

    def _set_stiffness(self, value: float):
        self.stiffness = max(10, value)

    def _set_speed(self, value: float):
        self.cycle_speed = max(10, value)

    def _set_color(self, color):
        self.color = color

    def _set_high_color(self, color):
        self.high_drag_color = color

    def _set_adhesion(self, value: float):
        self.adhesion_factor = max(1, value)

    def _set_key(self, value: int | None):
        self.cycle_key = value

    # ---------------- control
    def start(self):
        self.active = True
        self.base = None

    def cancel(self):
        self.active = False
        self.dragging = False

    # ---------------- drawing helpers
    def _preview_points(self):
        if not self.base:
            return []
        if self.direction.length() == 0:
            return []
        dir_norm = self.direction.normalize()
        pts = []
        for i in range(1, self.segments + 1):
            pos = self.base.pos + dir_norm * self.spacing * i
            pts.append(self.app.snap_to_grid(pos))
        return pts

    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        self.seg_field.draw(self.sidebar.screen)
        self.space_field.draw(self.sidebar.screen)
        self.mass_field.draw(self.sidebar.screen)
        self.radius_field.draw(self.sidebar.screen)
        self.stiff_field.draw(self.sidebar.screen)
        self.speed_field.draw(self.sidebar.screen)
        self.color_field.draw(self.sidebar.screen)
        self.high_field.draw(self.sidebar.screen)
        self.adh_field.draw(self.sidebar.screen)
        self.key_field.draw(self.sidebar.screen)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.create_rect)
        txt = self.sidebar.font.render("Create", True, (255, 255, 255))
        rect = txt.get_rect(center=self.create_rect.center)
        self.sidebar.screen.blit(txt, rect)

    def draw_preview(self):
        if not self.active or not self.base:
            return
        screen = self.sidebar.screen
        color = (150, 150, 150)
        last = self.base.pos
        for p in self._preview_points():
            pygame.draw.line(screen, color, last, p, 1)
            pygame.draw.circle(screen, color, (int(p.x), int(p.y)), int(self.radius), 1)
            last = p

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False

        if self.sidebar.visible:
            if self.seg_field.handle_event(event):
                return True
            if self.space_field.handle_event(event):
                return True
            if self.mass_field.handle_event(event):
                return True
            if self.radius_field.handle_event(event):
                return True
            if self.stiff_field.handle_event(event):
                return True
            if self.speed_field.handle_event(event):
                return True
            if self.color_field.handle_event(event):
                return True
            if self.high_field.handle_event(event):
                return True
            if self.adh_field.handle_event(event):
                return True
            if self.key_field.handle_event(event):
                return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.create_rect.collidepoint(event.pos) and self.base:
                    self.app.create_hook_arm(
                        self.base,
                        self.direction,
                        self.segments,
                        self.spacing,
                        self.mass,
                        self.radius,
                        self.stiffness,
                        self.color,
                        self.high_drag_color,
                        self.adhesion_factor,
                        self.cycle_key,
                        self.cycle_speed,
                    )
                    self.cancel()
                    self.sidebar.app.set_mode("drag")
                    return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                mouse = pygame.Vector2(event.pos)
                if not self.base:
                    if self.app.particles:
                        self.base = min(self.app.particles, key=lambda p: (p.pos - mouse).length())
                        self.dragging = True
                        self.direction = pygame.Vector2(1, 0)
                        return True
                else:
                    self.dragging = True
                    return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse = self.app.snap_to_grid(pygame.Vector2(event.pos))
            self.direction = mouse - self.base.pos
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return True

        return False


class InspectTool:
    """Select a particle or spring and edit its properties from the sidebar."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False
        self.particle = None
        self.spring = None
        self.bend = None

        x = sidebar.screen.get_width() - sidebar.WIDTH + 10
        width = sidebar.WIDTH - 20
        y = sidebar.extra_start_y

        self.color_field = ColorField(
            "P Color", lambda: self._get_color(), self._set_color, x, y, width
        )
        y += 40
        self.mass_field = SliderField(
            "P Mass", 0.1, 10.0, lambda: self._get_mass(), self._set_mass, x, y, width
        )
        y += 40
        self.radius_field = SliderField(
            "P Radius", 1, 50, lambda: self._get_radius(), self._set_radius, x, y, width
        )
        y += 40
        self.rest_field = SliderField(
            "S Rest", 1, 400, lambda: self._get_rest(), self._set_rest, x, y, width
        )
        y += 40
        self.stiff_field = SliderField(
            "S Stiff", 10, 1000, lambda: self._get_stiff(), self._set_stiff, x, y, width
        )
        y += 40
        self.max_field = SliderField(
            "S MaxF", 0, 2000, lambda: self._get_max(), self._set_max, x, y, width
        )
        y += 40
        self.bangle_field = SliderField(
            "B Ang", 0, 180, lambda: self._get_bangle(), self._set_bangle, x, y, width
        )
        y += 40
        self.bstiff_field = SliderField(
            "B Stiff", 10, 1000, lambda: self._get_bstiff(), self._set_bstiff, x, y, width
        )
        y += 40
        self.invis_rect = pygame.Rect(x, y, width, SidebarUI.BUTTON_HEIGHT)

    # ---------------- helpers
    def _get_color(self):
        return self.particle.color if self.particle else (255, 255, 255)

    def _set_color(self, color):
        if self.particle:
            self.particle.color = color

    def _get_mass(self):
        return self.particle.mass if self.particle else 0

    def _set_mass(self, value: float):
        if self.particle:
            self.particle.mass = max(0.1, value)

    def _get_radius(self):
        return self.particle.radius if self.particle else 0

    def _set_radius(self, value: float):
        if self.particle:
            self.particle.radius = max(1, int(value))

    def _get_rest(self):
        return self.spring.rest_length if self.spring else 0

    def _set_rest(self, value: float):
        if self.spring:
            self.spring.rest_length = max(1, value)

    def _get_stiff(self):
        return self.spring.stiffness if self.spring else 0

    def _set_stiff(self, value: float):
        if self.spring:
            self.spring.stiffness = max(10, value)

    def _get_bangle(self):
        return math.degrees(self.bend.rest_angle) if self.bend else 0

    def _set_bangle(self, value: float):
        if self.bend:
            self.bend.rest_angle = math.radians(max(0, value))

    def _get_bstiff(self):
        return self.bend.stiffness if self.bend else 0

    def _set_bstiff(self, value: float):
        if self.bend:
            self.bend.stiffness = max(10, value)

    def _get_max(self):
        if not self.spring:
            return 0
        return self.spring.max_force if self.spring.max_force is not None else 0

    def _set_max(self, value: float):
        if self.spring:
            self.spring.max_force = None if value == 0 else value

    def _toggle_invisible(self):
        if self.spring:
            self.spring.invisible = not self.spring.invisible

    # ---------------- control
    def start(self):
        self.active = True
        self.particle = None
        self.spring = None
        self.bend = None

    def cancel(self):
        self.active = False
        self.particle = None
        self.spring = None
        self.bend = None

    # ---------------- drawing
    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        if self.particle:
            self.color_field.draw(self.sidebar.screen)
            self.mass_field.draw(self.sidebar.screen)
            self.radius_field.draw(self.sidebar.screen)
        elif self.spring:
            self.rest_field.draw(self.sidebar.screen)
            self.stiff_field.draw(self.sidebar.screen)
            self.max_field.draw(self.sidebar.screen)
            pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.invis_rect)
            txt = "Invisible" if self.spring.invisible else "Visible"
            img = self.sidebar.font.render(txt, True, (255, 255, 255))
            rect = img.get_rect(center=self.invis_rect.center)
            self.sidebar.screen.blit(img, rect)
        elif self.bend:
            self.bangle_field.draw(self.sidebar.screen)
            self.bstiff_field.draw(self.sidebar.screen)

    def draw_preview(self):
        if not self.active:
            return
        if self.particle:
            pygame.draw.circle(
                self.sidebar.screen,
                (255, 255, 0),
                (int(self.particle.pos.x), int(self.particle.pos.y)),
                int(self.particle.radius) + 4,
                2,
            )
        elif self.spring:
            pygame.draw.line(
                self.sidebar.screen,
                (255, 255, 0),
                self.spring.p1.pos,
                self.spring.p2.pos,
                3,
            )
        elif self.bend:
            pygame.draw.line(
                self.sidebar.screen,
                (255, 255, 0),
                self.bend.p1.pos,
                self.bend.p2.pos,
                3,
            )
            pygame.draw.line(
                self.sidebar.screen,
                (255, 255, 0),
                self.bend.p2.pos,
                self.bend.p3.pos,
                3,
            )

    # ---------------- event handling
    def handle_event(self, event):
        if not self.active:
            return False

        if self.sidebar.visible:
            if self.particle:
                if self.color_field.handle_event(event):
                    return True
                if self.mass_field.handle_event(event):
                    return True
                if self.radius_field.handle_event(event):
                    return True
            elif self.spring:
                if self.rest_field.handle_event(event):
                    return True
                if self.stiff_field.handle_event(event):
                    return True
                if self.max_field.handle_event(event):
                    return True
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.invis_rect.collidepoint(event.pos):
                    self._toggle_invisible()
                    return True
            elif self.bend:
                if self.bangle_field.handle_event(event):
                    return True
                if self.bstiff_field.handle_event(event):
                    return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                mouse = pygame.Vector2(event.pos)
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


class SidebarUI:
    BUTTON_HEIGHT = 28
    BUTTON_MARGIN = 4
    WIDTH = 220
    TOGGLE_SIZE = 20

    def __init__(self, screen: pygame.Surface, app):
        self.screen = screen
        self.app = app
        self.font = pygame.font.SysFont(None, 24)
        self.buttons = []
        self.fields = []
        self.visible = True
        self.circle_tool = None
        self._setup_ui()
        # setup circle tool after computing layout
        self.particle_tool = ParticleTool(self)
        self.spring_tool = SpringTool(self)
        self.bend_tool = BendingSpringTool(self)
        self.circle_tool = CircleTool(self)
        self.rod_tool = RodTool(self)
        self.arm_tool = HookArmTool(self)
        self.grid_tool = GridTool(self)
        self.env_tool = EnvironmentTool(self)
        self.inspect_tool = InspectTool(self)

    # ----------------------------------------------------------- setup
    def _setup_ui(self):
        sw = self.screen.get_width()
        x = sw - self.WIDTH + 10
        y = 10

        def add_button(label, action):
            nonlocal y
            rect = pygame.Rect(x, y, self.WIDTH - 20, self.BUTTON_HEIGHT)
            self.buttons.append({"rect": rect, "label": label, "action": action})
            y += self.BUTTON_HEIGHT + self.BUTTON_MARGIN

        add_button("Drag", lambda: self.app.set_mode("drag"))
        add_button("Particle", lambda: self.app.set_mode("particle"))
        add_button("Spring", lambda: self.app.set_mode("spring"))
        add_button("Bend", lambda: self.app.set_mode("bend"))
        add_button("Circle", lambda: self.app.set_mode("circle"))
        add_button("Rod", lambda: self.app.set_mode("rod"))
        add_button("Arm", lambda: self.app.set_mode("arm"))
        add_button("Inspect", lambda: self.app.set_mode("inspect"))
        add_button("Grid", lambda: self.app.set_mode("grid"))
        add_button("Env", lambda: self.app.set_mode("env"))
        add_button("Delete", lambda: self.app.set_mode("delete"))
        add_button("Save", self.app.save_state_dialog)
        add_button("Load", self.app.load_state_dialog)
        add_button(lambda: "Resume" if self.app.paused else "Pause", self.app.toggle_pause)

        y += 10
        self.extra_start_y = y

    def visible_width(self):
        return self.WIDTH if self.visible else 0

    # ----------------------------------------------------------- draw
    def draw(self):
        sw = self.screen.get_width()
        sidebar_rect = pygame.Rect(sw - self.visible_width(), 0, self.visible_width(), self.screen.get_height())
        toggle_x = sw - self.visible_width() - self.TOGGLE_SIZE
        self.toggle_rect = pygame.Rect(toggle_x, 5, self.TOGGLE_SIZE, self.TOGGLE_SIZE)

        # background
        if self.visible:
            pygame.draw.rect(self.screen, (50, 50, 50), sidebar_rect)

            for btn in self.buttons:
                label = btn["label"]() if callable(btn["label"]) else btn["label"]
                pygame.draw.rect(self.screen, (80, 80, 80), btn["rect"])
                text_img = self.font.render(label, True, (255, 255, 255))
                text_rect = text_img.get_rect(center=btn["rect"].center)
                self.screen.blit(text_img, text_rect)

            for field in self.fields:
                field.draw(self.screen)

            # extra UI from tools
            self.particle_tool.draw_ui()
            self.spring_tool.draw_ui()
            self.bend_tool.draw_ui()
            self.circle_tool.draw_ui()
            self.rod_tool.draw_ui()
            self.arm_tool.draw_ui()
            self.grid_tool.draw_ui()
            self.env_tool.draw_ui()
            self.inspect_tool.draw_ui()

        # preview from tools (visible or not)
        self.particle_tool.draw_preview()
        self.spring_tool.draw_preview()
        self.bend_tool.draw_preview()
        self.circle_tool.draw_preview()
        self.rod_tool.draw_preview()
        self.arm_tool.draw_preview()
        self.grid_tool.draw_preview()
        self.env_tool.draw_preview()
        self.inspect_tool.draw_preview()

        # toggle button (always visible)
        pygame.draw.rect(self.screen, (100, 100, 100), self.toggle_rect)
        arrow = "<" if self.visible else ">"
        img = self.font.render(arrow, True, (255, 255, 255))
        rect = img.get_rect(center=self.toggle_rect.center)
        self.screen.blit(img, rect)

    # ----------------------------------------------------------- event handler
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.toggle_rect.collidepoint(event.pos):
                self.visible = not self.visible
                return True

        if self.visible:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in self.buttons:
                    if btn["rect"].collidepoint(event.pos):
                        btn["action"]()
                        return True

        if self.visible:
            for field in self.fields:
                if field.handle_event(event):
                    return True

        if self.particle_tool.handle_event(event):
            return True
        if self.spring_tool.handle_event(event):
            return True
        if self.bend_tool.handle_event(event):
            return True
        if self.circle_tool.handle_event(event):
            return True
        if self.rod_tool.handle_event(event):
            return True
        if self.arm_tool.handle_event(event):
            return True
        if self.grid_tool.handle_event(event):
            return True
        if self.env_tool.handle_event(event):
            return True
        if self.inspect_tool.handle_event(event):
            return True

        return False
