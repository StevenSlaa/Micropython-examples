# MFRC522 RFID (RC522)

Reads and writes MIFARE Classic 1k cards and tags with the blue RFID-RC522 board, over SPI.

## Install

Install it from the Pulsar IoT library panel, or copy `mfrc522.py` to `/lib` on the board.

## Wiring

The pin marked SDA on the module is the SPI chip select. Any GPIO works for all five signals;
these are just the ones used below.

| RC522 | ESP32 | Pico |
| --- | --- | --- |
| SCK | 18 | 18 |
| MOSI | 23 | 19 |
| MISO | 19 | 16 |
| RST | 4 | 20 |
| SDA (CS) | 5 | 17 |
| 3.3V | 3V3 | 3V3 |
| GND | GND | GND |

## Usage

Reading the id of whatever card is held against the reader:

```python
from time import sleep
from mfrc522 import MFRC522, uid_hex

reader = MFRC522(sck=18, mosi=23, miso=19, rst=4, cs=5)

while True:
    serial = reader.scan()
    if serial:
        print("card", uid_hex(serial))
    sleep(0.2)
```

Reading and writing a block, which needs authentication first:

```python
KEY = [0xFF] * 6            # the factory key of a blank card
BLOCK = 8

serial = reader.scan()
if serial and reader.select_tag(serial) == reader.OK:
    if reader.auth(reader.AUTHENT1A, BLOCK, KEY, serial) == reader.OK:
        print(reader.read(BLOCK))
        reader.write(BLOCK, [0x01] * 16)
    reader.stop_crypto1()   # always, or the next card will not authenticate
```

## Notes

- The module is 3.3V only. The 5V pin on the header is not a supply input, and feeding the
  logic 5V is the usual way these boards die.
- `scan()` returns a 5 byte serial: 4 bytes of card id plus a checksum. `uid_hex()` prints the
  id part; `select_tag()` and `auth()` want the whole thing.
- Blocks are 16 bytes. Every fourth block (3, 7, 11, …) is the sector trailer holding the keys
  and access bits — writing one with the wrong bytes bricks that sector permanently.
- Call `stop_crypto1()` after you are done with a card. Without it the reader stays in an
  encrypted session and the next authentication fails.
- Cheap modules vary in antenna tuning. If cards only read when touching the module, that is
  the hardware, not the code; lowering `baudrate` will not help but a different module will.
- The driver defaults to `SoftSPI`, which works on every port and every pin. Pass a
  `machine.SPI` instance as `spi=` to use a hardware bus.

## Tests

`python3 -B drivers/mfrc522/test_mfrc522.py` checks the constructor and the id helper off-board.

Used by: [spi-rfid-rc522](../../examples/spi-rfid-rc522)

## Credits

From [wendlers/micropython-mfrc522](https://github.com/wendlers/micropython-mfrc522), MIT,
Copyright 2016 Stefan Wendler. The constructor was changed to build a `SoftSPI` bus rather than
branching on `uname()`, which limited the original to the ESP8266 and the WiPy, and `scan()`
and `uid_hex()` were added.
