# Run with: python3 -B drivers/p9813/test_p9813.py
# Fake pins that record every edge, so the frame going down the wire can be decoded back into
# bytes and checked against what the chip expects.
from p9813 import P9813, checksum


class _DataPin:
    OUT = 3

    def __init__(self):
        self.level = 0

    def init(self, mode, value=0):
        self.level = value

    def __call__(self, level):
        self.level = level


class _ClockPin:
    """Samples the data line on every rising edge, the way the chip does."""

    OUT = 3

    def __init__(self, data):
        self.data = data
        self.level = 0
        self.bits = []

    def init(self, mode, value=0):
        self.level = value

    def __call__(self, level):
        if level == 1 and self.level == 0:
            self.bits.append(self.data.level)
        self.level = level


def wire(n=1, **kwargs):
    data = _DataPin()
    clock = _ClockPin(data)
    leds = P9813(clock, data, n, **kwargs)
    clock.bits.clear()  # drop the blanking frame the constructor sends
    return leds, clock


def decode(bits):
    assert len(bits) % 8 == 0, "a whole number of bytes"
    return [int("".join(str(bit) for bit in bits[i : i + 8]), 2) for i in range(0, len(bits), 8)]


# The checksum byte carries the inverted top two bits of blue, green and red, after two ones.
assert checksum(0x00, 0x00, 0x00) == 0b11111111, bin(checksum(0, 0, 0))
assert checksum(0xFF, 0xFF, 0xFF) == 0b11000000, bin(checksum(255, 255, 255))
assert checksum(0xFF, 0x00, 0x00) == 0b11111100, bin(checksum(255, 0, 0))
assert checksum(0x00, 0x00, 0xFF) == 0b11001111, bin(checksum(0, 0, 255))

# One LED: a start frame, the checksum, blue, green, red, then an end frame.
leds, clock = wire()
leds[0] = (255, 128, 64)
leds.write()
frame = decode(clock.bits)
assert frame[:4] == [0, 0, 0, 0], "32 zero bits open the frame"
assert frame[-4:] == [0, 0, 0, 0], "and close it"
assert frame[4:8] == [checksum(255, 128, 64), 64, 128, 255], frame[4:8]

# Reading a colour back gives it in the order it was set, not the order on the wire.
assert leds[0] == (255, 128, 64)

# Two LEDs are two blocks inside the one frame.
leds, clock = wire(n=2)
leds[0] = (10, 20, 30)
leds[1] = (40, 50, 60)
leds.write()
frame = decode(clock.bits)
assert len(frame) == 4 + 2 * 4 + 4, len(frame)
assert frame[4:12] == [checksum(10, 20, 30), 30, 20, 10, checksum(40, 50, 60), 60, 50, 40]

# fill() sets every LED, and brightness scales what goes out without touching what was set.
leds, clock = wire(n=2)
leds.fill((200, 100, 50))
leds.brightness = 0.5
leds.write()
frame = decode(clock.bits)
assert frame[5:8] == [25, 50, 100], frame[5:8]
assert leds[0] == (200, 100, 50), "the stored colour is unchanged"
leds.brightness = 0
leds.write()
assert decode(clock.bits)[-8:-4] == [checksum(0, 0, 0), 0, 0, 0], "zero brightness is dark"

print("p9813: ok")
