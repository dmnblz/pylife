"""Tiny event bus to decouple producers and consumers.

Allows parts of the app (e.g. sensors) to emit events that other
systems (e.g. registry/channel handling) can subscribe to without
direct references between them.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List


class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, name: str, fn: Callable) -> None:
        """Register ``fn`` to be called when ``name`` is emitted."""
        self._subscribers[name].append(fn)

    def unsubscribe(self, name: str, fn: Callable) -> None:
        """Remove ``fn`` from the subscribers of ``name`` if present."""
        lst = self._subscribers.get(name)
        if not lst:
            return
        try:
            lst.remove(fn)
        except ValueError:
            return
        if not lst:
            del self._subscribers[name]

    def emit(self, name: str, *args, **kwargs) -> None:
        """Invoke all callbacks subscribed to ``name``.

        Callbacks are invoked in the order they were registered and
        receive the provided ``*args`` / ``**kwargs``.
        """
        for fn in list(self._subscribers.get(name, ())):
            fn(*args, **kwargs)
