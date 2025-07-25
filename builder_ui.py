import pygame


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
        self._setup_ui()

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
        add_button("Delete", lambda: self.app.set_mode("delete"))
        add_button("Cycle Color", self.app.cycle_color)
        add_button(lambda: "Resume" if self.app.paused else "Pause", self.app.toggle_pause)

        # sliders
        slider_x = sw - self.WIDTH + 10
        slider_width = self.WIDTH - 20
        y += 10
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

        return False
