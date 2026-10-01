---
driver: meshtastic
author: Steven Slaa
---

# Meshtastic (text chat)

Lets a board with an SX127x LoRa radio chat with [Meshtastic](https://meshtastic.org) devices:
the off-grid LoRa messengers people carry hiking, at festivals and in emergencies. Messages sent
from here show up in the Meshtastic app on any phone paired to a node in range, and theirs come
back here.

It speaks the real protocol: the same radio settings and frequency, the same packet header, the
same encryption with the default channel key, and the node info that makes apps list this board by
name. It is only the chat part of Meshtastic, not the whole firmware.

## Install

Install it from the Pulsar IoT library panel, or copy `meshtastic.py` to `/lib` on the board. It
drives the radio through the [sx127x](../sx127x) driver, so install that too.

The firmware needs `cryptolib`, which ESP32 builds have. On a Pico, use the Pico W firmware.

## Usage

```python
from machine import Pin, SPI, unique_id
from sx127x import SX127x
from meshtastic import Meshtastic

radio = SX127x(SPI(1, baudrate=5_000_000, sck=Pin(5), mosi=Pin(27), miso=Pin(19)),
               cs=Pin(18), reset=Pin(23), tx_power=20)
node_id = int.from_bytes(unique_id()[-4:], "big")
mesh = Meshtastic(radio, node_id, "Base camp", "BASE", region="EU_868")

mesh.send_node_info()           # so apps show "Base camp" rather than a number
mesh.send_text("Hello mesh!")

while True:
    message = mesh.recv()       # (sender ID, text), or None
    if message:
        sender, text = message
        print(mesh.name(sender), ":", text)
```

## Matching the other devices

A Meshtastic device fresh out of the box uses the **LongFast** preset on its default channel, and
so does this driver. Only the region needs setting:

| `region` | Meshtastic region | LongFast frequency |
| --- | --- | --- |
| `EU_868` | EU_868 | 869.525 MHz |
| `US` | US | 906.875 MHz |
| `ANZ` | ANZ | 919.875 MHz |
| `EU_433` | EU_433 | 433.875 MHz (SX1278 boards) |

For another preset, pass `preset="MediumFast"` or one of the others in `PRESETS`. For a private
channel, pass its name as `channel` and its key as `key`: the 16 bytes behind the base64 key the
app shows. Everyone on the channel needs the same three.

## What it leaves out

- **Relaying.** This node talks and listens but does not repeat other nodes' packets; the
  Meshtastic devices around it still do.
- **Direct messages.** Since Meshtastic 2.5 they use public-key encryption, which this does not
  do. Channel messages, which is what the app's main chat is, work.
- Positions, telemetry, acknowledgements and the rest of the Meshtastic apps.

## Notes

- Messages are up to 200 bytes of text, which is UTF-8: emoji count as four.
- Sending blocks for as long as the radio is on air: roughly half a second on LongFast.
- Other nodes repeat everything, so the same packet arrives several times. `recv()` drops the
  repeats, and this node's own packets coming back.
- `mesh.names` fills in as other nodes announce themselves, which the Meshtastic firmware does
  every few hours and when it starts. Until then `name()` gives the `!1234abcd` form the app uses.

## Tests

`python3 -B drivers/meshtastic/test_meshtastic.py` checks the frequencies, encryption and packets
off-board. It needs `openssl` on the path.

## Credits

The protocol follows the [Meshtastic documentation](https://meshtastic.org/docs/overview/mesh-algo/)
and firmware (GPL-3.0). This is a separate implementation; no firmware code is copied.
