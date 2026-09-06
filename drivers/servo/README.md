# Hobby servo

Drives the three wire hobby servos — SG90, MG996R, DM-S0306D, TS90M and the rest of them.

## The one thing that makes a servo different

Everything else driven by PWM cares about the **duty cycle**: what fraction of the time the pin
is on. A servo does not. It measures how long each individual pulse lasts, and ignores the rest
of the cycle entirely.

Pulses arrive 50 times a second, and their length is the instruction:

| Pulse | A positional servo | A continuous rotation servo |
| --- | --- | --- |
| ~1.0ms | one end of its travel | full speed one way |
| ~1.5ms | the middle | stopped |
| ~2.0ms | the other end | full speed the other way |

That is why this driver talks in microseconds and degrees rather than duty, and why the same
class handles both kinds of servo: they are the same signal and the same hardware. Only the
electronics inside the continuous one have been changed to read the pulse as a speed.

## Install

Install it from the Pulsar IoT library panel, or copy `servo.py` to `/lib` on the board.

## A positional servo

```python
from machine import Pin
from servo import Servo

arm = Servo(Pin(17))

arm.angle = 0
arm.angle = 90
arm.angle = 180
print(arm.angle)     # what it was last told
arm.release()        # stop holding
```

## A continuous rotation servo

These have no travel to reach, so give them the narrower range they expect:

```python
wheel = Servo(Pin(17), min_us=1000, max_us=2000)

wheel.speed = 1.0     # full speed one way
wheel.speed = -0.4    # slowly the other
wheel.speed = 0       # actively holding still
wheel.release()       # coasting, not holding
```

## Measuring your servo

The defaults are a starting point, not a specification. Two knobs are worth setting once:

**`min_us` and `max_us`** are the pulses at the two ends of the travel. The 500 to 2500 default
reaches the full sweep of most positional servos. The 1000 to 2000 the datasheets quote usually
falls short at both ends. If your servo buzzes and strains at 0 or 180 it is being pushed past
its stop: bring these in. If it never quite reaches either end, widen them.

**`stop_us`** is where a continuous rotation servo stands still, and it is rarely exactly the
middle. A servo that creeps when told `speed = 0` wants this trimmed by a few tens of
microseconds:

```python
wheel = Servo(Pin(17), min_us=1000, max_us=2000, stop_us=1480)
```

Full speed each way is still reached: the driver measures out from wherever stop is.

## Notes

- **Do not power a servo from the board's 3.3V pin.** Even a small SG90 pulls several hundred
  milliamps when it starts moving, and far more if something stops it. That drop resets the
  board. Give it 5V of its own and join the grounds.
- The signal wire is happy at 3.3V from an ESP32 or a Pico even though the servo runs on 5V.
- Wire colours are near enough standard: brown or black is ground, red is power, and the pale
  one — orange, yellow or white — is the signal.
- `release()` stops the pulses. A positional servo goes limp and stops buzzing and drawing
  current; a continuous one coasts. It is not the same as `speed = 0`, which keeps a continuous
  servo actively resisting being turned.
- `angle` and `speed` report what the servo was last told, not where it is. A servo has no way
  to tell you it was stopped by something.
- Movement is not instant. Reaching the other end takes a few tenths of a second, and reading
  `angle` back immediately will not tell you it has arrived.
- `pulse_us` is there directly for a servo that wants something none of the above describes.

## Tests

`python3 -B drivers/servo/test_servo.py` checks the angle and speed maths in microseconds, the
clamping, the trimmed stop point and releasing, off-board.

Used by: [servo](../../examples/servo)
