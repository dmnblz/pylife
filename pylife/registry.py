"""Key and channel registries for variable elements and sensors.

This module centralises registration and per-frame channel signalling so the
builder app does not have to juggle multiple dictionaries and sets.
"""
from __future__ import annotations

from typing import Dict, List, Set, Callable

from channel import ChannelControlled


class RegistryManager:
    def __init__(self) -> None:
        # key -> list of variable objects
        self.vspring_keys: Dict[int, list] = {}
        self.vparticle_keys: Dict[int, list] = {}
        self.vbend_keys: Dict[int, list] = {}
        self.cycle_keys: Dict[int, list] = {}
        # channel -> set[ChannelControlled]
        self.channels: Dict[int, Set[ChannelControlled]] = {}
        # per-frame activation set
        self.active_channels: Set[int] = set()

    # variable key maps -------------------------------------------------
    def register_keyed(self, mapping: Dict[int, list], obj, key: int | None) -> None:
        if key is not None:
            mapping.setdefault(int(key), []).append(obj)

    def update_keyed(self, mapping: Dict[int, list], obj, new_key: int | None) -> None:
        # remove old
        old = getattr(obj, "key", None)
        if old is not None:
            lst = mapping.get(old, [])
            if obj in lst:
                lst.remove(obj)
            if not lst and old in mapping:
                del mapping[old]
        # add new
        setattr(obj, "key", new_key)
        if new_key is not None:
            mapping.setdefault(int(new_key), []).append(obj)

    # channel maps ------------------------------------------------------
    def register_channel(self, obj: ChannelControlled) -> None:
        ch = getattr(obj, "channel", None)
        if ch is not None:
            self.channels.setdefault(int(ch), set()).add(obj)

    def update_channel(self, obj: ChannelControlled, channel: int | None) -> None:
        old = getattr(obj, "channel", None)
        if old is not None:
            objs = self.channels.get(int(old))
            if objs:
                objs.discard(obj)
                if not objs:
                    del self.channels[int(old)]
        setattr(obj, "channel", channel)
        if channel is not None:
            self.channels.setdefault(int(channel), set()).add(obj)

    # sensors -----------------------------------------------------------
    def register_sensor(self, sensor, on_trigger: Callable[[int | None], None]) -> None:
        sensor.add_callback(lambda s, o: on_trigger(getattr(s, "channel", None)))

    def signal_channel(self, channel: int | None) -> None:
        if channel is not None:
            self.active_channels.add(int(channel))

    def apply_channel_signals(self) -> None:
        for ch, objs in self.channels.items():
            state = ch in self.active_channels
            for obj in set(objs):
                obj.set_channel_active(state)
        self.active_channels.clear()

