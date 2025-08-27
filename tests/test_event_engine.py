import pygame

from pylife.event_engine import (
    EventEngine,
    EventRule,
    ChannelSetAction,
    ChannelPulseAction,
    ChannelHoldAction,
    ChannelReleaseAction,
    TimerTrigger,
    KeyTrigger,
)
from pylife.registry import RegistryManager


class Dummy:
    def __init__(self):
        self.channel = 1
        self.active = False

    def set_channel_active(self, state: bool) -> None:
        self.active = bool(state)


def test_pulse_action_enables_then_expires() -> None:
    reg = RegistryManager()
    eng = EventEngine(reg)
    # Register a dummy on channel 1
    d = Dummy()
    reg.register_channel(d)
    # Immediate pulse for 50 ms via a one-shot timer
    eng.add_rule(
        EventRule(TimerTrigger("after", 0), [ChannelPulseAction(1, 50)])
    )
    # Tick once to fire timer and schedule the pulse
    eng.tick(0.001)
    # Apply signals this frame
    reg.apply_channel_signals()
    assert d.active is True
    # Advance 30 ms: still active
    eng.tick(0.03)
    reg.apply_channel_signals()
    assert d.active is True
    # Advance beyond 50 ms total
    eng.tick(0.2)
    reg.apply_channel_signals()
    assert d.active is False


def test_hold_and_release_persist_across_frames() -> None:
    reg = RegistryManager()
    eng = EventEngine(reg)
    d = Dummy()
    reg.register_channel(d)
    # Use key edges to hold then release
    eng.add_rule(EventRule(KeyTrigger(pygame.K_h, edge="down"), [ChannelHoldAction(1)]))
    eng.add_rule(EventRule(KeyTrigger(pygame.K_h, edge="up"), [ChannelReleaseAction(1)]))
    # Press
    eng.key_down(pygame.K_h)
    eng.tick(0.016)
    reg.apply_channel_signals()
    assert d.active is True
    # Multiple frames while held
    eng.tick(0.016)
    reg.apply_channel_signals()
    assert d.active is True
    # Release
    eng.key_up(pygame.K_h)
    eng.tick(0.016)
    reg.apply_channel_signals()
    assert d.active is False


def test_key_trigger_edges_and_hold() -> None:
    reg = RegistryManager()
    eng = EventEngine(reg)
    fired = {"down": 0, "up": 0, "hold": 0}

    class CounterAction:
        def __init__(self, key: str):
            self.key = key

        def execute(self, _r, _e):
            fired[self.key] += 1

    eng.add_rule(EventRule(KeyTrigger(pygame.K_a, edge="down"), [CounterAction("down")]))
    eng.add_rule(EventRule(KeyTrigger(pygame.K_a, edge="up"), [CounterAction("up")]))
    eng.add_rule(EventRule(KeyTrigger(pygame.K_a, edge="hold"), [CounterAction("hold")]))

    # Press once: should count one down and one hold
    eng.key_down(pygame.K_a)
    eng.tick(0.016)
    assert fired["down"] == 1
    assert fired["hold"] == 1
    # Next frame while held: no new down, hold increments
    eng.tick(0.016)
    assert fired["down"] == 1
    assert fired["hold"] == 2
    # Release: up increments once, and no hold
    eng.key_up(pygame.K_a)
    eng.tick(0.016)
    assert fired["up"] == 1
    # Another frame after release: no change
    eng.tick(0.016)
    assert fired["up"] == 1


def test_timer_every_with_drift() -> None:
    reg = RegistryManager()
    eng = EventEngine(reg)
    count = {"n": 0}

    class Bump:
        def execute(self, _r, _e):
            count["n"] += 1

    # Fire every 10ms
    from pylife.event_engine import TimerTrigger as TT
    eng.add_rule(EventRule(TT("every", 10), [Bump()]))

    # Advance with a large dt (~35ms). Should fire at least once, accounting for drift.
    eng.tick(0.035)
    assert count["n"] >= 1
    # Another 20ms should bump again
    eng.tick(0.02)
    assert count["n"] >= 2

