---
example: ttgo-t-display-espnow-send
author: Steven Slaa
---

# ESP-NOW: Sending from the T-Display v1.1

In this example the LilyGO/TTGO T-Display v1.1 sends a counter to another ESP32 over ESP-NOW, and
shows on its built-in 1.14 inch LCD how many messages it sent, what share of them the other board
acknowledged, and a strip of the last 38 messages: green when acknowledged, red when not.

ESP-NOW is Espressif's own protocol on the wifi radio: boards talk to each other directly, without
a router or a network. It is built into MicroPython (v1.20 and later) as the `espnow` module.

**You need two ESP32 boards for this.** This one sends; the other runs
[ESP-NOW: Receiving on the T-Display S3](../ttgo-t-display-s3-espnow-receive), or the plain
[ESP-NOW: Receiving](../espnow-receive) on any ESP32. The messages are the same as those of
[ESP-NOW: Sending](../espnow-send), so any of the receivers works with any of the senders.

## Requires

- [ST7789 display driver](../../drivers/st7789py), which talks to the display

> Install it from the library panel in the Pulsar IoT IDE, or copy `st7789py.py` into `/lib` on the
> microcontroller yourself. `pulsar_ui.py`, with the logo and the large digits, goes on the board
> next to the script; the IDE copies it for you.

## Connections

None. The LCD and the buttons are built into the board, and the messages go over the built-in wifi
radio. The pins are the same as in the [T-Display v1.1 example](../ttgo-t-display).

## Setting it up

1. Start the receiver on the other board. It shows its address at the bottom of the screen and
   prints a line like `Sender setting: receiver = b"\x24\x0a\xc4\x12\x34\x56"`.
2. Paste that line over `receiver = ...` at the top of this script and run it.

Leaving `receiver` on the broadcast address `b"\xff\xff\xff\xff\xff\xff"` also works: every
ESP-NOW board in range gets the messages. A broadcast is never acknowledged though, so the screen
then shows **BCAST**, blue squares, and no delivery rate.

## The buttons

| Button | What it does |
| --- | --- |
| Left (GPIO 0) | pause or resume sending |
| Right (GPIO 35) | step the rate through one message every 1000, 500 and 250 ms |

## What is on the screen

| Part | What it shows |
| --- | --- |
| Status, top right | green **SENDING**, red **NO ACK** when the last message was not acknowledged, amber **PAUSED**, blue **BCAST**; the light flashes on every message |
| SENT | messages sent since the start |
| DELIVERY | the share of them the receiver acknowledged |
| Strip | the last 38 messages, newest on the right |
| Footer | the receiver's address, the number lost, the channel and the rate |

`send()` only counts a message as delivered when the other board's radio acknowledged it, after
the radio has already retried a few times itself. A lost message here is one the receiver really
did not get, so the receiver's missed count should match.

## Output
```
Sending on channel 1 to 24:0a:c4:12:34:56
Sent: 1  Delivered: 1  Lost: 0
Sent: 2  Delivered: 2  Lost: 0
Sent: 3  Delivered: 2  Lost: 1
```

## Plotter

Three lines: sent and delivered climb together, and lost stays flat at the bottom. They split
apart as soon as messages go missing, when you carry the board out of range or unplug the receiver.

## Troubleshooting

| What you see | Likely cause |
| --- | --- |
| **NO ACK** all the time | the receiver is not running, `receiver` is not its address, or `channel` differs |
| Everything acknowledged but the receiver shows nothing | it is on another channel because it is connected to a wifi router |
| `MemoryError` | reset the board, or run the script on its own; another colour for text needs its own 4 KB table, add it to the list made before wifi starts |
| The picture is upside down | set `rotation = 3` instead of 1 |

## Tested
- LilyGO T-Display v1.1 running MicroPython 1.29.0, broadcasting once a second without a
  problem. With wifi on, this board has about 140 KB of memory for the program, so the colour
  tables and pixel buffers are all made before wifi starts, while the memory is still in one piece.
