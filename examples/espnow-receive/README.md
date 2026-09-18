---
example: espnow-receive
author: Steven Slaa
---

# ESP-NOW: Receiving

In this example the ESP32 prints its own address, then listens for ESP-NOW messages from another
ESP32, prints the counter in each one and reports any that went missing.

ESP-NOW is Espressif's own protocol on the wifi radio: boards talk to each other directly, without
a router or a network. It is built into MicroPython (v1.20 and later) as the `espnow` module, so no
driver is needed.

**You need two ESP32 boards for this.** This one receives; the other runs
[ESP-NOW: Sending](../espnow-send).

## Requires
Nothing to install: `espnow` is part of the MicroPython firmware for the ESP32.

## Connections
None. Everything goes over the built-in wifi radio.

## Output
```
My address: 24:0a:c4:12:34:56
Sender setting: receiver = b"\x24\x0a\xc4\x12\x34\x56"
Listening on channel 1
From: 30:ae:a4:ab:cd:ef  Counter: 1  Missed: 0
From: 30:ae:a4:ab:cd:ef  Counter: 2  Missed: 0
From: 30:ae:a4:ab:cd:ef  Counter: 4  Missed: 1
```

Copy the `Sender setting` line into the sending script. The counter goes up by one each message,
so a gap is a message that never arrived. When the sender restarts, its counter starts again at 1
and is not counted as missed.

## Nothing arrives

- Is `channel` the same on both boards?
- Is the sender running, and its `receiver` either this board's address or the broadcast address?
- A board connected to a wifi router uses the router's channel; keep both boards off wifi for this
  example.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
