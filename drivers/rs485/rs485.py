# Driver for the MAX485 and the RS-485 transceivers like it: MAX3485, SP3485, SN75176 and the
# blue breakout boards built around them.
#
# RS-485 is not a protocol. It is a way of carrying ordinary serial a long way — a kilometre is
# routine — by sending it as the difference between two wires instead of against ground, which
# is what makes it survive electrical noise that would ruin a plain UART. What you send over it
# is still up to you.
#
# The catch is that it is half duplex: one pair of wires, so only one device may talk at a time,
# and each has to say which it is doing. That is the DE and RE pins, normally wired together to
# one GPIO: high to talk, low to listen.
#
# Getting that pin back down too early is the classic RS-485 bug. uart.write() returns as soon
# as the bytes are handed to the hardware, not when they have left the wire, so dropping the
# line there cuts the end off every message. This driver waits.

from time import sleep_us, ticks_diff, ticks_ms


class RS485:
    """An RS-485 transceiver on `uart`, with DE and RE tied to `de`.

    `baudrate` must match the UART's, because it is how long a byte takes to leave that decides
    when it is safe to stop transmitting. `bits_per_byte` is 10 for the usual 8N1 — one start
    bit, eight data, one stop — and 11 if you have added parity or a second stop bit.
    """

    def __init__(self, uart, de, baudrate=9600, bits_per_byte=10, margin_us=100):
        self.uart = uart
        self.de = de
        self.baudrate = baudrate
        self.bits_per_byte = bits_per_byte
        # A little longer than the sums say, because being late costs nothing and being early
        # truncates the message.
        self.margin_us = margin_us
        de.init(de.OUT, value=0)
        self._listen()

    def _listen(self):
        self.de.value(0)

    def _talk(self):
        self.de.value(1)

    def byte_time_us(self, count=1):
        """How long `count` bytes take to leave at this baud rate."""
        return count * self.bits_per_byte * 1_000_000 // self.baudrate

    def write(self, data):
        """Sends `data`, and does not return until it has actually left the wire."""
        self._talk()
        try:
            written = self.uart.write(data)
            self._drain(len(data))
        finally:
            # Back to listening whatever happened: a transceiver left talking holds the whole
            # bus down and nothing else on it can say a word.
            self._listen()
        return written

    def _drain(self, count):
        """Waits for the last bit to leave, which is not the same as write() returning."""
        txdone = getattr(self.uart, "txdone", None)
        if txdone is not None:
            # Ports that can tell us are worth asking, but not worth trusting forever.
            deadline = ticks_ms() + self.byte_time_us(count) // 1000 + 20
            while not txdone() and ticks_diff(deadline, ticks_ms()) > 0:
                pass
        else:
            sleep_us(self.byte_time_us(count))
        sleep_us(self.margin_us)

    def any(self):
        """How many bytes have arrived and are waiting."""
        return self.uart.any()

    def read(self, count=None):
        return self.uart.read() if count is None else self.uart.read(count)

    def readline(self):
        return self.uart.readline()

    def query(self, data, timeout_ms=200, terminator=None):
        """Sends `data` and waits for a reply, which is how most RS-485 links are used.

        Returns what arrived, or None if nothing did before the timeout. With `terminator` set
        it waits for that to appear at the end; without it, it returns as soon as anything has
        arrived and no more has followed for a whole byte's time.
        """
        while self.uart.any():
            self.uart.read()  # anything left over from last time is not this answer
        self.write(data)

        reply = b""
        deadline = ticks_ms() + timeout_ms
        while ticks_diff(deadline, ticks_ms()) > 0:
            if self.uart.any():
                reply += self.uart.read() or b""
                if terminator and reply.endswith(terminator):
                    return reply
                if not terminator:
                    # Give the sender a moment to add more before deciding it has finished.
                    sleep_us(self.byte_time_us(2))
                    if not self.uart.any():
                        return reply
            else:
                sleep_us(200)
        return reply or None
