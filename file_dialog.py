"""File dialog utilities using Tkinter in a subprocess."""

from multiprocessing import Pipe, Process
from typing import Optional



def _save_process(initial: str, conn) -> None:
    try:
        from tkinter import Tk, filedialog
        root = Tk()
        root.withdraw()
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=initial,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        root.destroy()
    except Exception:
        path = None
    conn.send(path)
    conn.close()


def _open_process(conn) -> None:
    try:
        from tkinter import Tk, filedialog
        root = Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        root.destroy()
    except Exception:
        path = None
    conn.send(path)
    conn.close()


def choose_save_path(initial: str = "scene.json") -> Optional[str]:
    parent_conn, child_conn = Pipe()
    process = Process(target=_save_process, args=(initial, child_conn))
    process.start()
    path = parent_conn.recv()
    process.join()
    return path


def choose_open_path() -> Optional[str]:
    parent_conn, child_conn = Pipe()
    process = Process(target=_open_process, args=(child_conn,))
    process.start()
    path = parent_conn.recv()
    process.join()
    return path
