# Matrix Keypad (4x4) Example

In this example the microcontroller reads a membrane matrix keypad and collects the digits typed
into a code, checking it when `#` is pressed and clearing it on `*`.

## Requires
This example needs the [Matrix keypad](../../drivers/keypad) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

Eight GPIO pins for a 4x4 keypad, seven for a 4x3. No resistors are needed: the driver turns on
the board's own pull-ups for the column pins.

| Keypad | ESP32 | Pico |
| --- | --- | --- |
| Row 1 | 13 | 2 |
| Row 2 | 12 | 3 |
| Row 3 | 14 | 4 |
| Row 4 | 27 | 5 |
| Column 1 | 26 | 6 |
| Column 2 | 25 | 7 |
| Column 3 | 33 | 8 |
| Column 4 | 32 | 9 |

Looking at the ribbon from the front, the pins are usually the four rows then the four columns,
left to right. Nothing about that is standard, so see below if the keys come out wrong.

For a 4x3 keypad, leave out the fourth column and pass three column pins; the driver picks the
right labels from how many there are.

## Output
```
Type a code and press # to check it, or * to clear
Entered *
Entered **
Entered ***
Entered ****
Unlocked
```

Digits are shown as stars, since the point of a keypad is usually a code.

## If the keys come out wrong

Every key reporting as a different one, in a tidy pattern, means the row and column lists are
the other way round: swap `row_pins` and `column_pins`.

Keys reporting as shuffled means the ribbon is not in the order assumed here. Reorder the pin
numbers in the two lists to match your keypad rather than editing the driver.

Nothing at all from one row or column is usually a wiring break; the keys on the rest of the pad
will still work, which makes it easy to spot.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
