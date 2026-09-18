---
example: espnow-send
author: Steven Slaa
---

# ESP-NOW: Sending

In this example the ESP32 sends a counter to another ESP32 once a second over ESP-NOW, and prints
whether each message was acknowledged by the board at the other end.

ESP-NOW is Espressif's own protocol on the wifi radio: boards talk to each other directly, without
a router or a network. It is built into MicroPython (v1.20 and later) as the `espnow` module, so no
driver is needed.

**You need two ESP32 boards for this.** This one sends; the other runs
[ESP-NOW: Receiving](../espnow-receive).

## Requires
Nothing to install: `espnow` is part of the MicroPython firmware for the ESP32.

## Connections
None. Everything goes over the built-in wifi radio.

## Setting it up

1. Start the receiving example on the other board. It prints a line like
   `Sender setting: receiver = b"\x24\x0a\xc4\x12\x34\x56"`.
2. Paste that line over `receiver = ...` at the top of this script and run it.

Leaving `receiver` on the broadcast address `b"\xff\xff\xff\xff\xff\xff"` also works: every
ESP-NOW board in range gets the messages. A broadcast is never acknowledged though, so the
delivered count then only tells you the message left this board.

## Output
```
Sending on channel 1 to 24:0a:c4:12:34:56
Sent: 1  Delivered: 1  Lost: 0
Sent: 2  Delivered: 2  Lost: 0
Sent: 3  Delivered: 2  Lost: 1  (no answer)
```

`send()` returns `True` only when the other board's radio acknowledged the message, after the radio
has already retried a few times itself.

## Nothing is delivered at all

| Check | Why |
| --- | --- |
| `receiver` | must be the address the receiving board printed |
| `channel` | must be the same on both boards |
| The other board | must be running the receiving example |
| Wifi connection | a board connected to a router uses the router's channel, not `channel` |

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
