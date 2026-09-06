# DC motor on an H bridge (L293D, L298N)

Speed and direction for a DC motor on an H bridge.

One driver covers the L293D, the L298N module, the DRV8833 and the TB6612, because from the
board's side they are the same thing: two direction pins and, usually, an enable pin that takes
PWM for the speed. Where they differ is electrical, and no code can change it:

| | L293D | L298N module |
| --- | --- | --- |
| Current per motor | 600mA, 1.2A peak | 2A |
| Voltage lost in the bridge | about 1.9V | about 2V, and it gets hot |
| Flyback diodes | built in, the D in the name | on the module |
| Form | a 16 pin chip you wire yourself | a board with screw terminals |
| Enable | a pin per motor | a pin per motor, jumpered high by default |

The voltage the bridge drops is the thing people are caught by: a 6V motor on an L298N from a
6V supply sees about 4V and feels weak. Give it a supply a couple of volts higher, or use a
MOSFET based driver such as the DRV8833 or TB6612 instead, which lose a few tenths.

## Install

Install it from the Pulsar IoT library panel, or copy `motor.py` to `/lib` on the board.

## Usage

```python
from machine import Pin
from motor import Motor

left = Motor(Pin(12), Pin(14), enable=Pin(13))

left.speed = 1.0      # full forward
left.speed = -0.35    # a third of the way backwards
left.speed = 0        # coast
left.brake()          # stop sharply
```

Two motors are two objects. A robot whose motors face opposite ways can still take the same
numbers on both sides:

```python
left = Motor(Pin(12), Pin(14), Pin(13))
right = Motor(Pin(26), Pin(27), Pin(25), reverse=True)

left.speed = right.speed = 0.6     # both go forwards
```

## If the enable pin is jumpered

L298N modules ship with jumpers holding ENA and ENB high, and some L293D wirings tie enable to
3.3V. Leave `enable` out and the driver puts the PWM on whichever direction pin is driving,
which controls the speed just as well:

```python
motor = Motor(Pin(12), Pin(14))   # no enable: both pins must be PWM capable
```

## Notes

- **Never power a motor from the board's 3.3V or from USB.** Motors put spikes back down the
  supply that reset a microcontroller, and stall currents are far past what a USB port gives.
  Use a separate supply for the motor and join the grounds.
- `minimum` is worth setting. Every motor has a speed below which it only hums without turning;
  `Motor(..., minimum=0.35)` lifts the bottom of the range above that, so `speed = 0.05` still
  moves the shaft slowly instead of doing nothing.
- `brake()` shorts the motor's own windings to stop it sharply, where `speed = 0` lets it coast.
  Braking a large motor from full speed over and over puts that energy into the bridge as heat,
  which is one way an L298N ends up too hot to touch.
- Reading `speed` gives what you asked for. There is no feedback from the motor: an H bridge
  cannot tell you it is stalled, or that the wheel is off the ground.
- 1000Hz suits most small motors. A frequency in the low hundreds makes them whine audibly;
  much higher wastes power in the switching. `frequency=` if yours prefers otherwise.
- A bipolar stepper on an L293D is a different job and this driver does not do it.

## Tests

`python3 -B drivers/motor/test_motor.py` checks the pin levels and duty cycles for both wirings
and every state, off-board.

Used by: [dc-motor-l293d](../../examples/dc-motor-l293d)
