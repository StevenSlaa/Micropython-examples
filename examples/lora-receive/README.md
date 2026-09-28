---
example: lora-receive
author: Steven Slaa
---

# LoRa Radio: Receiving

In this example the microcontroller listens for packets over a long range LoRa link, and reports the
signal strength of each one and how many went missing.

**You need two boards for this.** This one receives; the other runs
[LoRa Radio: Sending](../lora-send).

## Requires
This example needs the [SX1276/SX1278 LoRa radio](../../drivers/sx127x) driver
installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

Set the pins at the top of the script to match your board. Boards with the radio built in are
already wired; for a separate RFM95/RFM96 module, wire it as in the last two columns.

| Script setting | LilyGO T3 LoRa32 V1.6.1 | Heltec WiFi LoRa 32 V2 | ESP32 + RFM95 module | Pico + RFM95 module |
| --- | --- | --- | --- | --- |
| `spi_id` | 1 | 1 | 1 | 0 |
| `sck_pin` | 5 | 5 | 18 | 2 |
| `mosi_pin` | 27 | 27 | 23 | 3 |
| `miso_pin` | 19 | 19 | 19 | 4 |
| `cs_pin` | 18 | 18 | 5 | 5 |
| `reset_pin` | 23 | 14 | 4 | 6 |

A separate module runs on **3.3V only**: VCC to 3V3, GND to GND. Its DIO pins can stay
unconnected.

**Never transmit without an antenna**, it can damage the radio. A bare module takes a straight
wire a quarter wavelength long: 8.2cm for 868MHz, 7.8cm for 915MHz, 17.3cm for 433MHz.

Boards with an SX1262 radio, like the Heltec WiFi LoRa 32 V3, need a different driver.

## Output
```
Listening on 868.0 MHz
RSSI: -41  SNR: 9.5  Missed: 0
RSSI: -43  SNR: 9.8  Missed: 0
RSSI: -118  SNR: -12.3  Missed: 2
```

- **RSSI** is the signal strength in dBm: -30 is on the same desk, -120 is the edge of range.
- **SNR** is how far above the background noise it was. Most radios need a positive SNR; LoRa
  still decodes around -20 dB, below the noise, and that is where its range comes from.
- **Missed** counts gaps in the sender's counter, since the sender cannot know.

Run the receiver from a laptop, or with the Plotter open, and carry the sender away from it
to find the real range of your setup.

## Nothing arrives

Frequency, bandwidth and spreading factor must match the sender exactly, and a mismatch gives
silence rather than an error. Past that: are both antennas on, and is the sender running? Two
boards within a few centimetres can also overload each other, so give them a metre.

## Plotter

Open the **Plotter** tab to graph RSSI, SNR and missed packets together. Walking away draws the
signal falling and, near the edge, the missed count starting to climb.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
