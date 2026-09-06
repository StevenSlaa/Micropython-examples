# Run with: python3 -B drivers/mfrc522/test_mfrc522.py
# Stubs machine so the patched constructor and the added helpers can be checked off-board.
import sys, types


class _Pin:
    OUT = 3

    def __init__(self, id, mode=None):
        self.id, self.mode, self.level = id, mode, None

    def value(self, level):
        self.level = level


class _SoftSPI:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.written = bytearray()

    def write(self, data):
        self.written += data

    def read(self, n, token=0):
        return bytes(n)


sys.modules["machine"] = types.SimpleNamespace(Pin=_Pin, SoftSPI=_SoftSPI, SPI=_SoftSPI)
from mfrc522 import MFRC522, uid_hex  # noqa: E402

assert uid_hex([0xDE, 0xAD, 0xBE, 0xEF, 0x00]) == "de:ad:be:ef", "the checksum byte is dropped"
assert uid_hex(b"\x01\x02\x03\x04") == "01:02:03:04", "bytes work as well as a list"

reader = MFRC522(sck=18, mosi=23, miso=19, rst=4, cs=5)
assert isinstance(reader.spi, _SoftSPI), "a bus is built when none is given"
assert reader.spi.kwargs["baudrate"] == 1000000
assert [reader.spi.kwargs[name].id for name in ("sck", "mosi", "miso")] == [18, 23, 19]
assert reader.rst.mode == _Pin.OUT and reader.cs.mode == _Pin.OUT, "control pins are outputs"
assert reader.rst.level == 1, "the reader is released from reset"
assert reader.spi.written, "init() talked to the reader"

bus = _SoftSPI()
shared = MFRC522(sck=None, mosi=None, miso=None, rst=_Pin(4, _Pin.OUT), cs=_Pin(5, _Pin.OUT), spi=bus)
assert shared.spi is bus, "a hardware bus is used as given"
assert shared.cs.id == 5, "an existing Pin is not rewrapped"

# request() never sees a card against the stub, so scan() has to report an empty field.
assert reader.scan() is None, "no card in the field"

print("mfrc522: ok")
