---
example: ir-remote-send
author: Steven Slaa
---

# IR Remote Send (NEC) Example

In this example the microcontroller sends remote control codes from an infrared LED, the same
codes a cheap remote sends, so it can drive a television or another board.

It is the other half of the [IR Remote (NEC) example](../ir-remote-nec), which receives them.

## Requires
This example needs the [IR transmitter (NEC remotes)](../../drivers/ir-transmitter) driver
installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

An infrared **LED**, not the receiver module: it is clear or pale blue with two legs, and looks
nothing like the black three pin receiver.

Straight from a pin, which works across a desk:

```
GPIO 4 ---[ 220R ]--- IR LED --- GND
```

Through a transistor, which works across a room, because the LED can then be driven with the
100mA or so it wants:

```
GPIO 4 ---[ 1k ]--- base       NPN, such as a BC547 or 2N2222
                    collector --- IR LED cathode
                    IR LED anode --- [ 100R ] --- 5V
                    emitter --- GND
```

Never wire an IR LED to a pin without a resistor.

## Output
```
Sending with the rmt backend
Sent power (0x45) to address 0x00
Sent volume up (0x46) to address 0x00
Sent volume down (0x15) to address 0x00
```

`rmt` means the ESP32 is generating the carrier in hardware and the timing is exact. `pwm` means
the board is doing it in software, which works but can lose the occasional frame; set `repeats`
to 2 there, since a receiver acts on the first frame it understands and treats the rest as a
held button.

## Checking it works

Infrared is invisible to you and obvious to a phone camera. Point a camera at the LED: it blinks
white or purple on screen while sending. That separates a wiring problem from a code problem
before you go looking for either.

To check the codes themselves, run the [IR Remote (NEC) example](../ir-remote-nec) on a second
board and point one at the other. What one sends is what the other prints.

## Finding the codes to send

The codes here are made up. Real ones come from the remote you want to imitate: run the
receiving example, press the button, and note the address and command it prints.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
