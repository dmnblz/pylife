"""Sidebar UI managing all builder tools."""

import pygame

from .fonts import get_font
from .tools.particle_tool import ParticleTool
from .tools.spring_tool import SpringTool
from .tools.variable_spring_tool import VariableSpringTool
from .tools.variable_particle_tool import VariableParticleTool
from .tools.variable_bending_spring_tool import VariableBendingSpringTool
from .tools.bending_spring_tool import BendingSpringTool
from .tools.grid_tool import GridTool
from .tools.environment_tool import EnvironmentTool
from .tools.circle_tool import CircleTool
from .tools.rod_tool import RodTool
from .tools.hook_arm_tool import HookArmTool
from .tools.sensor_tool import SensorTool
from .tools.inspect_tool import InspectTool
from . import theme


class SidebarUI:
    BUTTON_HEIGHT = 28
    BUTTON_MARGIN = 4
    WIDTH = 220
    TOGGLE_SIZE = 20

    def __init__(self, screen: pygame.Surface, app):
        """Create the sidebar UI and all tool instances.

        Parameters
        ----------
        screen:
            Surface used for rendering.
        app:
            Owning :class:`~start_create.BuilderApp`.
        """

        self.screen = screen
        self.app = app
        self.font = get_font(24)
        self.buttons = []
        self.fields = []
        self.visible = True
        self.scroll_offset = 0
        self.circle_tool = None
        self._setup_ui()
        # setup circle tool after computing layout
        self.particle_tool = ParticleTool(self)
        self.variable_particle_tool = VariableParticleTool(self)
        self.spring_tool = SpringTool(self)
        self.variable_spring_tool = VariableSpringTool(self)
        self.variable_bend_tool = VariableBendingSpringTool(self)
        self.bend_tool = BendingSpringTool(self)
        self.circle_tool = CircleTool(self)
        self.rod_tool = RodTool(self)
        self.arm_tool = HookArmTool(self)
        self.sensor_tool = SensorTool(self)
        self.grid_tool = GridTool(self)
        self.env_tool = EnvironmentTool(self)
        self.inspect_tool = InspectTool(self)

    # ----------------------------------------------------------- setup
    def _setup_ui(self):
        """Create default buttons and compute layout offsets."""

        sw = self.screen.get_width()
        x = sw - self.WIDTH + 10
        y = 10

        def add_button(label, action, key_hint: str | None = None, mode: str | None = None):
            """Add a clickable button to the sidebar.

            Parameters
            ----------
            label:
                Text to display on the button.
            action:
                Callback executed on click.
            key_hint:
                Optional short string shown on the button to indicate a
                keyboard shortcut.
            mode:
                Optional builder mode associated with this button. The
                button highlights while active.
            """

            nonlocal y
            rect = pygame.Rect(x, y, self.WIDTH - 20, self.BUTTON_HEIGHT)
            self.buttons.append(
                {
                    "rect": rect,
                    "label": label,
                    "action": action,
                    "key": key_hint,
                    "mode": mode,
                    "pressed": 0,
                }
            )
            y += self.BUTTON_HEIGHT + self.BUTTON_MARGIN

        add_button("Drag", lambda: self.app.set_mode("drag"), "1", "drag")
        add_button("Select", lambda: self.app.set_mode("select"), "Ctrl+S", "select")
        add_button("Particle", lambda: self.app.set_mode("particle"), "2", "particle")
        add_button("VarPar", lambda: self.app.set_mode("vparticle"), mode="vparticle")
        add_button("Spring", lambda: self.app.set_mode("spring"), "3", "spring")
        add_button("VarSpr", lambda: self.app.set_mode("vspring"), mode="vspring")
        add_button("Bend", lambda: self.app.set_mode("bend"), "4", "bend")
        add_button("VarBend", lambda: self.app.set_mode("vbend"), mode="vbend")
        add_button("Circle", lambda: self.app.set_mode("circle"), "5", "circle")
        add_button("Rod", lambda: self.app.set_mode("rod"), "6", "rod")
        add_button("Arm", lambda: self.app.set_mode("arm"), "7", "arm")
        add_button("Sensor", lambda: self.app.set_mode("sensor"), mode="sensor")
        add_button("Inspect", lambda: self.app.set_mode("inspect"), "8", "inspect")
        add_button("Events", self.app.open_events_modal, None, None)
        add_button("Grid", lambda: self.app.set_mode("grid"), "9", "grid")
        add_button("Env", lambda: self.app.set_mode("env"), "0", "env")
        add_button("Delete", lambda: self.app.set_mode("delete"), "Del", "delete")
        add_button("Undo", self.app.undo)
        add_button("Save", self.app.save_state_dialog)
        add_button("Load", self.app.load_state_dialog)
        add_button(lambda: "Light" if self.app.theme_name == "dark" else "Dark", self.app.toggle_theme)
        add_button(lambda: "Resume" if self.app.paused else "Pause", self.app.toggle_pause, "Space")

        y += 10
        self.extra_start_y = y

    def visible_width(self):
        """Return the width of the sidebar when visible."""
        return self.WIDTH if self.visible else 0

    # ----------------------------------------------------------- scrolling helpers
    def _rect_bottom(self, obj) -> int:
        """Return the maximum bottom coordinate of ``pygame.Rect`` attrs."""
        bottom = 0
        for val in getattr(obj, "__dict__", {}).values():
            if isinstance(val, pygame.Rect):
                bottom = max(bottom, val.bottom)
        return bottom

    def _tool_bottom(self, tool) -> int:
        """Return the lowest UI element used by ``tool``."""
        bottom = 0
        for val in vars(tool).values():
            if isinstance(val, (list, tuple)):
                for item in val:
                    bottom = max(bottom, self._rect_bottom(item))
            else:
                bottom = max(bottom, self._rect_bottom(val))
        return bottom

    def _content_bottom(self) -> int:
        """Compute the bottom edge of all sidebar content."""
        bottoms = [btn["rect"].bottom for btn in self.buttons]
        bottoms += [self._rect_bottom(f) for f in self.fields]
        tools = [
            self.particle_tool,
            self.variable_particle_tool,
            self.spring_tool,
            self.variable_spring_tool,
            self.bend_tool,
            self.variable_bend_tool,
            self.circle_tool,
            self.rod_tool,
            self.arm_tool,
            self.sensor_tool,
            self.grid_tool,
            self.env_tool,
            self.inspect_tool,
        ]
        bottoms += [self._tool_bottom(t) for t in tools]
        return max(bottoms, default=0) + 10

    def _clamp_scroll(self) -> None:
        """Limit ``scroll_offset`` to the available content range."""
        max_offset = min(0, self.screen.get_height() - self._content_bottom())
        self.scroll_offset = max(max_offset, min(0, self.scroll_offset))

    # ----------------------------------------------------------- draw
    def draw(self):
        """Render the sidebar and active tool interfaces."""
        sw = self.screen.get_width()
        sidebar_rect = pygame.Rect(sw - self.visible_width(), 0, self.visible_width(), self.screen.get_height())
        toggle_x = sw - self.visible_width() - self.TOGGLE_SIZE
        self.toggle_rect = pygame.Rect(toggle_x, 5, self.TOGGLE_SIZE, self.TOGGLE_SIZE)

        # background
        if self.visible:
            # panel background
            pygame.draw.rect(self.screen, theme.BG_SIDEBAR, sidebar_rect, border_radius=theme.RADIUS)

            now = pygame.time.get_ticks()
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.buttons:
                rect = btn["rect"].move(0, self.scroll_offset)
                label = btn["label"]() if callable(btn["label"]) else btn["label"]
                hint = btn.get("key")
                base = theme.BG_BUTTON
                if btn.get("mode") == self.app.mode:
                    base = theme.BG_BUTTON_ACTIVE
                if rect.collidepoint(mouse_pos):
                    base = theme.BG_BUTTON_HOVER
                if now - btn.get("pressed", 0) < 150:
                    base = theme.BG_BUTTON_HOVER
                pygame.draw.rect(self.screen, base, rect, border_radius=theme.RADIUS)
                # label left
                text_img = self.font.render(str(label), True, theme.TEXT)
                self.screen.blit(text_img, text_img.get_rect(midleft=(rect.x + 10, rect.centery)))
                # keycap right
                if hint:
                    cap_img = self.font.render(hint, True, theme.TEXT)
                    cap_rect = cap_img.get_rect(midright=(rect.right - 8, rect.centery))
                    pygame.draw.rect(self.screen, theme.BORDER, cap_rect.inflate(12, 6), border_radius=6)
                    self.screen.blit(cap_img, cap_rect)

            for field in self.fields:
                field.draw(self.screen, self.scroll_offset)

            # extra UI from tools
            self.particle_tool.draw_ui(self.scroll_offset)
            self.variable_particle_tool.draw_ui(self.scroll_offset)
            self.spring_tool.draw_ui(self.scroll_offset)
            self.variable_spring_tool.draw_ui(self.scroll_offset)
            self.variable_bend_tool.draw_ui(self.scroll_offset)
            self.bend_tool.draw_ui(self.scroll_offset)
            self.circle_tool.draw_ui(self.scroll_offset)
            self.rod_tool.draw_ui(self.scroll_offset)
            self.arm_tool.draw_ui(self.scroll_offset)
            self.sensor_tool.draw_ui(self.scroll_offset)
            self.grid_tool.draw_ui(self.scroll_offset)
            self.env_tool.draw_ui(self.scroll_offset)
            self.inspect_tool.draw_ui(self.scroll_offset)

        # preview from tools (visible or not)
        self.particle_tool.draw_preview()
        self.spring_tool.draw_preview()
        self.variable_spring_tool.draw_preview()
        self.variable_bend_tool.draw_preview()
        self.bend_tool.draw_preview()
        self.circle_tool.draw_preview()
        self.rod_tool.draw_preview()
        self.arm_tool.draw_preview()
        self.grid_tool.draw_preview()
        self.env_tool.draw_preview()
        self.inspect_tool.draw_preview()

        # toggle button (always visible)
        pygame.draw.rect(self.screen, theme.BORDER, self.toggle_rect, border_radius=theme.RADIUS)
        arrow = "<" if self.visible else ">"
        img = self.font.render(arrow, True, theme.TEXT)
        rect = img.get_rect(center=self.toggle_rect.center)
        self.screen.blit(img, rect)

    # ----------------------------------------------------------- event handler
    def handle_event(self, event):
        """Forward events to the sidebar and active tools.

        Parameters
        ----------
        event:
            Pygame event to process.

        Returns
        -------
        bool
            ``True`` if the event was consumed.
        """

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.toggle_rect.collidepoint(event.pos):
                self.visible = not self.visible
                return True

        # Only scroll sidebar if the mouse is over the sidebar area
        if event.type == pygame.MOUSEWHEEL:
            if self.visible:
                mx, my = pygame.mouse.get_pos()
                if mx >= self.screen.get_width() - self.visible_width():
                    self.scroll_offset += event.y * 20
                    self._clamp_scroll()
                    return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            if self.visible:
                mx, my = event.pos
                if mx >= self.screen.get_width() - self.visible_width():
                    self.scroll_offset += 20 if event.button == 4 else -20
                    self._clamp_scroll()
                    return True

        if self.visible:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for btn in self.buttons:
                    rect = btn["rect"].move(0, self.scroll_offset)
                    if rect.collidepoint(event.pos):
                        btn["action"]()
                        btn["pressed"] = pygame.time.get_ticks()
                        return True

        if self.visible:
            for field in self.fields:
                if field.handle_event(event, self.scroll_offset):
                    return True

        if self.particle_tool.handle_event(event, self.scroll_offset):
            return True
        if self.variable_particle_tool.handle_event(event, self.scroll_offset):
            return True
        if self.spring_tool.handle_event(event, self.scroll_offset):
            return True
        if self.variable_spring_tool.handle_event(event, self.scroll_offset):
            return True
        if self.variable_bend_tool.handle_event(event, self.scroll_offset):
            return True
        if self.bend_tool.handle_event(event, self.scroll_offset):
            return True
        if self.circle_tool.handle_event(event, self.scroll_offset):
            return True
        if self.rod_tool.handle_event(event, self.scroll_offset):
            return True
        if self.arm_tool.handle_event(event, self.scroll_offset):
            return True
        if self.sensor_tool.handle_event(event, self.scroll_offset):
            return True
        if self.grid_tool.handle_event(event, self.scroll_offset):
            return True
        if self.env_tool.handle_event(event, self.scroll_offset):
            return True
        if self.inspect_tool.handle_event(event, self.scroll_offset):
            return True

        return False
