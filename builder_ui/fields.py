"""Sidebar input widgets such as sliders, colour selectors and key fields."""

import pygame
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
    """Field allowing the user to pick a colour or enter a hex value."""

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
        """Launch the colour picker in a separate process."""
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
