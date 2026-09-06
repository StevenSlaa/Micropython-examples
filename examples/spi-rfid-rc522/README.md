---
example: spi-rfid-rc522
author: Steven Slaa
---

# SPI RFID RC522 Example

In this example the microcontroller reads the id of any MIFARE card or tag held against an
RFID-RC522 reader, and prints the contents of one block from it.

## Requires
This example needs the [MFRC522 RFID (RC522)](../../drivers/mfrc522) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

The pin marked SDA on the module is the SPI chip select. The module runs on 3.3V; its 5V pin is
not a supply input.

| RC522 | ESP32 | Pico |
| --- | --- | --- |
| SCK | 18 | 18 |
| MOSI | 23 | 19 |
| MISO | 19 | 16 |
| RST | 4 | 20 |
| SDA (CS) | 5 | 17 |
| 3.3V | 3V3 | 3V3 |
| GND | GND | GND |

## Output
```
Hold a card against the reader
Card: 43:8f:1c:a2
Block 8 contains b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
Card: 9d:04:7b:31
Block 8 contains b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
```

A card is only reported again once it has left the field, so holding one still prints one line
rather than flooding the console.

The key in the script is the factory key that blank cards ship with. A card that has been
written by something else, a hotel key or a transit card, will print an authentication failure
instead; its id still reads fine.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
