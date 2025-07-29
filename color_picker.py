"""Utility to pick a color using Tkinter in a separate process."""
from multiprocessing import Pipe, Process
from typing import Optional, Tuple


def _chooser_process(initial: str, conn) -> None:
    """Open Tkinter color chooser and send the selected RGB value."""
    try:
        from tkinter import Tk, colorchooser
        root = Tk()
        root.withdraw()
        rgb, _ = colorchooser.askcolor(color=initial)
        root.destroy()
    except Exception:  # pragma: no cover - Tkinter might not be available
        rgb = None
    conn.send(rgb)
    conn.close()


def choose_color(initial: Tuple[int, int, int]) -> Optional[Tuple[int, int, int]]:
    """Return an RGB tuple selected by the user or ``None`` if canceled."""
    hex_color = "#%02x%02x%02x" % initial
    parent_conn, child_conn = Pipe()
    process = Process(target=_chooser_process, args=(hex_color, child_conn))
    process.start()
    rgb = parent_conn.recv()
    process.join()
    if rgb:
        return tuple(map(int, rgb))
    return None
