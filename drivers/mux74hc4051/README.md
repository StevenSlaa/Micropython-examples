---
driver: mux74hc4051
author: Steven Slaa
---

# 74HC4051 analog multiplexer

## What it is

The 74HC4051 is an eight channel analog multiplexer: an electronic rotary switch. Three select
pins, S0 to S2, choose which one of the eight channels Y0 to Y7 is connected to the common pin Z.
Three pins give eight combinations, so three outputs from the board control eight connections.

The usual reason to use one is to run out of analog inputs. A Pico has three and an ESP32 a
handful; with a 74HC4051 in front of one of them you can read eight potentiometers, light
sensors or soil probes, one after another. Because the switch conducts both ways, it works just
as well the other way round, sending one signal out to eight places, and for digital signals as
well as analog ones.

| | |
| --- | --- |
| Channels | 8 (Y0 to Y7), one connected to Z at a time |
| Select pins | S0, S1, S2, plus E (enable, active low) |
| Supply | 2V to 6V; use 3.3V with a 3.3V board |
| Switch resistance | roughly 100Ω at 5V, more at 3.3V |
| Signal range | between VEE and VCC, so 0 to 3.3V with VEE on GND |
| Also sold as | CD74HC4051, 74HCT4051, and on "8 channel analog multiplexer" breakouts |

Pinout of the 16 pin chip:

| Pin | Name | | Pin | Name |
| --- | --- | --- | --- | --- |
| 1 | Y4 | | 16 | VCC |
| 2 | Y6 | | 15 | Y2 |
| 3 | Z (common) | | 14 | Y1 |
| 4 | Y7 | | 13 | Y0 |
| 5 | Y5 | | 12 | Y3 |
| 6 | E (enable) | | 11 | S0 |
| 7 | VEE | | 10 | S1 |
| 8 | GND | | 9 | S2 |

## Install

Install it from the Pulsar IoT library panel, or copy `mux74hc4051.py` to `/lib` on the board.

## Usage

```python
from machine import ADC, Pin
from mux74hc4051 import Mux74HC4051

adc = ADC(Pin(26))                                  # Z goes to an analog pin
mux = Mux74HC4051(Pin(2), Pin(3), Pin(4), enable=Pin(5), adc=adc)

print(mux.read(3))          # channel Y3, 0 to 65535
print(mux.read_all())       # all eight, Y0 first
```

On an ESP32, call `adc.atten(ADC.ATTN_11DB)` first so the ADC measures the full 0 to 3.3V.

Without an ADC, just choose the channel and use Z however you like, for example as a digital
input or output:

```python
mux = Mux74HC4051(Pin(2), Pin(3), Pin(4))
mux.channel = 6             # Y6 is now connected to Z
```

| | |
| --- | --- |
| `channel` | the channel connected to Z, 0 to 7. Set it to switch |
| `enabled` | `False` disconnects all channels from Z. Needs `enable=` |
| `read(channel)` | switches, waits `settle_ms`, returns `adc.read_u16()` |
| `read_all()` | a list of all eight readings |
| `settle_ms` | the wait after switching, default 1ms |

## Notes

- **Wire E to GND if you do not give an enable pin.** E is active low, and left floating the chip
  may switch itself off at random.
- **Tie VEE to GND.** VEE is the lower end of the signal range; it only goes below ground for
  negative signals, which need a separate negative supply.
- **Power it from 3.3V.** At 5V the select pins need more than 3.3V to see a high, and Z could
  put 5V on your board's analog pin. The 74HCT4051 only runs from 4.5V to 5.5V, so with a 3.3V
  board use the HC version.
- **Switching is break before make when there is an enable pin.** The select pins cannot all
  change at once, so between two channels the chip briefly connects the channels in between. The
  driver switches it off during the change. For reading sensors that does not matter; for sending
  a signal out to eight places it does.
- **Unused channels read noise.** A channel with nothing connected floats and gives random
  values. Connect unused channels to GND.
- **Sensors with a high output resistance need a longer `settle_ms`.** The ADC has to charge
  through the sensor, the switch and whatever the previous channel left behind. If a reading
  seems to follow the channel before it, raise `settle_ms` to 5 or 10.
- Keep the signal between VEE and VCC, and the current through a channel under about 25mA.
  A signal outside that range leaks into the other channels.

## Tests

`python3 -B drivers/mux74hc4051/test_mux74hc4051.py` checks the select pin bit order, the break
before make sequence, settling and the enable pin, off-board.

Used by: [mux-74hc4051](../../examples/mux-74hc4051)
