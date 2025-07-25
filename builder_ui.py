import pygame

class SidebarUI:
    BUTTON_HEIGHT = 28
    BUTTON_MARGIN = 4
    WIDTH = 220

    def __init__(self, screen: pygame.Surface, app):
        self.screen = screen
        self.app = app
        self.font = pygame.font.SysFont(None, 24)
        self.buttons = []
        self._setup_buttons()

    # ----------------------------------------------------------- setup
    def _setup_buttons(self):
        x = self.screen.get_width() - self.WIDTH + 10
        y = 10

        def add(label, action):
            nonlocal y
            rect = pygame.Rect(x, y, self.WIDTH - 20, self.BUTTON_HEIGHT)
            self.buttons.append({"rect": rect, "label": label, "action": action})
            y += self.BUTTON_HEIGHT + self.BUTTON_MARGIN

        add("Drag", lambda: self.app.set_mode("drag"))
        add("Particle", lambda: self.app.set_mode("particle"))
        add("Spring", lambda: self.app.set_mode("spring"))
        add("Delete", lambda: self.app.set_mode("delete"))
        add("Cycle Color", self.app.cycle_color)
        add("Mass -", lambda: self.app.adjust_mass(-0.1))
        add("Mass +", lambda: self.app.adjust_mass(0.1))
        add("Radius -", lambda: self.app.adjust_radius(-1))
        add("Radius +", lambda: self.app.adjust_radius(1))
        add("Stiff -", lambda: self.app.adjust_stiffness(-10))
        add("Stiff +", lambda: self.app.adjust_stiffness(10))
        add("Temp -", lambda: self.app.adjust_temperature(-10))
        add("Temp +", lambda: self.app.adjust_temperature(10))
        add(lambda: "Resume" if self.app.paused else "Pause", self.app.toggle_pause)

    # ----------------------------------------------------------- draw
    def draw(self):
        sidebar_rect = pygame.Rect(
            self.screen.get_width() - self.WIDTH, 0, self.WIDTH, self.screen.get_height()
        )
        pygame.draw.rect(self.screen, (50, 50, 50), sidebar_rect)

        for btn in self.buttons:
            label = btn["label"]() if callable(btn["label"]) else btn["label"]
            pygame.draw.rect(self.screen, (80, 80, 80), btn["rect"])
            text_img = self.font.render(label, True, (255, 255, 255))
            text_rect = text_img.get_rect(center=btn["rect"].center)
            self.screen.blit(text_img, text_rect)

        info_lines = [
            f"Mode: {self.app.mode}",
            f"Mass: {self.app.mass:.1f}",
            f"Radius: {self.app.radius}",
            f"Stiffness: {int(self.app.stiffness)}",
            f"Temperature: {int(self.app.physics.temperature)}",
        ]
        for i, text in enumerate(info_lines):
            img = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(img, (sidebar_rect.x + 10, sidebar_rect.y + 300 + i * 20))

    # ----------------------------------------------------------- event handler
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn["rect"].collidepoint(event.pos):
                    btn["action"]()
                    return True
        return False
