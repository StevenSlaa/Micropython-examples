from machine import Pin
from time import sleep
from sr74hc595 import ShiftRegister

# Configuration
# pins
data_pin = 13  # DS / SER
clock_pin = 14  # SHCP / SRCLK
latch_pin = 12  # STCP / RCLK
# True for a common anode display, where a segment lights when its pin is pulled low
common_anode = False
# how long each digit stays on screen
delay = 0.6

# Which shift register output drives which segment: Q0 to Q7 in order. If your display is
# wired differently, reorder this rather than the table below.
SEGMENT_ORDER = ("a", "b", "c", "d", "e", "f", "g", "dp")

#  aaa     Segments of a 7-segment digit. Each entry lists the segments that
# f   b    are lit for that character, and the table below turns those into
# f   b    the bits the shift register needs.
#  ggg
# e   c
# e   c
#  ddd  dp
DIGITS = {
    "0": "abcdef",
    "1": "bc",
    "2": "abdeg",
    "3": "abcdg",
    "4": "bcfg",
    "5": "acdfg",
    "6": "acdefg",
    "7": "abc",
    "8": "abcdefg",
    "9": "abcdfg",
    "a": "abcefg",
    "b": "cdefg",
    "c": "adef",
    "d": "bcdeg",
    "e": "adefg",
    "f": "aefg",
    "-": "g",
    " ": "",
}


def segments(character, point=False):
    """The byte that lights `character` on the display."""
    lit = set(DIGITS[character])
    if point:
        lit.add("dp")
    value = 0
    for bit, segment in enumerate(SEGMENT_ORDER):
        if segment in lit:
            value |= 1 << bit
    # A common anode display shares its positive pin, so a segment lights when its own pin is
    # pulled low: every bit is the other way round.
    return value ^ 0xFF if common_anode else value


display = ShiftRegister(Pin(data_pin), Pin(clock_pin), Pin(latch_pin))

while True:
    # Count 0 to 9, then run through the hex letters, with the decimal point on for the letters.
    for character in "0123456789":
        print("Showing", character)
        display.write(segments(character))
        sleep(delay)
    for character in "abcdef":
        print("Showing", character, "with the point")
        display.write(segments(character, point=True))
        sleep(delay)
    display.write(segments(" "))
    sleep(delay)
