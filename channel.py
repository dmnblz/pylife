"""Protocol for objects controlled via integer channels."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class ChannelControlled(Protocol):
    """Object that reacts to channel activation signals."""

    channel: int | None

    def set_channel_active(self, state: bool) -> None:
        """Apply channel-driven activation *state*."""
        ...
