---
example: lora-send
author: Steven Slaa
---

# LoRa Radio: Sending

In this example the microcontroller sends a counter over a long range LoRa link, and reports how
long each packet took to transmit.

**You need two boards for this.** This one sends; the other runs
[LoRa Radio: Receiving](../lora-receive).

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
Sending on 868.0 MHz
Sent: 1  Airtime: 125 ms
Sent: 2  Airtime: 124 ms
Sent: 3  Airtime: 125 ms
```

There is no "delivered" here, unlike the nRF24 example: LoRa has no acknowledgement, so the
sender never knows whether anyone heard it. The receiver counts the gaps instead.

The airtime is why LoRa reaches so far and carries so little. Raise `spreading_factor` to 12 on
both boards and watch it grow to over 800ms for the same four bytes.

## Why it waits so long between packets

In Europe the 868MHz band allows each device on air **1% of the time**, so the script waits 99
times the airtime between packets — about 12 seconds at spreading factor 9. Elsewhere the rules
differ; lower the wait at the bottom of the script if yours allow it.

## Plotter

Open the **Plotter** tab to graph the airtime. It stays flat unless you change the settings,
which makes it a clear picture of what spreading factor costs.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
