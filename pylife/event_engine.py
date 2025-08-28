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
from typing import List, Protocol, Set, Dict, Callable, Tuple, Optional

from sensor_particle import SensorParticle
from pylife.registry import RegistryManager


class Trigger(Protocol):
    def fired(self, engine: "EventEngine") -> bool:  # pragma: no cover - protocol only
        ...


class Action(Protocol):
    def execute(self, registry: RegistryManager, engine: "EventEngine") -> None:  # pragma: no cover
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

    def fired(self, engine: "EventEngine") -> bool:
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

    def execute(self, registry: RegistryManager, engine: "EventEngine") -> None:
        if self.channel is not None:
            registry.signal_channel(int(self.channel))


@dataclass
class ChannelPulseAction:
    """Activate a channel for a fixed duration in milliseconds."""

    channel: int | None
    duration_ms: int

    def execute(self, registry: RegistryManager, engine: "EventEngine") -> None:
        if self.channel is None:
            return
        end = engine.now_ms + max(0, int(self.duration_ms))
        engine._active_pulses.setdefault(int(self.channel), []).append(end)


@dataclass
class ChannelHoldAction:
    """Continuously mark a channel active until a matching release."""

    channel: int | None

    def execute(self, registry: RegistryManager, engine: "EventEngine") -> None:
        if self.channel is None:
            return
        ch = int(self.channel)
        engine._held_channels.add(ch)
        # Signal immediately this frame as well
        registry.signal_channel(ch)


@dataclass
class ChannelReleaseAction:
    """Release a previously held channel (no-op if not held)."""

    channel: int | None

    def execute(self, registry: RegistryManager, engine: "EventEngine") -> None:
        if self.channel is None:
            return
        engine._held_channels.discard(int(self.channel))


@dataclass
class DelayAction:
    """A delay placeholder used by SequenceAction for scheduling."""

    duration_ms: int

    def execute(self, registry: RegistryManager, engine: "EventEngine") -> None:
        # Standalone Delay has no effect; meaningful only inside SequenceAction
        return


class SequenceAction:
    """Execute a list of actions in order, supporting delays between steps.

    DelayAction steps cause the remaining sub-sequence to be scheduled
    after the specified number of milliseconds.
    """

    def __init__(self, steps: List[Action]):
        self.steps = list(steps)

    def _continue_from(self, index: int, registry: RegistryManager, engine: "EventEngine") -> None:
        i = index
        while i < len(self.steps):
            step = self.steps[i]
            if isinstance(step, DelayAction):
                delay = max(0, int(step.duration_ms))
                # schedule continuation after delay
                engine.schedule_in(delay, lambda _r, _e, idx=i + 1, r=registry, e=engine: self._continue_from(idx, r, e))
                return
            else:
                step.execute(registry, engine)
                i += 1

    def execute(self, registry: RegistryManager, engine: "EventEngine") -> None:
        self._continue_from(0, registry, engine)


@dataclass
class TimerTrigger:
    """Fires after/every interval in milliseconds."""

    mode: str  # "after" | "every"
    interval_ms: int
    _next_ms: int | None = None

    def fired(self, engine: "EventEngine") -> bool:
        if self._next_ms is None:
            self._next_ms = engine.now_ms + max(0, int(self.interval_ms))
            return False
        now = engine.now_ms
        if now >= self._next_ms:
            if self.mode == "every":
                # schedule next tick; carry remainder to avoid drift
                missed = (now - self._next_ms) // max(1, int(self.interval_ms))
                self._next_ms = self._next_ms + (missed + 1) * max(1, int(self.interval_ms))
            else:  # after
                # one-shot
                self._next_ms = 2**31 - 1
            return True
        return False


@dataclass
class KeyTrigger:
    """Fires on key down/up/hold for a specific pygame key code."""

    key: int
    edge: str  # "down" | "up" | "hold"

    def fired(self, engine: "EventEngine") -> bool:
        if self.edge == "down":
            return engine._consume_key_edge("down", self.key)
        if self.edge == "up":
            return engine._consume_key_edge("up", self.key)
        # hold
        return self.key in engine._keys_down


