# P9813 RGB LED Example

In this example the microcontroller shows red, green and blue on a chain of P9813 RGB LED
modules to check the wiring, and then cycles a rainbow along the chain.

## Requires
This example needs the [P9813 RGB LED driver](../../drivers/p9813) installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

| Module | ESP32 | Pico |
| --- | --- | --- |
| CI (clock in) | 14 | 14 |
| DI (data in) | 13 | 15 |
| VCC | 5V | VBUS (5V) |
| GND | GND | GND |

The chips take 5V but accept 3.3V logic, as long as the grounds are joined. Chain more modules
from CO and DO to the next module's CI and DI, and set `leds_count` to match.

Data travels one way only. A chain wired into the out end lights nothing at all, which looks
exactly like a dead module.

## Output
```
Showing red
Showing green
Showing blue
Cycling
```

Then a rainbow moving along the chain. A module lighting green when the console says red has its
channels wired in another order.

## Power

`brightness` starts at 0.4. These are constant current drivers, so unlike a plain LED they do not
dim as the chain gets longer, and each one can take about 60mA at white. A few modules from a
USB port is fine; a long strip wants its own 5V supply with the ground shared.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
