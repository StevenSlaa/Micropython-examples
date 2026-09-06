# IR Remote (NEC) Example

In this example the microcontroller decodes button presses from an infrared remote control using
a three pin 38kHz receiver module, prints which button was pressed, and toggles the onboard LED
from one of them.

The receiver runs from an interrupt, so the rest of the program is free to do whatever it likes
while it waits.

## Requires
This example needs the [IR receiver (NEC remotes)](../../drivers/ir-receiver) driver installed on
the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

The receiver's three legs are not in the order you would guess, and the order differs between
makers. Check your module's markings rather than copying a photo: VCC and GND the wrong way
round is why a receiver stays silent or gets warm.

| Module | ESP32 | Pico |
| --- | --- | --- |
| OUT | 15 | 15 |
| GND | GND | GND |
| VCC | 3V3 | 3V3 |

Works with a CHQ1838, VS1838B, TSOP1838, HX1838 or any of the other three pin 38kHz receivers,
and with almost any cheap remote, which send the NEC protocol.

## Finding your buttons

There is no standard list of button codes: every remote picks its own. Run the example, press
each button, and note what the console prints:

```
Point a remote at the receiver and press a button
Button unknown (0x44) from address 0x00
Button unknown (0x43) from address 0x00
Button power (0x45) from address 0x00
Button power (0x45) from address 0x00 held
```

Then fill in the `BUTTONS` table at the top of the script. The address is the same for every
button on one remote, so it is a way to ignore a second remote in the room.

## Output

The name of each button pressed, and `held` while a button stays down, which the remote sends
about nine times a second. The onboard LED toggles on the button mapped to `power`, once per
press rather than continuously while held.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
