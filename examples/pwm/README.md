---
example: pwm
author: Steven Slaa
---

# PWM (analog write)

This example will show you how to create a fading LED animation with a PWM Signal. 
This example can of course also be used to control servo's, motor drivers, buzzers, analog output, etc.

## What you will learn

- How a pin that only knows 0V and 3.3V can dim an LED
- What a duty cycle is, and what the frequency has to do with it
- Why a servo is the odd one out

## What an analog write is

A pin cannot output half a volt. It has two states, and that is all it has.

What it can do is switch between them very fast — thousands of times a second — and spend a
chosen share of that time on. Anything slower than the switching, which includes your eye, a
motor, and a heating element, cannot keep up with the individual pulses and responds to the
average instead. Half the time on looks like half brightness.

```python
led.duty_u16(0)       # off
led.duty_u16(32768)   # on half the time: half brightness
led.duty_u16(65535)   # fully on
```

That share is the duty cycle. It is not really dimming; it is [blinking](../blink)
too fast to see.

`freq()` decides how fast. Too slow and you see it as flicker rather than brightness — a few
hundred is the floor for a light. The 5000Hz here is comfortably past it.

**A servo is the exception.** It does not care about the share at all: it measures how long each
individual pulse lasts, and expects them 50 times a second. That is why the
[servo example](../servo) sets a frequency that would be useless for an LED.

## If it does not work

| What you see | What it usually means |
| --- | --- |
| The LED is on or off, with nothing between | The duty is only ever 0 or maximum. Print it and check it is changing |
| Visible flicker rather than dimming | The frequency is too low |
| The LED never goes fully dark | Some boards leak a little at very low duty; try 0 exactly |
| An error about PWM on this pin | Not every pin can do it on every board — try another |

## Connections

<img alt="connections" src="https://github.com/StevenSlaa/Micropython-examples/blob/f38e5477158664c2d6bfed5009aa8b868ddc54a6/PWM/res/circuit.png" height="300px">

## Output

The LED fades slowly in and back out. One step in eight is printed, so the console shows the
ramp without being flooded:

```
Duty: 0
Duty: 2048
Duty: 4096
Duty: 6144
```

The duty runs from 0 to 65535, the same range as the reading in the
[analog read example](../analog-read) — which is not a coincidence, and is what makes
[joining the two](../dimmer) so short.

## Plotter

Open the **Plotter** tab beside the REPL to see the duty cycle as a triangle wave, which is
exactly the ramp the LED brightness is following.

## Tested
This example has been tested on the following microcontroller running MicroPython:
- ESP32 Devkit v1
- ESP32S3 (FeatherS3)

---

**The five basics:** [1. Blink](../blink) · [2. Button](../button) · [3. Analog Read](../analog-read) · [5. Dimmer](../dimmer)
