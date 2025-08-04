"""Sidebar input widgets such as sliders, colour selectors and key fields."""

from typing import Callable

import pygame
from color_picker import choose_color


class SliderField:
    """A simple horizontal slider with an editable numeric field."""

    BOX_WIDTH = 50

    def __init__(
        self,
        label: str,
        min_val: float,
        max_val: float,
        get_value: Callable[[], float],
        set_value: Callable[[float], None],
        x: int,
        y: int,
        width: int,
    ):
        """Initialise a new slider widget.

        Parameters
        ----------
        label:
            Text label displayed above the slider.
        min_val, max_val:
            Range of selectable values.
        get_value:
            Callable returning the current value.
        set_value:
            Callable used to update the value.
        x, y, width:
            Position and width of the slider in pixels.
        """

        self.label = label
        self.min = min_val
        self.max = max_val
        self.get_value: Callable[[], float] = get_value
        self.set_value: Callable[[float], None] = set_value
        self.font = pygame.font.SysFont(None, 22)

        slider_width = width - self.BOX_WIDTH - 10
        self.slider_rect = pygame.Rect(x, y + 18, slider_width, 6)
        self.box_rect = pygame.Rect(self.slider_rect.right + 5, y + 10, self.BOX_WIDTH, 22)

        self.dragging = False
        self.editing = False
        self.text = ""

    def _value_to_ratio(self, value):
        """Map ``value`` onto the 0–1 slider range.

        Parameters
        ----------
        value:
            Value within ``[self.min, self.max]``.

        Returns
        -------
        float
            Normalised ratio representing the slider position.
        """

        return max(0, min(1, (value - self.min) / (self.max - self.min)))

    def _ratio_to_value(self, ratio):
        """Convert a slider ratio back into a value.

        Parameters
        ----------
        ratio:
            Normalised position between 0 and 1.

        Returns
        -------
        float
            Value corresponding to ``ratio``.
        """

        return self.min + ratio * (self.max - self.min)

    def draw(self, screen, offset: int = 0):
        """Render the slider and its numeric field.

        Parameters
        ----------
        screen:
            Surface on which to draw.
        offset:
            Vertical pixel offset applied for scrolling.

        Returns
        -------
        None
        """

        value = self.get_value()
        slider_rect = self.slider_rect.move(0, offset)
        box_rect = self.box_rect.move(0, offset)

        # label
        lbl = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(lbl, (slider_rect.x, slider_rect.y - 18))

        # slider track
        pygame.draw.rect(screen, (80, 80, 80), slider_rect)
        knob_x = int(slider_rect.x + self._value_to_ratio(value) * slider_rect.width)
        pygame.draw.rect(screen, (180, 180, 180), (knob_x - 3, slider_rect.y - 4, 6, slider_rect.height + 8))

        # textbox
        pygame.draw.rect(screen, (255, 255, 255), box_rect, 1)
        txt = self.text if self.editing else f"{value:.2f}"
        img = self.font.render(txt, True, (255, 255, 255))
        rect = img.get_rect(center=box_rect.center)
        screen.blit(img, rect)

    def handle_event(self, event, offset: int = 0):
        """Process input events for the slider.

        Parameters
        ----------
        event:
            Pygame event to handle.
        offset:
            Vertical pixel offset applied for scrolling.

        Returns
        -------
        bool
            ``True`` if the event was consumed.
        """

        slider_rect = self.slider_rect.move(0, offset)
        box_rect = self.box_rect.move(0, offset)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if slider_rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value(event.pos[0])
                return True
            if box_rect.collidepoint(event.pos):
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
        """Update the stored value from the mouse position.

        Parameters
        ----------
        mouse_x:
            Horizontal mouse coordinate in pixels.

        Returns
        -------
        None
        """

        ratio = (mouse_x - self.slider_rect.x) / self.slider_rect.width
        ratio = max(0, min(1, ratio))
        self.set_value(self._ratio_to_value(ratio))


