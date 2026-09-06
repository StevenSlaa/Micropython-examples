# Driver for a 38kHz infrared receiver module (CHQ1838, VS1838B, TSOP1838 and the rest of the
# three pin family), decoding the NEC protocol that nearly every cheap remote sends.
#
# The module does the hard part: it strips the 38kHz carrier and gives a logic level output,
# idle high, pulled low while the remote is transmitting. What is left is measuring how long
# each pulse lasted, which is what this does.
#
# A NEC frame is a 9ms mark, a 4.5ms space, then 32 bits sent least significant bit first.
# Every bit is a 560us mark; a short space after it means 0 and a long one means 1. Holding a
# button down sends a shorter frame that means "the same again".

from array import array
from machine import Pin, Timer
from micropython import const
from time import ticks_diff, ticks_us

REPEAT = -1  # decode() returns this for the "same again" frame a held button sends

_EDGES = const(68)  # a whole frame is 67 edges; one spare
_LEADER_MARK = (7000, 11000)  # 9ms, generously
_LEADER_SPACE = (3500, 5500)  # 4.5ms, a new button press
_REPEAT_SPACE = (1500, 3000)  # 2.25ms, a held button
_ONE_SPACE = 1000  # a space longer than this is a 1, shorter is a 0


def decode(durations):
    """Turns a list of pulse lengths in microseconds into (address, command).

    Returns REPEAT for a held button, or None for anything that is not a NEC frame, which
    includes the noise a fluorescent lamp or a phone camera puts on the receiver.
    """
    if len(durations) < 2:
        return None
    if not _LEADER_MARK[0] < durations[0] < _LEADER_MARK[1]:
        return None
    if _REPEAT_SPACE[0] < durations[1] < _REPEAT_SPACE[1]:
        return REPEAT
    if not _LEADER_SPACE[0] < durations[1] < _LEADER_SPACE[1]:
        return None
    if len(durations) < 2 + 64:
        return None  # the frame was cut short

    value = 0
    for bit in range(32):
        if durations[3 + bit * 2] > _ONE_SPACE:
            value |= 1 << bit

    address = value & 0xFF
    address_check = (value >> 8) & 0xFF
    command = (value >> 16) & 0xFF
    command_check = (value >> 24) & 0xFF

    if command ^ command_check != 0xFF:
        return None  # the command did not survive the trip
    # Plain NEC sends the address twice, the second time inverted. Extended NEC uses those two
    # bytes as one 16 bit address instead, which is why this checks rather than assumes.
    if address ^ address_check == 0xFF:
        return (address, command)
    return (address | (address_check << 8), command)


class IRReceiver:
    """Calls `callback(address, command, repeat)` for every button press it decodes.

    The callback runs from a timer, so it can allocate and print, but it should still return
    quickly: anything arriving while it runs is missed.
    """

    def __init__(self, pin, callback, block_ms=75):
        self._callback = callback
        self._times = array("i", (0 for _ in range(_EDGES)))
        self._index = 0
        self._last = None
        self._timer = Timer(-1)
        self._block = block_ms
        pin.init(Pin.IN)
        pin.irq(handler=self._edge, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)

    def _edge(self, pin):
        # An interrupt handler, so no allocation here: just a timestamp into an array that
        # already exists.
        if self._index < _EDGES:
            self._times[self._index] = ticks_us()
            self._index += 1
        if self._index == 1:
            # A whole frame takes about 68ms; decode once it has had time to arrive.
            self._timer.init(period=self._block, mode=Timer.ONE_SHOT, callback=self._decode)

    def _decode(self, _):
        count = self._index
        durations = [
            ticks_diff(self._times[i + 1], self._times[i]) for i in range(max(count - 1, 0))
        ]
        self._index = 0
        result = decode(durations)
        if result == REPEAT:
            if self._last:
                self._callback(self._last[0], self._last[1], True)
        elif result:
            self._last = result
            self._callback(result[0], result[1], False)
