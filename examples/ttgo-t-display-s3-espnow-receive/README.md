---
example: ttgo-t-display-s3-espnow-receive
author: Steven Slaa
---

# ESP-NOW: Receiving on the T-Display S3

In this example the LilyGO/TTGO T-Display-S3 listens for ESP-NOW messages from another ESP32 and
shows the link live on its built-in 1.9 inch LCD: how many messages arrived, what share of them made
it, the signal strength, and a chart of the signal that scrolls by and marks every lost message in
red.

ESP-NOW is Espressif's own protocol on the wifi radio: boards talk to each other directly, without
a router or a network. It is built into MicroPython (v1.20 and later) as the `espnow` module.

**You need two ESP32 boards for this.** This one receives; the other runs
[ESP-NOW: Sending](../espnow-send), unchanged.

## Requires

- [ST7789 8-bit parallel display](../../drivers/st7789-parallel), which talks to the display
- [RGB565 display drawing (shared)](../../drivers/rgb565-display), with the drawing methods

> Install them from the library panel in the Pulsar IoT IDE, or copy `st7789_parallel.py` and
> `rgb565_display.py` into `/lib` on the microcontroller yourself. `pulsar_ui.py`, with the logo and
> the large digits, goes on the board next to the script; the IDE copies it for you.

## Connections

None. The LCD is built into the board, and the messages go over the built-in wifi radio. The
display pins are the same as in the [T-Display S3 example](../ttgo-t-display-s3).

## Setting it up

1. Run this script on the T-Display-S3. Until a message arrives, the footer shows this board's own
   address, and the REPL prints a line like `Sender setting: receiver = b"\x24\x0a\xc4\x12\x34\x56"`.
2. Paste that line over `receiver = ...` in the [sending script](../espnow-send) and run it on the
   other board. Leaving the sender on the broadcast address works too.

## What is on the screen

| Part | What it shows |
| --- | --- |
| Status, top right | amber **WAITING** before the first message, green **LINKED** with a light that flashes on every message, red **NO LINK** once nothing arrived for `link_timeout_ms` |
| RECEIVED | every message that arrived, with the number of missed ones underneath |
| DELIVERY | the share of the sender's counters that arrived; green from 95%, yellow from 80%, red below |
| SIGNAL | the strength of the last message in dBm; green above -67, yellow above -80, red below |
| Chart | the signal over the last 15 seconds; a gap when the link is down, a red line where messages went missing |
| Footer | the sender's address and how long ago its last message came |

The sender's counter goes up by one each message, so a gap in it is a message that never arrived.
When the sender restarts, its counter starts again at 1, which is not counted as missed. Messages
that are not a number still count as received, they are just not checked for gaps.

## Output

The REPL prints one line per message:
```
My address: 24:0a:c4:12:34:56
Sender setting: receiver = b"\x24\x0a\xc4\x12\x34\x56"
RSSI: -48 dBm  Missed: 0
RSSI: -51 dBm  Missed: 0
RSSI: -63 dBm  Missed: 1
```

## Plotter

Two series: the signal in dBm, and the running count of missed messages. Walk away from the
sender with the board and watch the signal drop, and the missed count start to climb.

## Nothing arrives

| Check | Why |
| --- | --- |
| `channel` | must be the same on both boards |
| The sender's `receiver` | must be this board's address, or the broadcast address |
| Wifi connection | a board connected to a router uses the router's channel, not `channel` |
| Screen stays black | GPIO 15 must go high before the display is set up; see the [T-Display S3 example](../ttgo-t-display-s3) |

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
