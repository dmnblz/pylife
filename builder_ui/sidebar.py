"""Sidebar UI managing all builder tools."""

import pygame

from .tools.particle_tool import ParticleTool
from .tools.spring_tool import SpringTool
from .tools.bending_spring_tool import BendingSpringTool
from .tools.grid_tool import GridTool
from .tools.environment_tool import EnvironmentTool
from .tools.circle_tool import CircleTool
from .tools.rod_tool import RodTool
from .tools.hook_arm_tool import HookArmTool
from .tools.inspect_tool import InspectTool


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
        """Create default buttons and compute layout offsets."""

        sw = self.screen.get_width()
        x = sw - self.WIDTH + 10
        y = 10

        def add_button(label, action, key_hint: str | None = None):
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
            """

            nonlocal y
            rect = pygame.Rect(x, y, self.WIDTH - 20, self.BUTTON_HEIGHT)
            self.buttons.append(
                {"rect": rect, "label": label, "action": action, "key": key_hint}
            )
            y += self.BUTTON_HEIGHT + self.BUTTON_MARGIN

        add_button("Drag", lambda: self.app.set_mode("drag"), "1")
        add_button("Particle", lambda: self.app.set_mode("particle"), "2")
        add_button("Spring", lambda: self.app.set_mode("spring"), "3")
        add_button("Bend", lambda: self.app.set_mode("bend"), "4")
        add_button("Circle", lambda: self.app.set_mode("circle"), "5")
        add_button("Rod", lambda: self.app.set_mode("rod"), "6")
        add_button("Arm", lambda: self.app.set_mode("arm"), "7")
        add_button("Inspect", lambda: self.app.set_mode("inspect"), "8")
        add_button("Grid", lambda: self.app.set_mode("grid"), "9")
        add_button("Env", lambda: self.app.set_mode("env"), "0")
        add_button("Delete", lambda: self.app.set_mode("delete"), "Del")
        add_button("Undo", self.app.undo)
        add_button("Save", self.app.save_state_dialog)
        add_button("Load", self.app.load_state_dialog)
        add_button(lambda: "Resume" if self.app.paused else "Pause", self.app.toggle_pause)

        y += 10
        self.extra_start_y = y

    def visible_width(self):
        """Return the width of the sidebar when visible."""
        return self.WIDTH if self.visible else 0

    # ----------------------------------------------------------- draw
    def draw(self):
        """Render the sidebar and active tool interfaces."""
        sw = self.screen.get_width()
        sidebar_rect = pygame.Rect(sw - self.visible_width(), 0, self.visible_width(), self.screen.get_height())
        toggle_x = sw - self.visible_width() - self.TOGGLE_SIZE
        self.toggle_rect = pygame.Rect(toggle_x, 5, self.TOGGLE_SIZE, self.TOGGLE_SIZE)

        # background
        if self.visible:
            pygame.draw.rect(self.screen, (50, 50, 50), sidebar_rect)

            for btn in self.buttons:
                label = btn["label"]() if callable(btn["label"]) else btn["label"]
                hint = btn.get("key")
                if hint:
                    label = f"{label} [{hint}]"
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
