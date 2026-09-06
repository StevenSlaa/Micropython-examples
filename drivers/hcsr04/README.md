# HC-SR04

Ultrasonic distance driver for the HC-SR04. The sensor range is 2cm to 400cm; readings outside
that range raise `OSError('Out of range')`.

## Install

Install it from the Pulsar IoT library panel, or copy `hcsr04.py` to `/lib` on the board.

## Usage

```python
from hcsr04 import HCSR04

sensor = HCSR04(trigger_pin=5, echo_pin=18)
print(sensor.distance_cm())
```

Protect the echo pin with a 1k resistor. Pass `echo_timeout_us` if your sensor variant has a
different maximum range.

## Credits

Written by Roberto Sánchez, Apache-2.0 — <https://github.com/rsc1975/micropython-hcsr04>.

Used by: [ultrasonic-distance-sensor-hc-sr04](../../examples/ultrasonic-distance-sensor-hc-sr04)
