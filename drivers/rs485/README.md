---
driver: rs485
author: Steven Slaa
---

# RS-485 (MAX485)

Serial that survives a long wire. RS-485 sends each bit as the *difference* between two wires
rather than against ground, so noise that lands on both affects neither — which is why it runs a
kilometre through a factory where a plain UART would not manage ten metres of it.

Works with the MAX485, MAX3485, SP3485, SN75176 and the blue breakout boards built around them.

**RS-485 is not a protocol.** It carries whatever bytes you send: your own text commands, or
Modbus, or anything else. This driver handles the wire; what you say over it is yours.

## Install

Install it from the Pulsar IoT library panel, or copy `rs485.py` to `/lib` on the board.

## Usage

```python
from machine import Pin, UART
from rs485 import RS485

uart = UART(1, baudrate=9600, tx=Pin(17), rx=Pin(16))
bus = RS485(uart, de=Pin(4), baudrate=9600)

bus.write(b"hello\n")

if bus.any():
    print(bus.read())

reply = bus.query(b"temperature?\n", terminator=b"\n")   # send, then wait for an answer
```

The `baudrate` is passed twice on purpose: once to the UART, which uses it to send, and once
here, because how long a byte takes to leave is what decides when it is safe to stop
transmitting.

## The one thing that goes wrong

RS-485 is half duplex. One pair of wires, so only one device may speak at a time, and each has
to announce which it is doing — that is the DE and RE pins, wired together to a single GPIO:
high to talk, low to listen.

`uart.write()` returns as soon as the bytes are handed to the hardware, **not when they have
left the wire**. Dropping the direction line there cuts the end off every message, and the
symptom is maddening: short messages work, long ones arrive truncated, and it all changes when
you alter the baud rate.

This driver waits. It asks the UART whether it has finished if the port can answer, and
otherwise works out from the baud rate how long the bytes take, then adds a margin. Being a
little late costs nothing; being early loses data.

It also returns the line to listening in a `finally`, so a failed write cannot leave the
transceiver talking — which would hold the whole bus down and silence every other device on it.

## Wiring

| Module | Goes to |
| --- | --- |
| DI | the board's UART TX |
| RO | the board's UART RX |
| DE and RE | tied together, to one GPIO |
| VCC | 5V, or 3.3V for a MAX3485 |
| A, B | the pair, to every other device's A and B |

The two data wires should be a twisted pair — a single pair out of an ethernet cable is ideal
and free. Ground the modules to each other as well: RS-485 tolerates a difference between
grounds, but not an unlimited one.

**Termination:** a 120Ω resistor across A and B at each *end* of the run, and nowhere in the
middle. Many breakout boards have one fitted, which is right for two devices and wrong the
moment you add a third in the middle — that is when you start unsoldering them. Short runs on a
bench work without any of it, which is why the problem appears later rather than immediately.

## If nothing arrives

| What you see | What it usually means |
| --- | --- |
| Nothing at all, ever | A and B swapped. Manufacturers do not agree on which is which; swap them |
| The end of every message is missing | The direction line is dropping early — this driver is the fix, but check `baudrate` matches the UART |
| Rubbish characters | The two ends disagree on baud rate |
| Works on the bench, not on the long cable | Termination, or a ground that is not shared |
| Both devices talk and neither hears | Two transceivers transmitting at once; only one may talk at a time |

## Notes

- Nothing arbitrates the bus for you. If two devices transmit together both messages are
  destroyed, which is why nearly every real RS-485 system has one master that asks and several
  devices that only answer. `query()` is that pattern.
- A device cannot hear itself, and with DE and RE tied together it will not receive an echo of
  what it sent.
- `bits_per_byte` is 10 for the usual 8N1. Add parity or a second stop bit and it becomes 11,
  which matters only for the timing sums.
- 9600 is a sensible starting point. RS-485 will do far more, but slower is more forgiving of a
  long, badly terminated cable.

## Tests

`python3 -B drivers/rs485/test_rs485.py` records the direction pin, the write and the waiting as
one timeline and checks the order of them, which is the whole of what this driver has to get
right. It also covers the timing sums, both ways of knowing a send has finished, a failed write
releasing the bus, and `query()`.

Used by: [rs485-link](../../examples/rs485-link)
