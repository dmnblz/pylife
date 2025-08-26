"""Lightweight rule-based event engine for the builder.

Provides a minimal WHEN/THEN mechanism that can evolve into a richer
system. For now we support:

- SensorEdgeTrigger: enter/stay/exit based on a sensor + its trigger
- ChannelSetAction: mark a channel as active for this frame

Rules are evaluated each frame via :meth:`EventEngine.tick` and actions
are executed when their trigger fires. The engine relies on the existing
RegistryManager for channel signalling so it composes with current
variable elements.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Protocol

from sensor_particle import SensorParticle
from pylife.registry import RegistryManager


class Trigger(Protocol):
    def fired(self) -> bool:  # pragma: no cover - protocol only
        ...


class Action(Protocol):
    def execute(self, registry: RegistryManager) -> None:  # pragma: no cover
        ...


@dataclass
class SensorEdgeTrigger:
    """Trigger on sensor edge/state.

    edge: one of "enter", "stay", "exit".
    """

    sensor: SensorParticle
    edge: str = "stay"

    # internal state
    _prev_in: bool = False

    def _in_view(self) -> bool:
        trg = getattr(self.sensor, "trigger", None)
        if trg is None:
            return False
        # Use the sensor's geometric test without invoking callbacks
        try:
            return self.sensor.in_view(trg)
        except AttributeError:
            # Backward safeguard (should not happen once SensorParticle grows in_view)
            d = trg.pos - self.sensor.pos
            if d.length() > self.sensor.sense_radius:
                return False
            if self.sensor.half_angle < 3.141592653589793:
                if d.normalize().dot(self.sensor.forward) < math.cos(self.sensor.half_angle):  # type: ignore[name-defined]
                    return False
            return True

    def fired(self) -> bool:
        now_in = self._in_view()
        edge = self.edge
        hit = False
        if edge == "enter":
            hit = (not self._prev_in) and now_in
        elif edge == "exit":
            hit = self._prev_in and (not now_in)
        else:  # "stay"
            hit = now_in
        self._prev_in = now_in
        return hit


@dataclass
class ChannelSetAction:
    """Mark channel as active for this frame (if not None)."""

    channel: int | None

    def execute(self, registry: RegistryManager) -> None:
        if self.channel is not None:
            registry.signal_channel(int(self.channel))


@dataclass
class EventRule:
    trigger: Trigger
    actions: List[Action]

    def evaluate(self, registry: RegistryManager) -> None:
        if self.trigger.fired():
            for a in self.actions:
                a.execute(registry)


class EventEngine:
    """Holds rules and ticks them each frame.

    Keep this independent of pygame; BuilderApp owns and calls it.
    """

    def __init__(self, registry: RegistryManager) -> None:
        self.registry = registry
        self.rules: List[EventRule] = []

    def clear(self) -> None:
        self.rules.clear()

    def add_rule(self, rule: EventRule) -> None:
        self.rules.append(rule)

    def tick(self) -> None:
        for r in list(self.rules):
            r.evaluate(self.registry)

