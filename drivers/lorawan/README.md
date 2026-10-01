---
driver: lorawan
author: Steven Slaa
---

# LoRaWAN (The Things Network)

Connects a board with an SX127x LoRa radio to a LoRaWAN network such as
[The Things Network](https://www.thethingsnetwork.org), so its data reaches the internet through
any gateway in range, without wifi of its own.

It is a deliberately small LoRaWAN 1.0 stack: a class A device that joins over the air (OTAA),
sends uplinks, and receives the downlinks that come back just after them.

## Install

Install it from the Pulsar IoT library panel, or copy `lorawan.py` to `/lib` on the board. It
drives the radio through the [sx127x](../sx127x) driver, so install that too.

The firmware needs `cryptolib`, which ESP32 builds have. On a Pico, use the Pico W firmware.

## Usage

```python
from machine import Pin, SPI
from sx127x import SX127x
from lorawan import LoRaWAN

spi = SPI(1, baudrate=5_000_000, sck=Pin(5), mosi=Pin(27), miso=Pin(19))
radio = SX127x(spi, cs=Pin(18), reset=Pin(23), tx_power=14)

# The three values from the device's page in the TTN console, as shown there.
ttn = LoRaWAN(radio, dev_eui="70B3D57ED0000000", join_eui="0000000000000000",
              app_key="00112233445566778899AABBCCDDEEFF", region="EU868")

while not ttn.joined:
    ttn.join()

reply = ttn.send(b"\x01\x02", port=1)   # a downlink's payload, or None
```

`send()` returns once both receive windows have passed, which takes about seven seconds on TTN:
the network answers five seconds after an uplink, or six.

## The session is saved

A successful join is saved to `lorawan.json` in flash, with the frame counter, so a reset
carries on where it left off instead of joining again. TTN discourages joining over and over,
and it drops uplinks whose counter it has already seen.

**Delete `lorawan.json`** after deleting and re-registering the device in the console, or when
uplinks stop arriving for no other reason. The next start then joins afresh. Changing the keys in
the script does that by itself.

## Regions

| `region` | TTN frequency plan |
| --- | --- |
| `EU868` | Europe 863-870 MHz (SF9 for RX2 - recommended) |
| `US915` | United States 902-928 MHz, FSB 2 (used by TTN) |
| `AU915` | Australia 915-928 MHz, FSB 2 (used by TTN) |

The radio has to be the one sold for that band: an SX1276 for all three, not a 433MHz SX1278.

## What it leaves out

- Joining by ABP, class B and C, and confirmed uplinks.
- The network's commands that ride along with downlinks, such as adaptive data rate. They are
  ignored, so the data rate is the `spreading_factor` you choose. TTN copes with that; it may
  resend the same command for a while.
- Extra channels a network offers after joining: it uses the three standard EU868 channels, and
  the eight of sub-band 2 in the US and Australia.

## Notes

- Fair use on TTN is 30 seconds of airtime a day per device, and ten downlinks. At spreading
  factor 9 a small uplink takes about 170ms: roughly one every ten minutes.
- `spreading_factor` above 10 is not allowed in the US and Australia plans.
- Downlinks are queued in the console and delivered after the next uplink. Payloads on port 0,
  or with no payload, return None.

## Tests

`python3 -B drivers/lorawan/test_lorawan.py` checks the packets and cryptography off-board
against published examples. It needs `openssl` on the path.
