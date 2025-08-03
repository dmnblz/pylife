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
    def draw_ui(self) -> bool:
        """Return ``True`` if the tool should draw its UI.

        Subclasses should start their ``draw_ui`` implementation with::

            if not super().draw_ui():
                return

        The default method simply checks whether the tool is active and the
        sidebar is visible.
        """

        return self.active and getattr(self.sidebar, "visible", True)

    def draw_preview(self) -> bool:
        """Return ``True`` if the tool should draw a world-space preview."""
        return self.active

    # ---------------- events ----------------------------------------------------
    def handle_event(self, event) -> bool:  # pragma: no cover - trivial
        """Return ``True`` if the tool should handle ``event``.

        Subclasses typically call ``super().handle_event(event)`` and abort if
        it returns ``False``::

            if not super().handle_event(event):
                return False

        The default method returns ``True`` only when the tool is active and the
        sidebar is visible.
        """

        return self.active and getattr(self.sidebar, "visible", True)
