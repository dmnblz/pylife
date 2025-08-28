from __future__ import annotations

import pygame

from .fields import ButtonField
from . import theme


class EventsModal:
    """Centered modal UI for composing event rules with sequential blocks.

    Keeps simple state for a single rule under construction and lists
    existing rules with delete buttons.
    """

    def __init__(self, app):
        self.app = app
        self.visible = False
        self.editing_index: int | None = None
        # trigger state
        self.trigger_type = "sensor"  # sensor|key|timer
        self.sensor_index = 0
        self.sensor_edge = "stay"  # enter|stay|exit
        self.key_value: int | None = None
        self.key_edge = "down"  # down|hold|up
        self.capturing_key = False
        self.timer_mode = "every"  # every|after
        self.timer_ms = 1000
        # blocks: list of dicts {type, ...}
        self.blocks: list[dict] = []
        # cached geometry
        self.rect = pygame.Rect(0, 0, 760, 520)
        # inline numeric inputs registered per draw
        self._inputs: list[object] = []
        # persistent input state map: key -> {editing: bool, text: str}
        self._input_state: dict[str, dict] = {}
        # focused input state
        self._focused_input = None

    # -------------------------------------------------------------- lifecycle
    def open(self) -> None:
        self.visible = True

    def close(self) -> None:
        self.visible = False
        self.capturing_key = False

    # -------------------------------------------------------------- actions
    def _compile_actions(self):
        from pylife.event_engine import (
            ChannelSetAction,
            ChannelPulseAction,
            ChannelHoldAction,
            ChannelReleaseAction,
            DelayAction,
            SequenceAction,
        )
        actions = []
        for b in self.blocks:
            t = b.get("type")
            if t == "set":
                actions.append(ChannelSetAction(b.get("channel", 0)))
            elif t == "pulse":
                actions.append(ChannelPulseAction(b.get("channel", 0), int(b.get("duration_ms", 200))))
            elif t == "hold":
                actions.append(ChannelHoldAction(b.get("channel", 0)))
            elif t == "release":
                actions.append(ChannelReleaseAction(b.get("channel", 0)))
            elif t == "wait":
                actions.append(DelayAction(int(b.get("duration_ms", 0))))
        # Use a SequenceAction if there are waits or multiple steps
        if len(actions) > 1 or any(a.__class__.__name__ == "DelayAction" for a in actions):
            return [SequenceAction(actions)]
        return actions

    def _add_rule(self) -> None:
        from pylife.event_engine import EventRule, SensorEdgeTrigger, KeyTrigger, TimerTrigger
        if not self.blocks:
            return
        actions = self._compile_actions()
        trigger = None
        if self.trigger_type == "sensor" and self.app.sensors:
            sensor = self.app.sensors[self.sensor_index % len(self.app.sensors)]
            trigger = SensorEdgeTrigger(sensor, edge=self.sensor_edge)
        elif self.trigger_type == "key" and self.key_value is not None:
            trigger = KeyTrigger(int(self.key_value), edge=self.key_edge)
        elif self.trigger_type == "timer":
            trigger = TimerTrigger(self.timer_mode, int(self.timer_ms))
        if trigger:
            new_rule = EventRule(trigger, actions)
            # preserve enabled state when overwriting an existing rule
            if self.editing_index is not None and 0 <= self.editing_index < len(self.app.event_engine.rules):
                prev = self.app.event_engine.rules[self.editing_index]
                try:
                    new_rule.enabled = bool(getattr(prev, "enabled", True))
                except Exception:
                    new_rule.enabled = True
                self.app.event_engine.rules[self.editing_index] = new_rule
            else:
                self.app.event_engine.add_rule(new_rule)
            # Reset for next rule
            self.blocks.clear()
            self.editing_index = None

    # -------------------------------------------------------------- UI helpers
    def _panel_rect(self) -> pygame.Rect:
        sw, sh = self.app.screen.get_size()
        self.rect.center = (sw // 2, sh // 2)
        return self.rect

    def draw(self) -> None:
        if not self.visible:
            return
        # reset interactive buttons collection
        self._btns: list[ButtonField] = []
        self._inputs = []
        # dim background
        overlay = pygame.Surface(self.app.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((*theme.BG_SIDEBAR, 140))
        self.app.screen.blit(overlay, (0, 0))
        # panel
        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        # background
        pygame.draw.rect(panel, (*theme.BG_SIDEBAR, 235), panel.get_rect(), border_radius=12)
        pygame.draw.rect(panel, (*theme.TEXT, 40), panel.get_rect().inflate(-2, -2), width=1, border_radius=10)
        font = self.app.font
        # title
        title = font.render("Events Editor", True, theme.TEXT)
        panel.blit(title, (16, 12))
        y = 46
        # trigger row
        # Trigger type toggle
        def _toggle_trigger():
            order = ["sensor", "key", "timer"]
            i = order.index(self.trigger_type)
            self.trigger_type = order[(i + 1) % len(order)]
        ox, oy = self._panel_rect().topleft
        self._btn_trigger = ButtonField(lambda: f"Trigger: {self.trigger_type}", _toggle_trigger, 16, y, 200)
        self._btn_trigger.draw(panel, 0, origin=(ox, oy))
        self._btns.append(self._btn_trigger)
        x = 226
        if self.trigger_type == "sensor":
            def _edge():
                order = ["enter", "stay", "exit"]
                i = order.index(self.sensor_edge)
                self.sensor_edge = order[(i + 1) % len(order)]
            btn_edge = ButtonField(lambda: f"Edge: {self.sensor_edge}", _edge, x, y, 160)
            btn_edge.draw(panel, 0, origin=(ox, oy))
            self._btns.append(btn_edge)
            x += 170
            def _next_sensor():
                if self.app.sensors:
                    self.sensor_index = (self.sensor_index + 1) % len(self.app.sensors)
            btn_idx = ButtonField(lambda: f"Sensor: {self.sensor_index}" if self.app.sensors else "Sensor: -", _next_sensor, x, y, 160)
            btn_idx.draw(panel, 0, origin=(ox, oy))
            self._btns.append(btn_idx)
        elif self.trigger_type == "key":
            def _edge():
                order = ["down", "hold", "up"]
                i = order.index(self.key_edge)
                self.key_edge = order[(i + 1) % len(order)]
            btn_edge = ButtonField(lambda: f"Edge: {self.key_edge}", _edge, x, y, 160)
            btn_edge.draw(panel, 0, origin=(ox, oy))
            self._btns.append(btn_edge)
            x += 170
            def _capture():
                self.capturing_key = True
            btn_key = ButtonField(lambda: f"Key: {pygame.key.name(self.key_value)}" if self.key_value is not None else "Key: (capture)", _capture, x, y, 200)
            btn_key.draw(panel, 0, origin=(ox, oy))
            self._btns.append(btn_key)
        else:
            def _mode():
                self.timer_mode = "after" if self.timer_mode == "every" else "every"
            btn_mode = ButtonField(lambda: f"Mode: {self.timer_mode}", _mode, x, y, 160)
            btn_mode.draw(panel, 0, origin=(ox, oy))
            self._btns.append(btn_mode)
            x += 170
            # inline numeric entry for timer interval (ms)
            lab = font.render("Interval (ms)", True, theme.TEXT)
            panel.blit(lab, (x, y - 22))
            entry_rect = pygame.Rect(x, y + 2, 120, 24)
            self._draw_numeric_entry(panel, entry_rect, lambda: int(self.timer_ms), lambda v: setattr(self, "timer_ms", max(10, min(60000, int(v)))), key="timer_ms")

        y += 44
        # blocks header
        panel.blit(font.render("Blocks:", True, theme.TEXT), (16, y))
        y += font.get_linesize() + 6
        # add-block buttons
        def _add_set():
            self.blocks.append({"type": "set", "channel": 0})
        def _add_pulse():
            self.blocks.append({"type": "pulse", "channel": 0, "duration_ms": 200})
        def _add_wait():
            self.blocks.append({"type": "wait", "duration_ms": 200})
        def _add_hold():
            self.blocks.append({"type": "hold", "channel": 0})
        def _add_release():
            self.blocks.append({"type": "release", "channel": 0})
        btns = [
            ("+Set", _add_set),
            ("+Pulse", _add_pulse),
            ("+Wait", _add_wait),
            ("+Hold", _add_hold),
            ("+Release", _add_release),
        ]
        bx = 16
        for label, fn in btns:
            bf = ButtonField(label, fn, bx, y, 120)
            bf.draw(panel, 0, origin=(ox, oy))
            self._btns.append(bf)
            bx += 128
        y += 36
        # list blocks
        row_h = 34
        for i, b in enumerate(self.blocks):
            row_y = y + i * row_h
            # type label
            t = b.get("type")
            panel.blit(font.render(t.capitalize(), True, theme.TEXT), (24, row_y + 6))
            # value editors
            x = 140
            # inline numeric entry for channel when applicable
            if t in ("set", "pulse", "hold", "release"):
                ch_label = font.render("ch", True, theme.TEXT)
                panel.blit(ch_label, (x, row_y - 16))
                ch_rect = pygame.Rect(x, row_y + 4, 80, 24)
                def _get_ch(i=i):
                    return int(self.blocks[i].get('channel', 0))
                def _set_ch(v, i=i):
                    try:
                        self.blocks[i]['channel'] = max(0, min(9, int(v)))
                    except Exception:
                        pass
                self._draw_numeric_entry(panel, ch_rect, _get_ch, _set_ch, key=f"block-{i}-channel")
                x = ch_rect.right + 20
            # inline numeric entry for duration when applicable
            if t in ("pulse", "wait"):
                lab = font.render("ms", True, theme.TEXT)
                entry_rect = pygame.Rect(x, row_y + 4, 120, 24)
                def _get(i=i):
                    return int(self.blocks[i].get('duration_ms', 200))
                def _set(v, i=i):
                    try:
                        self.blocks[i]['duration_ms'] = max(10, min(60000, int(v)))
                    except Exception:
                        pass
                self._draw_numeric_entry(panel, entry_rect, _get, _set, key=f"block-{i}-ms")
                panel.blit(lab, (entry_rect.right + 6, row_y + 6))
                x = entry_rect.right + 40
            # delete block
            def _del(idx=i):
                if 0 <= idx < len(self.blocks):
                    self.blocks.pop(idx)
            # move up/down
            def _up(idx=i):
                if idx > 0:
                    self.blocks[idx-1], self.blocks[idx] = self.blocks[idx], self.blocks[idx-1]
            def _down(idx=i):
                if idx < len(self.blocks)-1:
                    self.blocks[idx+1], self.blocks[idx] = self.blocks[idx], self.blocks[idx+1]
            def _dup(idx=i):
                if 0 <= idx < len(self.blocks):
                    self.blocks.insert(idx+1, dict(self.blocks[idx]))
            # align controls near the right edge but fully visible
            gap = 8
            controls_total = 60 + gap + 60 + gap + 60 + gap + 90
            base_x = self.rect.width - 16 - controls_total
            bf_up = ButtonField("Up", _up, base_x, row_y, 60)
            bf_down = ButtonField("Down", _down, base_x + 60 + gap, row_y, 60)
            bf_dup = ButtonField("Dup", _dup, base_x + 60 + gap + 60 + gap, row_y, 60)
            bf_del = ButtonField("Delete", _del, base_x + 60 + gap + 60 + gap + 60 + gap, row_y, 90)
            bf_up.draw(panel, 0, origin=(ox, oy))
            bf_down.draw(panel, 0, origin=(ox, oy))
            bf_dup.draw(panel, 0, origin=(ox, oy))
            bf_del.draw(panel, 0, origin=(ox, oy))
            self._btns.extend([bf_up, bf_down, bf_dup, bf_del])
        y += len(self.blocks) * row_h + 8
        # footer buttons
        def _is_valid():
            if not self.blocks:
                return False
            # trigger validity
            if self.trigger_type == "sensor" and not self.app.sensors:
                return False
            if self.trigger_type == "key" and self.key_value is None:
                return False
            return True
        add_label = (lambda: ("Save Rule" if self.editing_index is not None else "Add Rule"))
        bf_add = ButtonField(add_label, self._add_rule, 16, y, 140, active=lambda: _is_valid())
        bf_close = ButtonField("Close", self.close, 170, y, 100)
        def _clear_blocks():
            self.blocks.clear()
            self.editing_index = None
        bf_clear = ButtonField("Clear Blocks", _clear_blocks, 280, y, 160)
        bf_add.draw(panel, 0, origin=(ox, oy))
        bf_close.draw(panel, 0, origin=(ox, oy))
        bf_clear.draw(panel, 0, origin=(ox, oy))
        self._btns.extend([bf_add, bf_close, bf_clear])

        # existing rules list
        y += 44
        panel.blit(font.render("Existing Rules:", True, theme.TEXT), (16, y))
        y += 8
        from pylife.event_engine import SensorEdgeTrigger, KeyTrigger, TimerTrigger, SequenceAction, DelayAction, ChannelSetAction, ChannelPulseAction, ChannelHoldAction, ChannelReleaseAction
        def _rule_title(rule) -> str:
            t = rule.trigger
            if isinstance(t, SensorEdgeTrigger):
                try:
                    idx = self.app.sensors.index(t.sensor)
                except ValueError:
                    idx = -1
                trig = f"Sensor[{idx}] {t.edge}"
            elif isinstance(t, KeyTrigger):
                trig = f"Key {t.key} {t.edge}"
            elif isinstance(t, TimerTrigger):
                trig = f"Timer {t.mode} {t.interval_ms}ms"
            else:
                trig = "Trigger"
            acts = getattr(rule, 'actions', [])
            def _act_name(a):
                if isinstance(a, SequenceAction):
                    return "Seq(...)"
                if isinstance(a, ChannelSetAction):
                    return f"Set({a.channel})"
                if isinstance(a, ChannelPulseAction):
                    return f"Pulse({a.channel},{a.duration_ms}ms)"
                if isinstance(a, ChannelHoldAction):
                    return f"Hold({a.channel})"
                if isinstance(a, ChannelReleaseAction):
                    return f"Release({a.channel})"
                if isinstance(a, DelayAction):
                    return f"Wait({a.duration_ms}ms)"
                return a.__class__.__name__
            a_txt = ", ".join(_act_name(a) for a in acts)
            prefix = "[disabled] " if not getattr(rule, 'enabled', True) else ""
            return f"{prefix}{trig} -> {a_txt}"

        def _flatten_actions(acts):
            out = []
            for a in acts:
                if isinstance(a, SequenceAction):
                    out.extend(_flatten_actions(getattr(a, 'steps', [])))
                elif isinstance(a, ChannelSetAction):
                    out.append({"type": "set", "channel": a.channel})
                elif isinstance(a, ChannelPulseAction):
                    out.append({"type": "pulse", "channel": a.channel, "duration_ms": a.duration_ms})
                elif isinstance(a, ChannelHoldAction):
                    out.append({"type": "hold", "channel": a.channel})
                elif isinstance(a, ChannelReleaseAction):
                    out.append({"type": "release", "channel": a.channel})
                elif isinstance(a, DelayAction):
                    out.append({"type": "wait", "duration_ms": a.duration_ms})
            return out

        def _load_rule(idx: int):
            if not (0 <= idx < len(self.app.event_engine.rules)):
                return
            rule = self.app.event_engine.rules[idx]
            t = rule.trigger
            if isinstance(t, SensorEdgeTrigger):
                self.trigger_type = "sensor"
                try:
                    self.sensor_index = self.app.sensors.index(t.sensor)
                except ValueError:
                    self.sensor_index = 0
                self.sensor_edge = t.edge
            elif isinstance(t, KeyTrigger):
                self.trigger_type = "key"
                self.key_value = int(t.key)
                self.key_edge = t.edge
            elif isinstance(t, TimerTrigger):
                self.trigger_type = "timer"
                self.timer_mode = t.mode
                self.timer_ms = int(t.interval_ms)
            # blocks
            self.blocks = _flatten_actions(getattr(rule, 'actions', []))
            self.editing_index = idx

        rules = list(getattr(self.app.event_engine, 'rules', ()))
        for i, rule in enumerate(rules):
            row_y = y + i * 30
            # title text
            txt = font.render(_rule_title(rule), True, theme.TEXT)
            panel.blit(txt, (16, row_y + 6))
            # buttons
            def _mk_edit(j=i):
                return lambda: _load_rule(j)
            def _mk_del(j=i):
                def _del():
                    if 0 <= j < len(self.app.event_engine.rules):
                        self.app.event_engine.rules.pop(j)
                        # if we were editing a rule after this index, adjust
                        if self.editing_index is not None:
                            if self.editing_index == j:
                                self.editing_index = None
                                self.blocks.clear()
                            elif self.editing_index > j:
                                self.editing_index -= 1
                return _del
            def _mk_toggle(j=i):
                def _toggle():
                    if 0 <= j < len(self.app.event_engine.rules):
                        r = self.app.event_engine.rules[j]
                        try:
                            r.enabled = not bool(getattr(r, 'enabled', True))
                        except Exception:
                            r.enabled = True
                return _toggle
            # position buttons at right
            pr = self.rect
            bx = pr.width - 330
            label = ("Disable" if getattr(rule, 'enabled', True) else "Enable")
            b_toggle = ButtonField(label, _mk_toggle(), bx, row_y, 100)
            b_edit = ButtonField("Edit", _mk_edit(), bx + 110, row_y, 90)
            b_del = ButtonField("Delete", _mk_del(), bx + 210, row_y, 100)
            b_toggle.draw(panel, 0, origin=(ox, oy))
            b_edit.draw(panel, 0, origin=(ox, oy))
            b_del.draw(panel, 0, origin=(ox, oy))
            self._btns.extend([b_toggle, b_edit, b_del])

        # draw onto screen
        self.app.screen.blit(panel, self._panel_rect())

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        # eat ESC to close
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()
            return True
        # capture key value
        if self.capturing_key and event.type == pygame.KEYDOWN:
            self.key_value = int(event.key)
            self.capturing_key = False
            return True
        # route mouse/keyboard events to inputs and buttons using local coordinates
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.MOUSEWHEEL):
            rect = self._panel_rect()
            # For wheel events, pygame supplies .y not .pos; allow through
            if hasattr(event, "pos"):
                if not rect.collidepoint(event.pos):
                    # Click outside closes
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.close()
                    return True
                # transform to local coordinates for buttons
                local = (event.pos[0] - rect.x, event.pos[1] - rect.y)
                # build a minimal event with remapped position for buttons
                attrs = {"pos": local}
                if hasattr(event, "button"):
                    attrs["button"] = getattr(event, "button")
                if hasattr(event, "y"):
                    attrs["y"] = getattr(event, "y")
                evt = pygame.event.Event(event.type, attrs)
                # inputs first
                for inp in list(getattr(self, "_inputs", [])):
                    if inp.handle_event(evt):
                        return True
                for b in list(getattr(self, "_btns", [])):
                    if b.handle_event(evt, 0):
                        return True
                return True
            return True
        if event.type == pygame.KEYDOWN:
            # forward to focused numeric input if any
            for inp in list(getattr(self, "_inputs", [])):
                if getattr(inp, 'state', {}).get('editing'):
                    if inp.handle_event(event):
                        return True
        return False

    # -------------------------------------------------------------- inline numeric entry
    class _NumericEntry:
        def __init__(self, rect: pygame.Rect, get_value, set_value, font, state: dict):
            self.rect = rect
            self.get_value = get_value
            self.set_value = set_value
            self.font = font
            self.state = state

        def draw(self, surf: pygame.Surface):
            pygame.draw.rect(surf, theme.BG_INPUT, self.rect, border_radius=6)
            pygame.draw.rect(surf, theme.BORDER, self.rect, 1, border_radius=6)
            txt = self.state.get("text") if self.state.get("editing") else str(self.get_value())
            img = self.font.render(txt, True, theme.TEXT)
            surf.blit(img, img.get_rect(center=self.rect.center))

        def handle_event(self, event: pygame.event.Event) -> bool:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect.collidepoint(event.pos):
                    self.state["editing"] = True
                    self.state["text"] = ""
                    return True
            if event.type == pygame.KEYDOWN and self.state.get("editing"):
                if event.key == pygame.K_RETURN:
                    try:
                        self.set_value(int(self.state.get("text") or 0))
                    except Exception:
                        pass
                    self.state["editing"] = False
                    return True
                elif event.key == pygame.K_ESCAPE:
                    self.state["editing"] = False
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.state["text"] = (self.state.get("text") or "")[:-1]
                    return True
                else:
                    ch = event.unicode
                    if ch and ch in "0123456789":
                        self.state["text"] = (self.state.get("text") or "") + ch
                        return True
            return False

    def _draw_numeric_entry(self, surf: pygame.Surface, rect: pygame.Rect, get_value, set_value, key: str):
        state = self._input_state.setdefault(key, {"editing": False, "text": ""})
        entry = EventsModal._NumericEntry(rect, get_value, set_value, self.app.font, state)
        entry.draw(surf)
        self._inputs.append(entry)
