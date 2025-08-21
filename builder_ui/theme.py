"""Theme token definitions with runtime switchable dark and light palettes."""

from __future__ import annotations

THEMES: dict[str, dict[str, tuple[int, int, int] | int]] = {
    "dark": {
        "ACCENT": (99, 171, 255),
        "TEXT": (235, 238, 245),
        "TEXT_MUTED": (190, 196, 210),
        # keep dark but not black, so shadows remain visible
        "BG_CANVAS_TOP": (34, 34, 40),
        "BG_CANVAS_BOTTOM": (24, 24, 30),
        "BG_SIDEBAR": (38, 41, 49),
        "BG_BUTTON": (54, 57, 66),
        "BG_BUTTON_HOVER": (68, 72, 83),
        "BG_BUTTON_ACTIVE": (78, 82, 95),
        "BG_INPUT": (46, 49, 57),
        "BORDER": (90, 95, 110),
        "BORDER_ACTIVE": (120, 130, 155),
        # overlay outside play area (RGBA alpha via separate drawing)
        "OFFBOUNDS": (0, 0, 0, 110),
        "RADIUS": 8,
    },
    "light": {
        "ACCENT": (60, 130, 255),
        "TEXT": (20, 24, 28),
        "TEXT_MUTED": (75, 85, 100),
        "BG_CANVAS_TOP": (252, 252, 255),
        "BG_CANVAS_BOTTOM": (232, 236, 244),
        "BG_SIDEBAR": (250, 252, 255),
        "BG_BUTTON": (238, 240, 250),
        "BG_BUTTON_HOVER": (230, 234, 246),
        "BG_BUTTON_ACTIVE": (215, 222, 240),
        "BG_INPUT": (245, 246, 253),
        "BORDER": (200, 205, 220),
        "BORDER_ACTIVE": (160, 170, 190),
        "OFFBOUNDS": (0, 0, 0, 60),
        "RADIUS": 8,
    },
}

# Default active theme name and token placeholders
_active_theme = "dark"

ACCENT: tuple[int, int, int]
TEXT: tuple[int, int, int]
TEXT_MUTED: tuple[int, int, int]
BG_CANVAS_TOP: tuple[int, int, int]
BG_CANVAS_BOTTOM: tuple[int, int, int]
BG_SIDEBAR: tuple[int, int, int]
BG_BUTTON: tuple[int, int, int]
BG_BUTTON_HOVER: tuple[int, int, int]
BG_BUTTON_ACTIVE: tuple[int, int, int]
BG_INPUT: tuple[int, int, int]
BORDER: tuple[int, int, int]
BORDER_ACTIVE: tuple[int, int, int]
OFFBOUNDS: tuple[int, int, int, int]
RADIUS: int


def _apply_theme(values: dict[str, tuple[int, int, int] | int]) -> None:
    global ACCENT, TEXT, TEXT_MUTED
    global BG_CANVAS_TOP, BG_CANVAS_BOTTOM, BG_SIDEBAR
    global BG_BUTTON, BG_BUTTON_HOVER, BG_BUTTON_ACTIVE
    global BG_INPUT, BORDER, BORDER_ACTIVE, OFFBOUNDS, RADIUS
    ACCENT = values["ACCENT"]  # type: ignore[assignment]
    TEXT = values["TEXT"]  # type: ignore[assignment]
    TEXT_MUTED = values["TEXT_MUTED"]  # type: ignore[assignment]
    BG_CANVAS_TOP = values["BG_CANVAS_TOP"]  # type: ignore[assignment]
    BG_CANVAS_BOTTOM = values["BG_CANVAS_BOTTOM"]  # type: ignore[assignment]
    BG_SIDEBAR = values["BG_SIDEBAR"]  # type: ignore[assignment]
    BG_BUTTON = values["BG_BUTTON"]  # type: ignore[assignment]
    BG_BUTTON_HOVER = values["BG_BUTTON_HOVER"]  # type: ignore[assignment]
    BG_BUTTON_ACTIVE = values["BG_BUTTON_ACTIVE"]  # type: ignore[assignment]
    BG_INPUT = values["BG_INPUT"]  # type: ignore[assignment]
    BORDER = values["BORDER"]  # type: ignore[assignment]
    BORDER_ACTIVE = values["BORDER_ACTIVE"]  # type: ignore[assignment]
    OFFBOUNDS = values["OFFBOUNDS"]  # type: ignore[assignment]
    RADIUS = int(values["RADIUS"])  # type: ignore[index]


def set_theme(name: str) -> None:
    """Set the active theme tokens by name ("dark" or "light")."""
    global _active_theme
    name = name.lower()
    if name not in THEMES:
        name = "dark"
    _active_theme = name
    _apply_theme(THEMES[name])


def get_theme_name() -> str:
    return _active_theme


# initialise defaults
set_theme(_active_theme)

__all__ = [
    "ACCENT",
    "TEXT",
    "TEXT_MUTED",
    "BG_CANVAS_TOP",
    "BG_CANVAS_BOTTOM",
    "BG_SIDEBAR",
    "BG_BUTTON",
    "BG_BUTTON_HOVER",
    "BG_BUTTON_ACTIVE",
    "BG_INPUT",
    "BORDER",
    "BORDER_ACTIVE",
    "OFFBOUNDS",
    "RADIUS",
    "set_theme",
    "get_theme_name",
    "THEMES",
]