@dataclass
class EventRule:
    """A rule mapping a trigger to one or more actions.

    The ``enabled`` flag allows rules to be toggled without deletion.
    Disabled rules are skipped by the engine but kept in the list and
    persisted with the scene.
    """

    trigger: Trigger
    actions: List[Action]
    enabled: bool = True

    def evaluate(self, registry: RegistryManager, engine: "EventEngine") -> None:
        if not self.enabled:
            return
        if self.trigger.fired(engine):
            for a in self.actions:
                a.execute(registry, engine)


class EventEngine:
    """Holds rules and ticks them each frame.

    Keep this independent of pygame; BuilderApp owns and calls it.
    """

    def __init__(self, registry: RegistryManager) -> None:
        self.registry = registry
        self.rules: List[EventRule] = []
        self.now_ms: int = 0
        # key handling
        self._keys_down: Set[int] = set()
        self._down_edges: Set[int] = set()
        self._up_edges: Set[int] = set()
        # pulses: channel -> list[end_ms]
        self._active_pulses: Dict[int, List[int]] = {}
        # held channels (active until released)
        self._held_channels: Set[int] = set()
        # scheduled continuations: (due_ms, callback)
        self._scheduled: List[Tuple[int, Callable[[RegistryManager, "EventEngine"], None]]] = []

    def clear(self) -> None:
        self.rules.clear()
        self._active_pulses.clear()
        self._held_channels.clear()
        self._scheduled.clear()

    def add_rule(self, rule: EventRule) -> None:
        self.rules.append(rule)

    def tick(self, dt: float | None = None) -> None:
        if dt is not None:
            self.now_ms += int(max(0.0, dt) * 1000)
        # run scheduled continuations due at or before now
        if self._scheduled:
            now = self.now_ms
            due: List[Tuple[int, Callable[[RegistryManager, "EventEngine"], None]]] = []
            keep: List[Tuple[int, Callable[[RegistryManager, "EventEngine"], None]]] = []
            for t, fn in self._scheduled:
                if t <= now:
                    due.append((t, fn))
                else:
                    keep.append((t, fn))
            self._scheduled = keep
            for _, fn in due:
                try:
                    fn(self.registry, self)
                except Exception:
                    # swallow to avoid breaking the frame; user-level actions are best-effort
                    pass
        # pulses: keep channels active while their pulse lives
        if self._active_pulses:
            expired: list[tuple[int, int]] = []
            for ch, ends in self._active_pulses.items():
                # signal for this frame
                self.registry.signal_channel(ch)
                # drop finished
                keep = [t for t in ends if t > self.now_ms]
                if keep:
                    self._active_pulses[ch] = keep
                else:
                    expired.append((ch, 0))
            for ch, _ in expired:
                self._active_pulses.pop(ch, None)
        # held channels: signal every frame
        for ch in list(self._held_channels):
            self.registry.signal_channel(ch)
        for r in list(self.rules):
            r.evaluate(self.registry, self)
        # clear key edges at end of frame
        self._down_edges.clear()
        self._up_edges.clear()

    # key integration -------------------------------------------------
    def key_down(self, key: int) -> None:
        if key not in self._keys_down:
            self._keys_down.add(key)
            self._down_edges.add(key)

    def key_up(self, key: int) -> None:
        if key in self._keys_down:
            self._keys_down.discard(key)
            self._up_edges.add(key)

    def _consume_key_edge(self, edge: str, key: int) -> bool:
        if edge == "down":
            if key in self._down_edges:
                # leave it present for this evaluation but ensure single fire per frame
                return True
            return False
        if edge == "up":
            return key in self._up_edges
        return False

    # scheduling --------------------------------------------------------
    def schedule_at(self, due_ms: int, callback: Callable[[RegistryManager, "EventEngine"], None]) -> None:
        self._scheduled.append((max(0, int(due_ms)), callback))

    def schedule_in(self, delay_ms: int, callback: Callable[[RegistryManager, "EventEngine"], None]) -> None:
        self.schedule_at(self.now_ms + max(0, int(delay_ms)), callback)
