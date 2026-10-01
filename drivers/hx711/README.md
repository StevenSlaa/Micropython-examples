---
driver: hx711
author: Steven Slaa
---

# HX711 load cell amplifier

## What it is

The HX711 is a 24 bit analog to digital converter made by Avia Semiconductor for one job:
reading load cells, the strain gauge bars inside kitchen and bathroom scales. A load cell's
output changes by a few millionths of a volt per gram, far too little for a microcontroller's
own ADC. The HX711 amplifies it up to 128 times and measures it with 24 bits.

It is sold on small green or red boards, often bundled with a load cell. The board has four
pins to the load cell (E+, E-, A-, A+) and four to the microcontroller (VCC, GND, DT, SCK).

| | |
| --- | --- |
| Measures | differential voltage from a load cell bridge |
| Resolution | 24 bits, signed: -8 388 608 to 8 388 607 |
| Channels | A at gain 128 or 64, B at gain 32 |
| Rate | 10 readings per second, or 80 with the RATE pin high |
| Supply | 2.6V to 5.5V |
| Interface | two wire serial of its own: DOUT (DT on the board) and PD_SCK (SCK) |

## Install

Install it from the Pulsar IoT library panel, or copy `hx711.py` to `/lib` on the board.

## Usage

```python
from hx711 import HX711

sensor = HX711(dout=16, pd_sck=17)

sensor.tare()               # with the scale empty
sensor.calibrate(500)       # with 500 g on it; returns the scale to save
print(sensor.weight())      # in grams, the unit calibrate() was given

print(sensor.read_raw())    # one raw 24 bit reading
```

Calibrating once and passing the numbers back in skips it on the next boot:

```python
sensor = HX711(16, 17, scale=419.8)   # scale from calibrate()
sensor.tare()                         # the zero drifts, so tare on each start anyway
```

| Method | Returns |
| --- | --- |
| `read_raw()` | one raw reading |
| `read(samples=5)` | the average of the middle half of `samples` raw readings |
| `weight(samples=5)` | `(read() - offset) / scale` |
| `tare(samples=15)` | sets and returns `offset` |
| `calibrate(known_weight, samples=15)` | sets and returns `scale` |
| `is_ready()` | `True` when a reading is waiting, for code that must not block |
| `power_down()`, `power_up()` | sleep under 1uA, and wake |

`gain` is a property: set it to 128 or 64 for channel A, or 32 for channel B.

## Notes

- A reading takes up to 100ms at the usual 10 per second, and the driver waits for it. Use
  `is_ready()` first if the loop has other work to do.
- The chip powers down if the clock stays high for over 60us. The driver turns interrupts off
  for the half millisecond it takes to clock a reading out, so a WiFi interrupt cannot do that
  mid-read.
- `read()` sorts the samples and averages only the middle half, so a single bad reading, which
  bit-banged serial produces now and then, is thrown out instead of skewing the result.
- A negative weight under load means the load cell is wired or mounted the other way round.
  `calibrate()` then returns a negative scale and weights come out positive anyway; swap A+ and
  A- if you prefer positive raw numbers.
- A load cell creeps: the zero drifts a little with temperature and after a heavy load. Tare on
  start, and again whenever it matters.
- A raw reading of 8 388 607 or -8 388 608 means the input is out of range: check the wiring,
  or the load is over what the cell is rated for.
- Many cheap boards tie RATE to GND for 10 readings a second. 80 a second is noisier; it needs
  RATE lifted and wired to VCC on the board.
- Power the board from 3V3 so DT stays at 3.3V logic.

## Tests

`python3 -B drivers/hx711/test_hx711.py` runs the driver against a fake HX711, checking the bit
order and sign, the gain pulses, the glitch-resistant average and the tare and calibration maths,
off-board.

Written from the [Avia Semiconductor HX711 datasheet](https://cdn.sparkfun.com/datasheets/Sensors/ForceFlex/hx711_english.pdf).
