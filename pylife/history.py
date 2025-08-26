"""Undo history stack with simple callable actions."""
from __future__ import annotations

from typing import Callable, List


class UndoStack:
    def __init__(self) -> None:
        self._stack: List[Callable[[], None]] = []

    def push(self, action: Callable[[], None]) -> None:
        self._stack.append(action)

    def undo(self) -> None:
        if self._stack:
            self._stack.pop()()

    def clear(self) -> None:
        self._stack.clear()

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._stack)