class ColorField:
    """Field allowing the user to pick a colour or enter a hex value."""

    BOX_WIDTH = 70
    COLOR_SIZE = 24

    def __init__(
        self,
        label: str,
        get_color: Callable[[], tuple[int, int, int]],
        set_color: Callable[[tuple[int, int, int]], None],
        x: int,
        y: int,
        width: int,
    ):
        """Initialise a colour selection field.

        Parameters
        ----------
        label:
            Text displayed above the field.
        get_color, set_color:
            Callables for retrieving and storing the colour.
        x, y, width:
            Position and width in pixels.
        """

        self.label = label
        self.get_color: Callable[[], tuple[int, int, int]] = get_color
        self.set_color: Callable[[tuple[int, int, int]], None] = set_color
        self.font = pygame.font.SysFont(None, 22)

        self.color_rect = pygame.Rect(x, y + 14, self.COLOR_SIZE, self.COLOR_SIZE)
        self.box_rect = pygame.Rect(
            self.color_rect.right + 5, y + 10, self.BOX_WIDTH, 22
        )

        self.editing = False
        self.text = ""

    def draw(self, screen, offset: int = 0):
        """Render the colour swatch and hex entry box.

        Parameters
        ----------
        screen:
            Surface on which to draw.
        offset:
            Vertical pixel offset applied for scrolling.

        Returns
        -------
        None
        """

        color = self.get_color()
        color_rect = self.color_rect.move(0, offset)
        box_rect = self.box_rect.move(0, offset)
        lbl = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(lbl, (color_rect.x, color_rect.y - 18))

        pygame.draw.rect(screen, color, color_rect)
        pygame.draw.rect(screen, (255, 255, 255), color_rect, 1)

        pygame.draw.rect(screen, (255, 255, 255), box_rect, 1)
        txt = self.text if self.editing else "#%02X%02X%02X" % color
        img = self.font.render(txt, True, (255, 255, 255))
        rect = img.get_rect(center=box_rect.center)
        screen.blit(img, rect)

    def handle_event(self, event, offset: int = 0):
        """Process user input for the colour field.

        Parameters
        ----------
        event:
            Pygame event to handle.
        offset:
            Vertical pixel offset applied for scrolling.

        Returns
        -------
        bool
            ``True`` if the event was consumed.
        """

        color_rect = self.color_rect.move(0, offset)
        box_rect = self.box_rect.move(0, offset)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if color_rect.collidepoint(event.pos):
                self._choose_color()
                return True
            if box_rect.collidepoint(event.pos):
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
        """Parse ``value`` as ``#RRGGBB`` and update the colour.

        Parameters
        ----------
        value:
            Hexadecimal colour string.

        Returns
        -------
        None
        """

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

    def __init__(
        self,
        label: str,
        get_key: Callable[[], int | None],
        set_key: Callable[[int | None], None],
        x: int,
        y: int,
        width: int,
    ):
        """Create an editable key field.

        Parameters
        ----------
        label:
            Text displayed above the field.
        get_key, set_key:
            Callables for retrieving and storing the key.
        x, y, width:
            Position and width in pixels.
        """

        self.label = label
        self.get_key: Callable[[], int | None] = get_key
        self.set_key: Callable[[int | None], None] = set_key
        self.font = pygame.font.SysFont(None, 22)

        self.box_rect = pygame.Rect(x, y + 10, self.BOX_WIDTH, 22)
        self.editing = False

    def draw(self, screen, offset: int = 0):
        """Render the key field.

        Parameters
        ----------
        screen:
            Surface on which to draw.
        offset:
            Vertical pixel offset applied for scrolling.

        Returns
        -------
        None
        """

        key = self.get_key()
        text = pygame.key.name(key) if key is not None else "None"
        if self.editing:
            text = f"[{text}]"

        box_rect = self.box_rect.move(0, offset)
        lbl = self.font.render(self.label, True, (255, 255, 255))
        screen.blit(lbl, (box_rect.x, box_rect.y - 18))
        pygame.draw.rect(screen, (255, 255, 255), box_rect, 1)
        img = self.font.render(text, True, (255, 255, 255))
        rect = img.get_rect(center=box_rect.center)
        screen.blit(img, rect)

    def handle_event(self, event, offset: int = 0):
        """Handle mouse and keyboard input.

        Parameters
        ----------
        event:
            Pygame event to process.
        offset:
            Vertical pixel offset applied for scrolling.

        Returns
        -------
        bool
            ``True`` if the event was consumed.
        """

        box_rect = self.box_rect.move(0, offset)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if box_rect.collidepoint(event.pos):
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


class ButtonField:
    """Simple clickable button with pressed and active states."""

    HEIGHT = 28

    def __init__(
        self,
        label: str | Callable[[], str],
        action: Callable[[], None],
        x: int,
        y: int,
        width: int,
        active: Callable[[], bool] | bool = False,
    ) -> None:
        """Create a button field.

        Parameters
        ----------
        label:
            Text displayed on the button or a callable returning it.
        action:
            Callback executed when the button is clicked.
        x, y, width:
            Position and width of the button.
        active:
            Optional boolean or callable indicating whether the button is in
            an active/toggled state.
        """

        self.label = label
        self.action = action
        self.active = active
        self.rect = pygame.Rect(x, y, width, self.HEIGHT)
        self.font = pygame.font.SysFont(None, 24)
        self.pressed = 0

    def draw(self, screen, offset: int = 0) -> None:
        """Render the button.

        Parameters
        ----------
        screen:
            Surface on which to draw.
        offset:
            Vertical pixel offset applied for scrolling.
        """

        rect = self.rect.move(0, offset)
        label = self.label() if callable(self.label) else self.label
        color = (80, 80, 80)
        active = self.active() if callable(self.active) else self.active
        if active:
            color = (120, 120, 120)
        if pygame.time.get_ticks() - self.pressed < 150:
            color = (60, 60, 60)
        pygame.draw.rect(screen, color, rect)
        img = self.font.render(label, True, (255, 255, 255))
        screen.blit(img, img.get_rect(center=rect.center))

    def handle_event(self, event, offset: int = 0) -> bool:
        """Handle mouse clicks on the button.

        Parameters
        ----------
        event:
            Pygame event to process.
        offset:
            Vertical pixel offset applied for scrolling.

        Returns
        -------
        bool
            ``True`` if the event was consumed.
        """

        rect = self.rect.move(0, offset)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if rect.collidepoint(event.pos):
                self.action()
                self.pressed = pygame.time.get_ticks()
                return True
        return False
