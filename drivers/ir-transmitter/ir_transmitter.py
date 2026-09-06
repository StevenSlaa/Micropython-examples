# Sends NEC infrared remote codes through an IR LED.
#
# Transmitting is not like receiving: the 38kHz carrier has to be gated by pulses measured in
# hundreds of microseconds, and how well a board can do that depends on what hardware it has.
# This picks the best available at run time rather than being told which board it is on:
#
#   RMT  an ESP32 peripheral built for exactly this. The carrier and the pulse train are
#        generated in hardware, so the timing is exact and nothing else on the board disturbs it.
#   PWM  everywhere else, including the Pico. The carrier is a PWM channel switched on and off
#        by sleep_us, which is accurate to tens of microseconds. NEC receivers are tolerant
#        enough that this works, but a badly timed interrupt can spoil a frame.
#
# `backend` says which one is in use.

_BIT_MARK = 560
_ONE_SPACE = 1690
_ZERO_SPACE = 560
_LEADER = (9000, 4500)
_REPEAT_FRAME = (9000, 2250, 560)


def encode(address, command):
    """A NEC frame as alternating mark and space lengths in microseconds, starting with a mark.

    An address above 0xff is sent as a 16 bit extended address; below that it is sent the plain
    way, twice, the second time inverted.
    """
    if address > 0xFF:
        value = address & 0xFFFF
    else:
        value = (address & 0xFF) | ((address ^ 0xFF) << 8)
    value |= ((command & 0xFF) << 16) | ((command ^ 0xFF) << 24)

    pulses = [_LEADER[0], _LEADER[1]]
    for bit in range(32):
        pulses.append(_BIT_MARK)
        pulses.append(_ONE_SPACE if value & (1 << bit) else _ZERO_SPACE)
    pulses.append(_BIT_MARK)  # the stop mark, which closes the last bit's space
    return pulses


class _RMTCarrier:
    """The ESP32's remote control peripheral, which does the whole job in hardware."""

    name = "rmt"

    def __init__(self, pin, frequency, duty):
        from esp32 import RMT

        # clock_div 80 makes one tick one microsecond, which is what the pulse lengths are in.
        self._rmt = RMT(0, pin=pin, clock_div=80, tx_carrier=(frequency, duty, 1))

    def send(self, pulses):
        # The first pulse is a mark, so the train starts with the carrier on.
        self._rmt.write_pulses(tuple(pulses), 1)
        self._rmt.wait_done(timeout=200)


class _PWMCarrier:
    """A PWM channel switched on and off in software. Works anywhere, timed less exactly."""

    name = "pwm"

    def __init__(self, pin, frequency, duty):
        from machine import PWM

        self._pwm = PWM(pin)
        self._pwm.freq(frequency)
        self._level = int(65535 * duty // 100)
        self._pwm.duty_u16(0)

    def send(self, pulses):
        from time import sleep_us

        pwm = self._pwm
        level = self._level
        for index, duration in enumerate(pulses):
            # Even entries are marks, with the carrier running; odd ones are silence.
            pwm.duty_u16(level if index % 2 == 0 else 0)
            sleep_us(duration)
        pwm.duty_u16(0)


class IRTransmitter:
    """Sends NEC codes from an IR LED on `pin`.

    >>> transmitter = IRTransmitter(Pin(4))
    >>> transmitter.send(0x00, 0x45)          # the code a receiver would report
    >>> print(transmitter.backend)            # 'rmt' or 'pwm'
    """

    def __init__(self, pin, frequency=38000, duty=33, carrier=None):
        if carrier is None:
            try:
                carrier = _RMTCarrier(pin, frequency, duty)
            except (ImportError, AttributeError, ValueError, OSError):
                # No RMT on this board, or its channel is taken: fall back to plain PWM.
                carrier = _PWMCarrier(pin, frequency, duty)
        self._carrier = carrier
        self.backend = carrier.name

    def send(self, address, command, repeats=0):
        """Sends one button press, then `repeats` "same again" frames as if it were held."""
        self._carrier.send(encode(address, command))
        for _ in range(repeats):
            self._gap()
            self._carrier.send(list(_REPEAT_FRAME))

    def send_raw(self, pulses):
        """Sends mark and space lengths directly, for a protocol this driver does not know."""
        self._carrier.send(list(pulses))

    def _gap(self):
        from time import sleep_ms

        # A real remote repeats every 108ms; the frame already took most of that.
        sleep_ms(40)
