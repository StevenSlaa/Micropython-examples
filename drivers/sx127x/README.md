---
driver: sx127x
author: Steven Slaa
---

# SX1276/SX1278 LoRa radio

A long range radio link between boards, using the Semtech SX127x chips found on the LilyGO T3
LoRa32, the Heltec WiFi LoRa 32, and the RFM95/96 modules. A kilometre or more line of sight
with the stock antenna, at the price of a very slow data rate.

This is plain LoRa, board to board. It is **not LoRaWAN**: it does not talk to The Things Network
or any other gateway.

## Install

Install it from the Pulsar IoT library panel, or copy `sx127x.py` to `/lib` on the board.

## Wiring

The radio talks SPI, plus a reset pin. Boards with the radio built in have it wired already:

| Radio | LilyGO T3 LoRa32 V1.6.1 | Heltec WiFi LoRa 32 V2 | ESP32 + RFM95 module | Pico + RFM95 module |
| --- | --- | --- | --- | --- |
| SCK | 5 | 5 | 18 | 2 |
| MOSI | 27 | 27 | 23 | 3 |
| MISO | 19 | 19 | 19 | 4 |
| CS (NSS) | 18 | 18 | 5 | 5 |
| RESET | 23 | 14 | 4 | 6 |
| SPI bus | `SPI(1)` | `SPI(1)` | `SPI(1)` | `SPI(0)` |

A bare module runs on **3.3V only**. DIO0 is not used by this driver, so it can stay unconnected.
Boards with an SX1262 radio, such as the Heltec WiFi LoRa 32 V3, are a different chip and need a
different driver.

**Never transmit without an antenna.** The power has nowhere to go and can damage the radio. A
bare module takes a straight wire a quarter wavelength long: 8.2cm for 868MHz, 7.8cm for 915MHz,
17.3cm for 433MHz.

## Sending

```python
from machine import Pin, SPI
from sx127x import SX127x

# The pins of a LilyGO T3 LoRa32; see the table above for others.
spi = SPI(1, baudrate=5_000_000, sck=Pin(5), mosi=Pin(27), miso=Pin(19))
lora = SX127x(spi, cs=Pin(18), reset=Pin(23), frequency=868_000_000)

lora.send(b"hello")
```

`send()` returns once the packet has left the antenna. Nothing confirms that anyone heard it —
LoRa has no acknowledgement of its own. If you need one, have the receiver send a reply.

## Receiving

```python
lora.receive()

while True:
    packet = lora.recv()
    if packet:
        print(packet, lora.rssi, "dBm", lora.snr, "dB")
```

`recv()` returns `None` until a packet is waiting. Packets that arrive corrupted are dropped and
counted in `lora.crc_errors`.

## Both ends have to agree

A link that does nothing at all is almost always a setting that differs between the two boards.
All of these must match:

| Setting | Default | |
| --- | --- | --- |
| `frequency` | 868 000 000 | In Hz. Use the band the board was sold for, see below |
| `bandwidth` | 125 000 | 7 800 to 500 000 Hz. Narrower reaches further |
| `spreading_factor` | 9 | 7 to 12. Each step up roughly doubles the airtime and adds range |
| `coding_rate` | 5 | 5 to 8, meaning 4/5 to 4/8. More is more error correction |
| `sync_word` | 0x12 | A private network. 0x34 is LoRaWAN's; leave it alone |

`tx_power` (2 to 20 dBm, default 17) and `preamble_length` do not have to match.

## Frequency

The chip on the board decides the band, and the antenna is tuned to it:

- **SX1276**, 868MHz: Europe, 915MHz: Americas and Australia.
- **SX1278**, 433MHz: Asia, and also licence-free in Europe at low power.

The model is printed on the shield and usually on the box. Transmitting outside your region's
band is illegal as well as ineffective.

In Europe the 868MHz band allows each device to transmit **1% of the time**. At spreading
factor 9 a short packet takes about 125ms, so one every 12 seconds or so is the limit.

## Changing settings

```python
lora.configure(frequency=869_525_000, spreading_factor=12)
```

Any constructor setting except `tx_power` and `xtal` can change between
packets; the rest stay as they are. `invert_iq=True` is there for LoRaWAN, whose gateways
transmit with it inverted — the [lorawan](../lorawan) driver uses both.

`recv(timeout_ms=500)` waits up to that long for a packet instead of checking once, and does not
give up on one that has started arriving.

## Notes

- Packets are 1 to 255 bytes, of any content.
- The radio cannot listen while it sends. `send()` stops listening and, if `receive()` was on,
  starts it again afterwards.
- `rssi` is the signal strength of the last packet: -30 is right next to it, -120 is the edge.
  `snr` is how far above the noise it was; LoRa still decodes down to about -20 dB, which is its
  whole trick.
- Two boards on a desk can overload each other at 20dBm. Put a metre between them before
  concluding something is broken.
- A crystal that runs off makes two boards drift apart, which shows at narrow bandwidths.
  `xtal=32_000_000` is the knob; trim it on one side if 7.8kHz or 10.4kHz will not link.
- The driver polls rather than using DIO0. At LoRa's data rates that costs nothing.
- `sleep()` drops the radio to about a microamp for battery projects; the next `send()` or
  `receive()` wakes it.

## Tests

`python3 -B drivers/sx127x/test_sx127x.py` checks the register handling off-board.
