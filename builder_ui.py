import pygame
import math
from color_picker import choose_color


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
        self.create_rect = pygame.Rect(x, y, width, SidebarUI.BUTTON_HEIGHT)

    # ---------------- value setters
    def _set_radius(self, value: float):
        self.radius = max(1, value)

    def _set_segments(self, value: float):
        self.segments = max(3, int(value))

    # ---------------- control
    def start(self):
        self.active = True
        self.center = None

    def cancel(self):
        self.active = False
        self.dragging = False

    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        self.radius_field.draw(self.sidebar.screen)
        self.segments_field.draw(self.sidebar.screen)
        pygame.draw.rect(self.sidebar.screen, (80, 80, 80), self.create_rect)
        txt = self.sidebar.font.render("Create", True, (255, 255, 255))
        rect = txt.get_rect(center=self.create_rect.center)
        self.sidebar.screen.blit(txt, rect)

    def draw_preview(self):
        if not self.active or self.center is None:
            return
        screen = self.sidebar.screen
        color = (150, 150, 150)
        center = (int(self.center.x), int(self.center.y))
        pygame.draw.circle(screen, color, center, int(self.radius), 1)
        for i in range(self.segments):
            theta1 = (i / self.segments) * 2 * math.pi
            theta2 = ((i + 1) % self.segments) / self.segments * 2 * math.pi
            p1 = self.center + pygame.Vector2(math.cos(theta1), math.sin(theta1)) * self.radius
            p2 = self.center + pygame.Vector2(math.cos(theta2), math.sin(theta2)) * self.radius
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
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.create_rect.collidepoint(event.pos) and self.center:
                    self.app.create_circle(self.center, self.radius, self.segments)
                    self.cancel()
                    self.sidebar.app.set_mode("drag")
                    return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # click in world area to set center
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                self.center = pygame.Vector2(event.pos)
                self.dragging = True
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.radius = (pygame.Vector2(event.pos) - self.center).length()
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
            pts.append(pos)
        return pts

    # ---------------- drawing
    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        self.radius_field.draw(self.sidebar.screen)
        self.length_field.draw(self.sidebar.screen)
        self.segments_field.draw(self.sidebar.screen)
        self.skel_count_field.draw(self.sidebar.screen)
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
                    )
                    self.cancel()
                    self.sidebar.app.set_mode("drag")
                    return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                self.center = pygame.Vector2(event.pos)
                self.dragging = True
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.length = abs(event.pos[0] - self.center.x) * 2
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
            return True

        return False


class HookArmTool:
    """Preview and creation helper for :class:`HookArm` instances."""

    def __init__(self, sidebar: 'SidebarUI'):
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False
        self.base = None
        self.direction = pygame.Vector2(1, 0)
        self.segments = 3
        self.spacing = 20.0
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
        self.key_field = KeyField("Cycle", lambda: self.cycle_key, self._set_key, x, y, width)
        y += 40
        self.create_rect = pygame.Rect(x, y, width, SidebarUI.BUTTON_HEIGHT)

    # ---------------- value setters
    def _set_segments(self, value: float):
        self.segments = max(1, int(value))

    def _set_spacing(self, value: float):
        self.spacing = max(1, value)

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
            pts.append(pos)
        return pts

    def draw_ui(self):
        if not self.active or not self.sidebar.visible:
            return
        self.seg_field.draw(self.sidebar.screen)
        self.space_field.draw(self.sidebar.screen)
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
            pygame.draw.circle(screen, color, (int(p.x), int(p.y)), self.app.radius, 1)
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
            if self.key_field.handle_event(event):
                return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.create_rect.collidepoint(event.pos) and self.base:
                    self.app.create_hook_arm(
                        self.base,
                        self.direction,
                        self.segments,
                        self.spacing,
                        self.cycle_key,
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
            self.direction = pygame.Vector2(event.pos) - self.base.pos
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging:
            self.dragging = False
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
        self.circle_tool = CircleTool(self)
        self.rod_tool = RodTool(self)
        self.arm_tool = HookArmTool(self)

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
        add_button("Circle", lambda: self.app.set_mode("circle"))
        add_button("Rod", lambda: self.app.set_mode("rod"))
        add_button("Arm", lambda: self.app.set_mode("arm"))
        add_button("Delete", lambda: self.app.set_mode("delete"))
        add_button(lambda: "Resume" if self.app.paused else "Pause", self.app.toggle_pause)

        # sliders
        slider_x = sw - self.WIDTH + 10
        slider_width = self.WIDTH - 20
        y += 10
        color_field = ColorField(
            "Color", lambda: self.app.color, self.app.set_color, slider_x, y, slider_width
        )
        self.fields.append(color_field)
        y += 40
        self.fields.append(
            SliderField("Mass", 0.1, 10.0, lambda: self.app.mass, self.app.set_mass, slider_x, y, slider_width)
        )
        y += 40
        self.fields.append(
            SliderField("Radius", 1, 50, lambda: self.app.radius, self.app.set_radius, slider_x, y, slider_width)
        )
        y += 40
        self.fields.append(
            SliderField(
                "Stiff", 10, 1000, lambda: self.app.stiffness, self.app.set_stiffness, slider_x, y, slider_width
            )
        )
        y += 40
        self.fields.append(
            SliderField(
                "Temp", 0, 1000, lambda: self.app.physics.temperature, self.app.set_temperature, slider_x, y, slider_width
            )
        )
        y += 40
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
            self.circle_tool.draw_ui()
            self.rod_tool.draw_ui()
            self.arm_tool.draw_ui()

        # preview from tools (visible or not)
        self.circle_tool.draw_preview()
        self.rod_tool.draw_preview()
        self.arm_tool.draw_preview()

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

        if self.circle_tool.handle_event(event):
            return True
        if self.rod_tool.handle_event(event):
            return True
        if self.arm_tool.handle_event(event):
            return True

        return False
