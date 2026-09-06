# Run with: python3 -B drivers/ir-receiver/test_ir_receiver.py
# Builds NEC frames as pulse lengths and decodes them back, which is the whole of the protocol
# work. Stubs the firmware modules so the file imports off-board.
import sys, types

sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
sys.modules["machine"] = types.SimpleNamespace(Pin=object, Timer=object)
sys.modules["time"] = types.SimpleNamespace(ticks_us=lambda: 0, ticks_diff=lambda a, b: a - b)
from ir_receiver import REPEAT, decode  # noqa: E402


def frame(address, command, extended=False):
    """The pulse lengths a remote sends for one button press."""
    if extended:
        value = address & 0xFFFF
    else:
        value = (address & 0xFF) | ((address ^ 0xFF) << 8)
    value |= (command & 0xFF) << 16 | ((command ^ 0xFF) << 24)
    durations = [9000, 4500]
    for bit in range(32):
        durations.append(560)  # every bit starts with the same mark
        durations.append(1690 if value & (1 << bit) else 560)
    durations.append(560)  # the stop mark
    return durations


# A plain NEC press, where the address is sent twice, the second time inverted.
assert decode(frame(0x00, 0x45)) == (0x00, 0x45)
assert decode(frame(0xEF, 0x16)) == (0xEF, 0x16)

# Extended NEC uses those two bytes as one 16 bit address instead.
assert decode(frame(0x2A3C, 0x07, extended=True)) == (0x2A3C, 0x07)

# A held button sends a shorter frame that means "the same again".
assert decode([9000, 2250, 560]) == REPEAT

# Anything that is not a NEC frame is rejected rather than guessed at.
assert decode([]) is None
assert decode([9000]) is None
assert decode([600, 4500] + [560] * 64) is None, "no leader mark"
assert decode([9000, 8000] + [560] * 64) is None, "a leader space of the wrong length"
assert decode([9000, 4500, 560, 560]) is None, "the frame was cut short"

# A command that did not survive the trip is dropped: its check byte will not match.
broken = frame(0x00, 0x45)
broken[3 + 16 * 2] = 1690 if broken[3 + 16 * 2] == 560 else 560  # flip one command bit
assert decode(broken) is None, "a corrupted command is rejected"

# Real receivers are not exact, so the thresholds have to have room in them.
sloppy = frame(0x00, 0x45)
sloppy[0], sloppy[1] = 8400, 4200
for index in range(2, len(sloppy)):
    sloppy[index] = int(sloppy[index] * 0.85)
assert decode(sloppy) == (0x00, 0x45), "a frame 15% short still decodes"

print("ir_receiver: ok")
