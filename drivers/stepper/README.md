# Stepper motor (ULN2003, A4988)

A stepper does not spin while power is applied. It moves a fixed fraction of a turn per step and
then holds there, which means you can know where the shaft is without any sensor — as long as
nothing has stopped it.

Two wirings are covered, because both are everywhere:

| Class | Wiring | Typical parts |
| --- | --- | --- |
| `UnipolarStepper` | four pins straight to the coils | 28BYJ-48 with a ULN2003 board, or any stepper on an L293D or L298N |
| `StepDirStepper` | two pins, step and direction | A4988, DRV8825, TMC2208 with a NEMA 17 |

## Install

Install it from the Pulsar IoT library panel, or copy `stepper.py` to `/lib` on the board.

## A 28BYJ-48 on a ULN2003 board

The small blue motor and its board, and the reason most people meet steppers at all.

```python
from machine import Pin
from stepper import UnipolarStepper

motor = UnipolarStepper([Pin(pin) for pin in (13, 12, 14, 27)])

motor.step(2048)        # half a turn, since it is 4096 half steps per revolution
motor.angle = 90        # or say it in degrees
motor.move_to(0)        # back to where it started
motor.release()         # let go: it holds and gets warm until you do
```

## A NEMA 17 on an A4988 or DRV8825

```python
from machine import Pin
from stepper import StepDirStepper

motor = StepDirStepper(step=Pin(13), direction=Pin(12), enable=Pin(14),
                       steps_per_revolution=200, rpm=60)

motor.angle = 360
motor.release()
```

Microstepping is set with jumpers on those boards, not in software, so a driver set to sixteenth
steps needs `steps_per_revolution=200 * 16`.

## Steps per revolution

This number is the whole of the driver's idea of where the shaft is, so it is worth getting
right:

| Motor | Steps per revolution |
| --- | --- |
| 28BYJ-48, half stepping (the default) | 4096 |
| 28BYJ-48, full stepping | 2048 |
| NEMA 17 and most bipolar steppers | 200 |
| Any of the above with microstepping | multiply by the microstep setting |

The 28BYJ-48's figures include its internal gearbox. That gearbox is really 63.68395:1 rather
than the 64:1 everyone quotes, so a "full revolution" of 4096 steps is out by about half a
percent — a degree and a bit. It never matters for one turn and it accumulates over hundreds, so
if you need a shaft to come back to exactly the same place, tune `steps_per_revolution` by hand
rather than trusting the round number.

## Stepping sequences

`sequence=` chooses how the coils are walked, and it is a trade rather than a setting with a
right answer:

| Sequence | Coils on | Steps per revolution | Notes |
| --- | --- | --- | --- |
| `HALF` (default) | one or two, alternating | 4096 on a 28BYJ-48 | Smoothest and quietest, half the top speed |
| `FULL` | two | 2048 | About 40% more torque, twice the current |
| `WAVE` | one | 2048 | Least current, least torque, misses steps under load |

## Notes

- **Do not run a stepper from the board's supply.** A 28BYJ-48 wants 5V and around 250mA, and a
  NEMA 17 far more. Give it its own supply and join the grounds.
- **Position is counted, not measured.** If something stops the shaft, the motor misses steps
  and the count silently becomes wrong. There is no way for the driver to know; that is the
  price of having no sensor.
- **Releasing matters.** A stopped stepper holds its position by keeping current in the coils.
  It will be warm to the touch and will stay that way. `release()` gives that up — along with
  the holding torque, so anything the motor was supporting will move.
- `step()` blocks until it has finished, so a full turn at 10rpm holds up your program for six
  seconds. Stepping a little at a time inside your own loop is how to do something else
  meanwhile.
- Asking for more rpm than the motor can manage makes it buzz and sit still rather than going
  faster. A 28BYJ-48 runs out at about 15rpm.
- **If it hums and vibrates instead of turning**, two of the four coil wires are swapped. Try
  `[Pin(13), Pin(14), Pin(12), Pin(27)]` — swapping the middle two is the usual fix, because
  ULN2003 boards do not all order their outputs the same way.

## Tests

`python3 -B drivers/stepper/test_stepper.py` reads the coil patterns back as the motor would see
them and checks the sequences, the direction, the position bookkeeping and the step pulses,
off-board.

Used by: [stepper](../../examples/stepper)
