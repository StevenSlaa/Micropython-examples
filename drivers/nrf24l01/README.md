---
driver: nrf24l01
author: micropython-lib contributors
---

# nRF24L01+ radio

A two way 2.4GHz radio link between boards. Each end sends packets of up to 32 bytes to an
address, and the receiving module acknowledges them in hardware — so the sender knows whether a
packet arrived, without writing any protocol of your own.

Range is tens of metres indoors with the small PCB-antenna modules, more with the PA+LNA ones
that have a screw-on aerial.

## Install

Install it from the Pulsar IoT library panel, or copy `nrf24l01.py` to `/lib` on the board.

## Before the code: the power supply

**This is why nRF24L01 modules fail.** More than every other cause put together.

The module runs on 3.3V and is quiet almost all the time, but transmitting draws a sudden burst
of current. A supply that cannot deliver it dips, the module browns out, and the symptoms are
maddening: it works on the bench and not on battery, it works for a minute and stops, it
receives but never sends, or a board resets whenever it transmits.

**Solder a capacitor across the module's VCC and GND pins.** 10µF is the usual advice, with a
100nF beside it. This is not optional on a breadboard, and the PA+LNA modules want more —
100µF, and often their own regulator rather than the board's 3.3V pin.

**Never put 5V on VCC.** The module is a 3.3V part and 5V destroys it. Its data pins, however,
are 5V tolerant, so a 5V board can drive them directly.

## Wiring

Eight pins: SPI, plus two of its own.

| Module | Goes to |
| --- | --- |
| VCC | 3.3V, with that capacitor |
| GND | GND |
| CE | any GPIO — puts the radio into transmit or listen |
| CSN | any GPIO — the SPI chip select |
| SCK, MOSI, MISO | the board's SPI pins |
| IRQ | not used by this driver |

## Sending

```python
from machine import Pin, SPI
from nrf24l01 import NRF24L01
import struct

radio = NRF24L01(SPI(2, sck=Pin(18), mosi=Pin(23), miso=Pin(19)),
                 csn=Pin(5), ce=Pin(4), channel=76, payload_size=8)

radio.open_tx_pipe(b"\xe1\xf0\xf0\xf0\xf0")   # where to send
radio.open_rx_pipe(1, b"\xd2\xf0\xf0\xf0\xf0")  # where replies would come back
radio.stop_listening()

try:
    radio.send(struct.pack("<i", 42))
    print("acknowledged")
except OSError:
    print("nobody answered")
```

`send()` raising is a feature, not a nuisance: the receiving module acknowledges in hardware, so
an exception means the packet genuinely did not arrive. Retries have already happened — the
driver asks the chip for eight of them before giving up.

## Receiving

```python
radio.open_rx_pipe(1, b"\xe1\xf0\xf0\xf0\xf0")   # the address the sender sends to
radio.start_listening()

while True:
    if radio.any():
        packet = radio.recv()
        print(struct.unpack("<i", packet[:4])[0])
```

## Both ends have to agree

A link that does nothing at all, with no errors, is almost always a setting that differs between
the two boards. All four of these must match:

| | What happens if they differ |
| --- | --- |
| `channel` | Nothing is heard at all |
| `payload_size` | Packets arrive as rubbish, or not at all |
| Addresses | The sender's `open_tx_pipe` must equal the receiver's `open_rx_pipe` |
| Data rate and CRC | Nothing is heard |

Addresses are five bytes and arbitrary — they are names, not routes. Avoid `00` and `ff` runs,
which the datasheet warns can be confused with the preamble.

## Choosing a channel

Channels are 0 to 125, each 1MHz, from 2.400GHz. WiFi occupies the bottom of that range and is
usually the loudest thing in the room, so **76 and above is quieter** — channel 76 is a common
choice, and the driver's default of 46 sits right under a busy WiFi channel 6.

If a link is unreliable, changing channel is the first thing to try, and the effect is usually
obvious rather than marginal.

## Speed and power

```python
from nrf24l01 import POWER_3, SPEED_250K
radio.set_power_speed(POWER_3, SPEED_250K)
```

The driver already picks `POWER_3` (maximum) and `SPEED_250K`, which is the best combination for
range: the slower the data rate, the further it reaches for the same power. `SPEED_1M` and
`SPEED_2M` are there for when throughput matters more than distance, and both ends must agree.

## Notes

- Payloads are a fixed size, set when the radio is created, and short data is padded. `recv()`
  therefore always gives you `payload_size` bytes; slice off what you need.
- 32 bytes is the maximum. Anything longer has to be split into several packets by you.
- A module cannot listen and send at the same time. `stop_listening()` before sending and
  `start_listening()` after, which is what the examples do.
- Two modules sitting a few centimetres apart can be *too* close for the PA+LNA versions, which
  overload their own receivers. Move them apart before concluding something is broken.
- The IRQ pin is not used here; the driver polls. That is simpler and fine at these rates.
- `send()` blocks for up to `timeout` milliseconds, 500 by default.

## Credits

From [micropython-lib](https://github.com/micropython/micropython-lib/tree/master/micropython/drivers/radio/nrf24l01),
MIT, vendored unchanged.

Used by: [nrf24-send](../../examples/nrf24-send) and [nrf24-receive](../../examples/nrf24-receive)
