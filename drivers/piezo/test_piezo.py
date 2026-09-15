# Run with: python3 -B drivers/piezo/test_piezo.py
# A fake PWM, pin and sleep that write to one timeline, so the order of sound, silence and waiting
# can be checked off-board.
import sys, types

events = []


class _PWM:
    def __init__(self, pin, freq=None, duty_u16=None):
        events.append(("init", freq, duty_u16))

    def freq(self, value):
        events.append(("freq", value))

    def duty_u16(self, value):
        events.append(("duty", value))


class _Pin:
    OUT = 1

    def init(self, mode, value=None):
        events.append(("pin", mode, value))

    def value(self, value):
        events.append(("value", value))


def _sleep_ms(ms):
    events.append(("sleep", ms))


sys.modules["machine"] = types.SimpleNamespace(PWM=_PWM)
sys.modules["time"] = types.SimpleNamespace(sleep_ms=_sleep_ms)
import piezo  # noqa: E402
from piezo import Piezo, note_frequency  # noqa: E402

# Notes are tuned to A4 = 440Hz, and a sharp and a flat can name the same pitch.
assert note_frequency("A4") == 440
assert note_frequency("A5") == 880
assert note_frequency("C4") == 262
assert note_frequency("C#4") == note_frequency("Db4") == 277
assert note_frequency("Bb3") == 233
assert note_frequency("a") == 440, "lower case, and octave 4 when it is left out"
for bad in ("H4", "", "C4.5", "Cx4"):
    try:
        note_frequency(bad)
        raise AssertionError("not a note: %r" % bad)
    except ValueError:
        pass

# A passive buzzer starts silent, so creating it does not click.
events.clear()
buzzer = Piezo(object())
assert events == [("init", 1000, 0)], events

# A tone: pitch, a 50% square wave, the wait, then silence.
events.clear()
buzzer.tone(2000, 100)
assert events == [("freq", 2000), ("duty", 32768), ("sleep", 100), ("duty", 0)], events

# Without a duration it keeps sounding until stop().
events.clear()
buzzer.tone(1000)
assert events == [("freq", 1000), ("duty", 32768)], events
buzzer.stop()
assert events[-1] == ("duty", 0)


# Ctrl+C in the middle of a tone still silences it.
def _interrupted(ms):
    raise KeyboardInterrupt


piezo.sleep_ms = _interrupted
try:
    buzzer.tone(2000, 100)
except KeyboardInterrupt:
    pass
assert events[-1] == ("duty", 0), "interrupted, and silent"
piezo.sleep_ms = _sleep_ms

# A melody at 120 beats per minute: a beat is 500ms, a note ends in a 20ms gap, a rest is silent.
events.clear()
buzzer.play("A4 R:0.5 A5:2", tempo=120)
assert events == [
    ("freq", 440), ("duty", 32768), ("sleep", 480), ("duty", 0), ("sleep", 20),
    ("sleep", 250),
    ("freq", 880), ("duty", 32768), ("sleep", 980), ("duty", 0), ("sleep", 20),
    ("duty", 0),
], events

# A typo anywhere is refused before a single note plays.
for bad in ("C5 D5 X5", "C5:0", "C5:fast"):
    events.clear()
    try:
        buzzer.play(bad)
        raise AssertionError("a bad melody must be refused: %r" % bad)
    except ValueError:
        pass
    assert events == [], "nothing played for %r" % bad

# Volume narrows the pulse, and zero is silence.
events.clear()
Piezo(object(), volume=0.5).tone(1000)
assert events[-1] == ("duty", 16384), events
events.clear()
Piezo(object(), volume=0).tone(1000)
assert events[-1] == ("duty", 0), events

# An active buzzer is switched like an LED, and makes its own pitch.
events.clear()
beeper = Piezo(_Pin(), active=True)
assert events == [("pin", 1, 0)], events
events.clear()
beeper.tone(2000, 50)
assert events == [("value", 1), ("sleep", 50), ("value", 0)], events

print("piezo: ok")
