---
driver: sy6970
author: Steven Slaa
---

# SY6970 battery charger

Driver for the Silergy SY6970, a charger for a single LiPo cell with a power path: it runs the board
from USB and charges the battery at the same time, and runs the board from the battery when USB is
unplugged. LilyGO fits it to boards such as the T-Display-S3 Long, at I2C address 0x6A.

The chip works without any software, but two of its defaults cause trouble, and this driver deals
with them:

- It has a **watchdog** that resets all its settings every 40 seconds unless software keeps talking
  to it. The driver switches the watchdog off, so settings you make stay.
- It **keeps trying to charge** even when no battery is connected. Switch charging off in that case:
  on a T-Display-S3 Long without a battery, charging left on froze the board after a few minutes.

## Install

Install it from the Pulsar IoT library panel, or copy `sy6970.py` to `/lib` on the board.

## Usage

```python
from machine import I2C, Pin
from sy6970 import SY6970

charger = SY6970(I2C(0, scl=Pin(10), sda=Pin(15)))  # the T-Display-S3 Long's I2C pins

charger.charge_enabled = False   # no battery connected

print(charger.input)             # what powers the board: "USB host", "adapter", "none", ...
print(charger.input_voltage)     # mV, 0 without input
print(charger.system_voltage)    # mV, what the chip supplies to the board
print(charger.battery_voltage)   # mV, 0 when there is nothing to measure
print(charger.charge_state)      # "not charging", "pre-charge", "fast charging" or "charged"
print(charger.charge_current)    # mA into the battery
```

The readings are measured by the chip itself, once a second; the driver switches that on.

## Settings

| Property | Range | Default on the tested board |
| --- | --- | --- |
| `charge_enabled` | `True` or `False` | `True` |
| `charge_current_limit` | 0 to 5056 mA, steps of 64 | 2048 mA |
| `charge_voltage` | 3840 to 4608 mV, steps of 16 | 4208 mV |
| `input_current_limit` | 100 to 3250 mA, steps of 50 | depends on what is plugged in |

Values round down to the chip's steps and are clamped to its range.

**Use a charge current your battery can take.** A common rule for LiPo cells is at most the battery's
capacity per hour, so 500 mA or less for a 500 mAh cell:

```python
charger.charge_current_limit = 448   # 500 rounds down to 448 as well
```

The chip itself resets the settings when it loses power completely, for example when both USB and
the battery are disconnected. Set them each time your program starts.

## Faults

`charger.faults` returns the fault register; 0 means none. The chip clears it when it is read, so
read it once and keep the value.

| Bit | Meaning |
| --- | --- |
| `0x80` | the watchdog expired (only when it is on) |
| `0x40` | boost fault, when the battery powers USB devices |
| `0x30` | charge fault: input, temperature or safety timer |
| `0x08` | battery over-voltage, also seen when no battery is connected |
| `0x07` | temperature sensor out of range |

With `watchdog=True` the chip's watchdog stays on. It then needs to be talked to at least every 40
seconds, or its settings go back to their defaults.

## Tested

- LilyGO T-Display-S3 Long running MicroPython 1.29.0, on USB without a battery, with charging
  switched off: `input` "adapter", `input_voltage` 5300 mV, `system_voltage` 3664 mV,
  `battery_voltage` 0, `charge_state` "not charging" and no faults. The limits read back as the
  chip's defaults: 2048 mA charge current, 500 mA input current and 4208 mV charge voltage.

## Credits

The register map and scaling come from lewisxhe's
[XPowersLib](https://github.com/lewisxhe/XPowersLib), which also has the SY6970 datasheet. The chip
is register compatible with TI's BQ25895.
