# TC74 temperature

Reads temperature from a Microchip TC74 over I2C. The sensor is a small, cheap thermometer in a
three pin package: no calibration, no conversion maths, one signed byte of whole degrees.

## Install

Install it from the Pulsar IoT library panel, or copy `tc74.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, SoftI2C
from tc74 import TC74

sensor = TC74(SoftI2C(scl=Pin(22), sda=Pin(21)))
print(sensor.temperature, "C")
```

Sleeping between readings, which is most of the point of the part:

```python
sensor.standby = True           # a few microamps instead of a few hundred
...
sensor.standby = False
while not sensor.ready:         # the first conversion takes about a quarter of a second
    sleep_ms(50)
print(sensor.temperature)
```

## Notes

- The I2C address is fixed in the part number: TC74A0 is `0x48`, A1 `0x49`, and so on up to A7
  at `0x4F`. Pass `address=0x4A` for a TC74A2. Run the
  [i2c-scanner](../../examples/i2c-scanner) example if you are not sure which one you have.
- Readings are whole degrees, from -65 to 127. There is no fractional part to be had.
- Accuracy is about ±2°C, and the package reads its own die, so a warm regulator next to it
  shows up in the number. `TC74(i2c, offset=-3)` trims a reading against a thermometer you
  trust; the offset is added to every reading.
- `ready` is false until the first conversion after power-up or after waking from standby has
  finished. Reading before then gives you the previous value, not an error.
- `standby = True` freezes the temperature register as well as saving the power, so read first
  and sleep after.
