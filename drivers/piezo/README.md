---
driver: piezo
author: Steven Slaa
---

# Piezo buzzer

## What it is

A piezo buzzer makes sound with a thin disc of piezoelectric ceramic glued to a metal plate. Put a
voltage across the ceramic and it bends; switch the voltage on and off quickly and the plate
vibrates and pushes the air. How fast you switch it is the pitch you hear. They are cheap, draw
only a few milliamps, and are the usual way to give a project a beep, an alarm or a little tune.

They come in two kinds that look almost the same, and this driver handles both:

| | Passive | Active |
| --- | --- | --- |
| Inside | just the piezo element | the element plus its own oscillator |
| How it is driven | a square wave from PWM | on and off, like an LED |
| Pitch | anything you ask for, so it plays melodies | one fixed pitch, usually around 2.3kHz |
| Underneath | green circuit board visible | sealed with black filling |
| On a battery | a single click | a continuous beep |
| In the driver | `Piezo(pin)` | `Piezo(pin, active=True)` |

## Install

Install it from the Pulsar IoT library panel, or copy `piezo.py` to `/lib` on the board.

## Usage

```python
from machine import Pin
from piezo import Piezo

piezo = Piezo(Pin(18))

piezo.tone(2000, 100)                      # 2000Hz for 100ms, then silence
piezo.play("C5 C5 G5 G5 A5 A5 G5:2")       # a melody, returns when it is done
piezo.play("E5:0.5 E5:0.5 R E5", tempo=180)

piezo.tone(440)                            # keeps sounding...
piezo.stop()                               # ...until this
```

For an active buzzer, pass `active=True`. `tone()` and `play()` still work, but every note comes
out at the buzzer's own pitch, so a melody becomes its rhythm.

## Melodies

A melody is a string of notes separated by spaces:

| Written | Means |
| --- | --- |
| `C5` | the note C in octave 5, one beat |
| `F#4`, `Bb4` | sharps with `#`, flats with `b` |
| `A4:2` | two beats |
| `A4:0.5` | half a beat |
| `R`, `R:2` | a rest of one beat, two beats |

`tempo` is beats per minute and defaults to 120, which makes one beat half a second. `A4` is
440Hz, and `note_frequency("C#5")` gives you the frequency of any note name if you would rather
call `tone()` yourself.

The whole melody is checked before it starts, so a typo raises a `ValueError` straight away
instead of stopping the tune halfway through.

## Settings

| Argument | Default | What it does |
| --- | --- | --- |
| `active` | `False` | `True` for an active buzzer |
| `volume` | `1.0` | 0.0 to 1.0, passive buzzers only |
| `gap_ms` | `20` | the silence at the end of each note, so `C5 C5` is heard as two notes instead of one long one. Raise it for a more staccato sound |

All three can be changed on the object later, for example `piezo.volume = 0.3`.

## Notes

- **It always goes quiet.** Every `tone()` with a duration and every `play()` silences the
  buzzer in a `finally`, so pressing Ctrl+C in the middle of a melody does not leave it
  screaming. The one exception is `tone()` without a duration: that is meant to keep going, so
  call `stop()` yourself.
- **Loudness depends on pitch.** Small buzzers are loudest between roughly 2kHz and 4kHz, and
  quiet below 500Hz. A melody in octave 5 or 6 carries much better than the same tune in
  octave 4.
- **Volume is not a smooth scale.** It narrows the pulse, and a piezo is loudest at a 50% square
  wave, which is `1.0`. Values down to about `0.1` still sound nearly as loud; the difference
  is mostly below that.
- **On a Pico, pins share PWM.** GP18 and GP19 are one PWM channel, and so are every other
  neighbouring pair. Use them for two different PWM things and changing the buzzer's pitch
  changes the other's frequency too.
- `tone()` and `play()` block until they finish. On a board that has to do something else at the
  same time, use `tone(frequency)` and `stop()` from your own loop.

## Tests

`python3 -B drivers/piezo/test_piezo.py` checks the note frequencies, the melody parser, the
order of sound, gaps and silence, and that an interrupted tone goes quiet, off-board.

Used by: [piezo-buzzer](../../examples/piezo-buzzer)
