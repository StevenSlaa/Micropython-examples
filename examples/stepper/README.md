---
example: stepper
author: Steven Slaa
---

# Stepper Motor

In this example the microcontroller turns a stepper a quarter turn at a time all the way round,
returns it to where it started, and then releases it.

A stepper is worth the extra wires because it moves a known amount and then holds there. No
sensor is needed to know where the shaft is — as long as nothing stops it, which is the catch
worth understanding before you rely on one.

Set `wiring` at the top of the script to match what you have:

- **`"uln2003"`** — the small blue 28BYJ-48 and its driver board, or any stepper on an L293D or
  L298N. Four pins straight to the coils.
- **`"stepdir"`** — an A4988, DRV8825 or TMC2208 driving a NEMA 17. Two pins: one pulse is one
  step.

## Requires
This example needs the [Stepper motor](../../drivers/stepper) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

### 28BYJ-48 on a ULN2003 board

| Board | ESP32 | Pico |
| --- | --- | --- |
| IN1 | 13 | 10 |
| IN2 | 12 | 11 |
| IN3 | 14 | 12 |
| IN4 | 27 | 13 |
| + | a separate 5V supply | a separate 5V supply |
| − | GND, shared with the board | GND, shared with the board |

The motor plugs into the white socket on the driver board; it only fits one way.

### A4988 or DRV8825

| Board | ESP32 | Pico |
| --- | --- | --- |
| STEP | 13 | 10 |
| DIR | 12 | 11 |
| EN | 14 | 12 |
| VMOT, GND | the motor supply, 8V to 35V | the motor supply, 8V to 35V |
| VDD, GND | 3V3 and GND | 3V3 and GND |

These boards need a current limit set with the little potentiometer before you run a motor for
any length of time, or the driver overheats and shuts down. They also want a large capacitor
across the motor supply, which is what the datasheet warns about in bold.

**Do not run either motor from the board's own supply.** A 28BYJ-48 pulls around 250mA and a
NEMA 17 far more, which browns the board out and resets it.

## Output
```
Steps per revolution: 4096
Angle: 90.0 degrees
Angle: 180.0 degrees
Angle: 270.0 degrees
Angle: 360.0 degrees
Angle: 0.0 degrees
Released
```

Each line appears when the move has finished, because stepping blocks: a full turn at 10rpm
takes six seconds and the program does nothing else meanwhile.

## Try it while it runs

While the `Released` pause is on, turn the shaft with your fingers. It moves freely. Do the same
a second earlier, while the motor is holding, and it resists — that holding is why a stopped
stepper is warm, and why `release()` is worth calling when you are done.

## If it hums but does not turn

Two of the four coil wires are the wrong way round. Swap the middle two pins in `coil_pins`:
`(13, 14, 12, 27)`. ULN2003 boards do not all order their outputs the same way, and this is by
far the most common problem with them.

If it turns but only weakly, or skips, drop `rpm`. A 28BYJ-48 runs out at about 15 and simply
buzzes above that.

## Plotter

Open the **Plotter** tab beside the REPL to see the angle as a staircase up to 360 and then
straight back to zero. It is what the motor was *told*, not where it is: a stepper cannot report
that something stopped it, which is exactly why the number can drift from reality.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
