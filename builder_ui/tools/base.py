"""Common interface for sidebar tools.

This module defines :class:`Tool`, a small base class used by the
sidebar tools.  It centralises the ``start``/``cancel`` lifecycle
and provides no-op hooks for drawing and event handling.  Subclasses
can override whichever behaviour they require.
"""

from __future__ import annotations


class Tool:
    """Minimal base class for sidebar tools.

    Parameters
    ----------
    sidebar:
        The :class:`builder_ui.sidebar.SidebarUI` instance owning the
        tool.  A reference to ``sidebar.app`` is exposed as ``self.app``
        for convenience.
    """

    def __init__(self, sidebar: "SidebarUI") -> None:
        self.sidebar = sidebar
        self.app = sidebar.app
        self.active = False

    # ---------------- lifecycle -------------------------------------------------
    def start(self) -> None:
        """Activate the tool."""
        self.active = True

    def cancel(self) -> None:
        """Deactivate the tool."""
        self.active = False

    # ---------------- drawing ---------------------------------------------------
    def draw_ui(self, offset: int = 0) -> bool:
        """Return ``True`` if the tool should draw its UI.

        Parameters
        ----------
        offset:
            Vertical sidebar offset applied during scrolling. The base class
            ignores this value but subclasses should forward it to their
            widgets.

        Subclasses should start their ``draw_ui`` implementation with::

            if not super().draw_ui(offset):
                return

        The default method simply checks whether the tool is active and the
        sidebar is visible.
        """

        return self.active and getattr(self.sidebar, "visible", True)

    def draw_preview(self) -> bool:
        """Return ``True`` if the tool should draw a world-space preview."""
        return self.active

    # ---------------- events ----------------------------------------------------
    def handle_event(self, event, offset: int = 0) -> bool:  # pragma: no cover - trivial
        """Return ``True`` if the tool should handle ``event``.

        Parameters
        ----------
        event:
            Pygame event being processed.
        offset:
            Vertical sidebar offset applied during scrolling.

        Subclasses typically call ``super().handle_event(event, offset)`` and abort if
        it returns ``False``::

            if not super().handle_event(event, offset):
                return False

        The default method returns ``True`` only when the tool is active and the
        sidebar is visible.
        """

        # If not active/visible, ignore
        if not (self.active and getattr(self.sidebar, "visible", True)):
            return False
        # Redirect scroll inputs to world zoom when pointer is over world area
        # This prevents sidebar scrolling while zooming with mouse wheel in the world.
        import pygame  # local to avoid circulars
        if event.type in (pygame.MOUSEWHEEL, pygame.MOUSEBUTTONDOWN) and getattr(event, "button", None) in (4, 5) or event.type == pygame.MOUSEWHEEL:
            mouse_x = pygame.mouse.get_pos()[0]
            if mouse_x < self.sidebar.screen.get_width() - self.sidebar.visible_width():
                return False
        return True
