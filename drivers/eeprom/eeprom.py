# Driver for the 24-series I2C EEPROMs: 24LC01 through 24LC512, AT24C32, CAT24C256 and the
# many parts that copy them.
#
# EEPROM keeps what you write to it with the power off, which RAM does not, and can be
# rewritten, which flash on the board can only do in blocks. It is the right place for a
# setting, a serial number, a calibration constant or a counter.
#
# Two details separate a working driver from one that silently loses data:
#
#   Page writes   A write that runs off the end of a page does not continue into the next one.
#                 It wraps back to the start of the same page and overwrites what it just put
#                 there. The driver splits every write at the page boundaries.
#
#   Write cycles  After a write the chip stops answering for a few milliseconds while it
#                 commits. Rather than guessing at a delay, the driver knocks until it answers
#                 again, which is both faster and safer.

from time import ticks_add, ticks_diff, ticks_ms

# Size in bytes and page size in bytes, by the number in the part name. The letters in front of
# the number differ by manufacturer and do not change anything here.
DEVICES = {
    "24c01": (128, 8),
    "24c02": (256, 8),
    "24c04": (512, 16),
    "24c08": (1024, 16),
    "24c16": (2048, 16),
    "24c32": (4096, 32),
    "24c64": (8192, 32),
    "24c128": (16384, 64),
    "24c256": (32768, 64),
    "24c512": (65536, 128),
}


class EEPROM:
    """An I2C EEPROM.

    `size` and `page_size` are in bytes and must match the part: guessing them too large is how
    data gets quietly overwritten. `for_part()` fills them in from a part number.

    Chips of 2Kbit and under address their memory with one byte; larger ones use two. That
    follows from the size, so it is worked out rather than asked for.
    """

    def __init__(self, i2c, address=0x50, size=32768, page_size=64, timeout_ms=100):
        self.i2c = i2c
        self.address = address
        self.size = size
        self.page_size = page_size
        self.timeout_ms = timeout_ms
        # 256 bytes is all a single address byte can reach.
        self.address_bits = 8 if size <= 256 else 16

    @classmethod
    def for_part(cls, i2c, part, address=0x50, **kwargs):
        """An EEPROM described by its part number, such as "24c256" or "CAT24C256"."""
        key = "".join(character for character in part.lower() if character.isdigit() or character == "c")
        for name, (size, page_size) in DEVICES.items():
            if key.endswith(name) or key.startswith(name):
                return cls(i2c, address, size, page_size, **kwargs)
        raise ValueError("Unknown part %s; pass size and page_size instead" % part)

    def __len__(self):
        return self.size

    def _check(self, offset, length):
        if offset < 0 or length < 0 or offset + length > self.size:
            raise ValueError(
                "Bytes %d to %d are outside this %d byte device" % (offset, offset + length, self.size)
            )

    def _wait(self):
        """Waits for a write to finish, by asking the chip until it answers again."""
        deadline = ticks_add(ticks_ms(), self.timeout_ms)
        while True:
            try:
                self.i2c.writeto(self.address, b"")
                return
            except OSError:
                # Still committing. A chip that never comes back is a real failure, so this
                # gives up eventually rather than hanging.
                if ticks_diff(deadline, ticks_ms()) <= 0:
                    raise OSError("The EEPROM at 0x%02x did not finish writing" % self.address)

    def read(self, offset, length):
        """Reads `length` bytes. Reading may cross pages freely; only writing may not."""
        self._check(offset, length)
        if not length:
            return b""
        return self.i2c.readfrom_mem(self.address, offset, length, addrsize=self.address_bits)

    def write(self, offset, data):
        """Writes bytes, splitting at page boundaries so nothing wraps over itself."""
        self._check(offset, len(data))
        while data:
            # How much room is left in the page this offset falls in.
            room = self.page_size - (offset % self.page_size)
            chunk = data[:room]
            self.i2c.writeto_mem(self.address, offset, chunk, addrsize=self.address_bits)
            self._wait()
            offset += len(chunk)
            data = data[len(chunk) :]

    def fill(self, value=0xFF, offset=0, length=None):
        """Fills a region with one byte. 0xff is what an erased EEPROM reads as."""
        length = self.size - offset if length is None else length
        self.write(offset, bytes([value]) * length)
