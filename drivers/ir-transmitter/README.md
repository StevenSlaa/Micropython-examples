# IR transmitter (NEC remotes)

Sends NEC remote codes from an infrared LED — the other half of the
[IR receiver](../ir-receiver) driver, and it speaks the same protocol, so one board can drive a
television, or another board running the receiver.

## Install

Install it from the Pulsar IoT library panel, or copy `ir_transmitter.py` to `/lib` on the board.

## Usage

```python
from machine import Pin
from ir_transmitter import IRTransmitter

transmitter = IRTransmitter(Pin(4))

transmitter.send(0x00, 0x45)              # address and command, as a receiver reports them
transmitter.send(0x00, 0x45, repeats=3)   # as if the button were held
print(transmitter.backend)                # which mechanism it picked
```

For a protocol this driver does not know, hand it the pulse lengths directly:

```python
transmitter.send_raw([9000, 4500, 560, 1690, 560])   # marks and spaces in microseconds
```

## How it sends, and why that varies

Receiving is just measuring pulses, so it works the same everywhere. Sending means gating a
38kHz carrier with pulses a few hundred microseconds long, and how well a board does that
depends on the hardware it has. The driver tries the best mechanism available and falls back,
rather than being told which board it is on:

| `backend` | Where | Quality |
| --- | --- | --- |
| `rmt` | ESP32 and ESP32-S3 | Exact. The carrier and the pulse train come out of a peripheral built for this, and nothing else running on the board disturbs them. |
| `pwm` | Everywhere else, including the Pico | Good enough. A PWM channel switched on and off by `sleep_us`, accurate to tens of microseconds. Receivers tolerate that, but an interrupt landing mid-frame can spoil one. |

If a Pico misses the occasional frame, send with `repeats=2`: a receiver acts on the first frame
it understands and treats the rest as a held button.

## Wiring

An IR LED, not the receiver module — they look nothing alike, the LED being clear or pale blue
with two legs.

```
GPIO ---[ 1k ]--- base of an NPN transistor (BC547, 2N2222)
                     collector --- IR LED cathode
                     IR LED anode --- [ 100R ] --- 5V or 3V3
                     emitter --- GND
```

A GPIO pin can drive the LED directly through a resistor, and it will work across a desk. The
transistor is what gets you across a room, because the LED can then be given the 100mA or so it
wants in pulses. Do not connect an IR LED to a pin without a resistor.

## Notes

- The LED is invisible to you and obvious to a phone camera. Point one at it: a working
  transmitter blinks white or purple on the screen. This is the quickest way to tell a wiring
  problem from a code problem.
- `duty=33` is the carrier duty cycle in percent, which is the usual compromise between range
  and current. `frequency=38000` suits nearly every remote; a few use 36kHz or 40kHz.
- `encode(address, command)` is exported and pure, giving the pulse list without sending it.
  It is what the tests decode with the receiver driver to check the two agree.
- Addresses above `0xff` are sent as a 16 bit extended address, matching what the receiver
  driver reports for remotes that use them.
- Sending blocks for the length of the frame, about 68ms, plus 40ms for each repeat.

## Tests

`python3 -B drivers/ir-transmitter/test_ir_transmitter.py` decodes the frames this driver builds
using the receiver driver, so the two ends are checked against each other, and confirms the
backend choice, off-board.

Used by: [ir-remote-send](../../examples/ir-remote-send)
