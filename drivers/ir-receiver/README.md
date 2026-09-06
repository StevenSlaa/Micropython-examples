# IR receiver (NEC remotes)

Decodes infrared remote controls with one of the little three pin 38kHz receivers — CHQ1838,
VS1838B, TSOP1838, HX1838 and the rest of the family are all the same part for this purpose,
and are what comes in the kit with the small black credit-card remote.

The module does the hard half: it strips the 38kHz carrier and gives a plain logic output, idle
high and pulled low while a remote is transmitting. This driver measures those pulses and turns
them into a button.

Only the NEC protocol is decoded, which is what nearly every cheap remote sends. A Sony or an
RC5 remote will not be understood.

To send codes rather than receive them, see the [IR transmitter](../ir-transmitter) driver.

## Install

Install it from the Pulsar IoT library panel, or copy `ir_receiver.py` to `/lib` on the board.

## Usage

```python
from machine import Pin
from ir_receiver import IRReceiver

def pressed(address, command, repeat):
    print("button", hex(command), "held" if repeat else "pressed")

IRReceiver(Pin(15), pressed)

while True:
    pass          # the receiver works from an interrupt; the program is free to do anything
```

Buttons are identified by `command`; `address` says which device the remote is talking to, and
is the same for every button on one remote. There is no standard list — press each button and
write down what it prints.

Holding a button down sends a shorter "same again" frame, which arrives as `repeat=True` with
the previous button's code, roughly nine times a second.

## Wiring

Three pins, and the order is not the one you would guess. Looking at the **front**, the domed
side facing you, they are usually OUT, GND, VCC from the left — but this varies between makers
and getting it wrong is the usual reason a receiver does nothing or gets warm. Check the
markings on your module.

| Module | Goes to |
| --- | --- |
| OUT | any GPIO |
| GND | GND |
| VCC | 3.3V |

Most of these modules run happily on 3.3V; some are specified for 5V and are simply less
sensitive at 3.3V.

## Notes

- The output is active low and idles high, so a pin reading 0 all the time means either
  constant infrared or a swapped VCC and GND.
- Sunlight, fluorescent lamps and some LED bulbs put noise on the receiver. That is not a
  problem here: noise does not look like a NEC frame, so `decode` returns nothing for it.
- The callback runs from a timer rather than the interrupt itself, so printing in it is fine.
  It should still return quickly, because anything arriving while it runs is missed.
- Reach is a few metres, and drops sharply if the remote is not pointed at the receiver or its
  battery is old.
- `decode(durations)` is exported and pure: hand it a list of pulse lengths in microseconds and
  it gives back `(address, command)`, `REPEAT`, or `None`. Useful for testing without a remote.
- Adding `micropython.alloc_emergency_exception_buf(100)` at the top of your program makes any
  error inside the interrupt handler readable instead of silent.

## Tests

`python3 -B drivers/ir-receiver/test_ir_receiver.py` builds NEC frames as pulse lengths and
decodes them back, including a corrupted one and one 15% out of spec, off-board.

Used by: [ir-remote-nec](../../examples/ir-remote-nec)
