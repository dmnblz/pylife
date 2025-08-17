"""Popup listing multiple selected objects for inspection."""

from __future__ import annotations

import pygame

from . import theme


class SelectionMenu:
    """Simple menu listing selected particles, springs and bends."""

    ITEM_HEIGHT = 24
    PADDING = 6

    def __init__(
        self,
        app,
        particles,
        springs,
        bends,
    ) -> None:
        """Prepare menu entries from the current selection."""

        self.app = app
        self.font = pygame.font.SysFont(None, 22)
        self.items: list[dict] = []
        labels: list[tuple[str, object, str]] = []
        for i, p in enumerate(particles, 1):
            labels.append((f"Particle {i}", p, "particle"))
        for i, s in enumerate(springs, 1):
            labels.append((f"Spring {i}", s, "spring"))
        for i, b in enumerate(bends, 1):
            labels.append((f"Bend {i}", b, "bend"))
        width = 0
        for label, obj, kind in labels:
            img = self.font.render(label, True, theme.TEXT)
            width = max(width, img.get_width())
        width += self.PADDING * 2
        height = self.PADDING * 2 + self.ITEM_HEIGHT * len(labels)
        self.rect = pygame.Rect(10, 10, width, height)
        y = self.rect.y + self.PADDING
        for label, obj, kind in labels:
            rect = pygame.Rect(
                self.rect.x + self.PADDING,
                y,
                width - self.PADDING * 2,
                self.ITEM_HEIGHT,
            )
            self.items.append({"rect": rect, "label": label, "obj": obj, "kind": kind})
            y += self.ITEM_HEIGHT

    def draw(self, screen: pygame.Surface) -> None:
        """Render the popup menu."""

        pygame.draw.rect(screen, theme.BG_SIDEBAR, self.rect, border_radius=theme.RADIUS)
        for item in self.items:
            rect = item["rect"]
            color = theme.BG_BUTTON
            if rect.collidepoint(pygame.mouse.get_pos()):
                color = theme.BG_BUTTON_HOVER
            pygame.draw.rect(screen, color, rect, border_radius=theme.RADIUS)
            img = self.font.render(item["label"], True, theme.TEXT)
            screen.blit(img, img.get_rect(center=rect.center))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process input events for the menu."""

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.rect.collidepoint(event.pos):
                self.app.selection_menu = None
                return True
            for item in self.items:
                if item["rect"].collidepoint(event.pos):
                    self._choose(item["obj"], item["kind"])
                    return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.selection_menu = None
            return True
        return False

    def _choose(self, obj, kind: str) -> None:
        """Inspect the chosen object and close the popup."""

        tool = self.app.ui.inspect_tool
        tool.particle = None
        tool.spring = None
        tool.bend = None
        if kind == "particle":
            tool.particle = obj
        elif kind == "spring":
            tool.spring = obj
        else:
            tool.bend = obj
        self.app.set_mode("inspect")
        self.app.selection_menu = None
