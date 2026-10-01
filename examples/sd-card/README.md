---
example: sd-card
author: Steven Slaa
---

# SD Card

In this example the microcontroller mounts a microSD card, adds a line to a log file and reads
the whole file back. Run it a few times and the file grows by one line each run, because what is
on the card survives the power going.

## Requires
On an **ESP32** nothing: the firmware has SD card support built in, as `machine.SDCard`.

On other boards, like the **Pico**, install micropython-lib's `sdcard` driver once, from the REPL
with the board online, or with `mpremote mip install sdcard` from a computer:

```python
import mip
mip.install("sdcard")
```

The script picks whichever one the board has.

## Connections

Set the pins at the top of the script to match your board.

| Script setting | LilyGO T3 LoRa32 V1.6.1 | ESP32 + SD module | Pico + SD module |
| --- | --- | --- | --- |
| `sck_pin` | 14 | 18 | 18 |
| `mosi_pin` | 15 | 23 | 19 |
| `miso_pin` | 2 | 19 | 16 |
| `cs_pin` | 13 | 5 | 17 |

The module's pins may be labelled CLK for SCK, DI for MOSI and DO for MISO. Modules with a
regulator on board (usually the larger, full-size SD ones) take 5V on VCC; bare microSD breakouts
take 3.3V. GND to GND either way.

On a Pico the four pins must belong to SPI0, as the ones in the table do.

## Output
```
Size: 7948 MB  Free: 7931 MB
log.txt now holds:
Started, 1843 ms after boot
Started, 1852 ms after boot

Files on the card: ['log.txt']
```

## The card will not mount

- The card must be formatted **FAT32**. Cards over 32GB come as exFAT and have to be reformatted
  first.
- Push it in until it clicks, and check the wiring: MOSI and MISO swapped is the usual mistake.
- `ImportError: no module named 'sdcard'` means a board without built-in support and the driver
  not installed yet; see Requires.
- On an ESP32 already using `SPI(1)` for something else, like a LoRa radio, change `slot=2` to
  `slot=3` so the card uses the other SPI controller.

## Notes

- `os.umount("/sd")` before pulling the card out, or the last writes may never reach it. Writing
  with `with open(...)` closes each file straight away, which limits the damage if power goes.
- On ESP32 boards GPIO2 is also a boot pin. If uploading new firmware fails with a card wired to
  it, take the card out while flashing.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
