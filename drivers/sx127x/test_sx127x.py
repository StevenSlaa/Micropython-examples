# Run with: python3 -B drivers/sx127x/test_sx127x.py
# A fake radio behind a fake SPI bus, so the register handling can be checked without a board.
import sys, time, types

sys.modules["micropython"] = types.SimpleNamespace(const=lambda value: value)
time.sleep_ms = lambda ms: None
time.ticks_ms = lambda: int(time.monotonic() * 1000)
time.ticks_diff = lambda a, b: a - b
from sx127x import SX127x  # noqa: E402


class _Pin:
    OUT = 1

    def __init__(self, radio=None):
        self.radio = radio

    def init(self, mode, value=1):
        self(value)

    def __call__(self, value):
        if self.radio and value == 0:
            self.radio.address = None


class _Radio:
    """Registers and a 256 byte FIFO. Going into transmit finishes at once."""

    def __init__(self, version=0x12):
        self.registers = bytearray(128)
        self.registers[0x42] = version
        self.fifo = bytearray(256)
        self.address = None

    def write(self, data):
        for byte in data:
            if self.address is None:
                self.address = byte
            elif self.address == 0x80:
                self._fifo_step(byte)
            elif self.address == 0x92:
                self.registers[0x12] &= ~byte  # writing a one clears that flag
            else:
                self.registers[self.address & 0x7F] = byte
                if self.address == 0x81 and byte & 0x07 == 0x03:
                    self.registers[0x12] |= 0x08
                self.address += 1

    def read(self, length):
        if self.address == 0x00:
            return bytes(self._fifo_step() for _ in range(length))
        return bytes(self.registers[self.address:self.address + length])

    def _fifo_step(self, byte=None):
        pointer = self.registers[0x0D]
        self.registers[0x0D] = (pointer + 1) & 0xFF
        if byte is None:
            return self.fifo[pointer]
        self.fifo[pointer] = byte


def make(**settings):
    radio = _Radio()
    return radio, SX127x(radio, _Pin(radio), **settings)


try:
    SX127x(_Radio(version=0), _Pin())
    raise AssertionError("an absent chip reads version 0")
except OSError:
    pass

radio, lora = make()
r = radio.registers
assert r[0x06:0x09] == b"\xd9\x00\x00", "868MHz"
assert make(frequency=915_000_000)[0].registers[0x06:0x09] == b"\xe4\xc0\x00", "915MHz"
assert make(frequency=433_000_000)[0].registers[0x06:0x09] == b"\x6c\x40\x00", "433MHz"
assert r[0x1D] == 0x72, "125kHz, coding rate 4/5, explicit header"
assert r[0x1E] == 0x94, "spreading factor 9 with CRC"
assert r[0x26] == 0x04, "SF9 at 125kHz is fast enough to skip low data rate optimisation"
assert make(spreading_factor=12)[0].registers[0x26] == 0x0C, "SF12 at 125kHz needs it"
assert r[0x09] == 0x8F and r[0x4D] == 0x84, "17dBm on PA_BOOST"
radio20 = make(tx_power=20)[0].registers
assert radio20[0x09] == 0x8F and radio20[0x4D] == 0x87, "20dBm through the high power DAC"
assert r[0x01] == 0x81, "LoRa, standby"
assert r[0x20:0x22] == b"\x00\x08" and r[0x39] == 0x12, "preamble and sync word"

for bad in ({"bandwidth": 100_000}, {"spreading_factor": 6}, {"coding_rate": 9}):
    try:
        make(**bad)
        raise AssertionError("accepted %s" % bad)
    except ValueError:
        pass

lora.receive()
lora.send(b"hello")
assert radio.fifo[:5] == b"hello" and r[0x22] == 5, "payload in the FIFO, length set"
assert r[0x01] == 0x85, "back to listening after sending"

# A packet arrives: 3 bytes at FIFO offset 10, SNR -2dB, raw RSSI 60.
radio.fifo[10:13] = b"abc"
r[0x10], r[0x13], r[0x19], r[0x1A] = 10, 3, 0xF8, 60
r[0x12] = 0x40
assert lora.recv() == b"abc"
assert lora.snr == -2.0 and lora.rssi == -99.0, "868MHz offset, then the negative SNR"
assert lora.recv() is None, "flags were cleared"

r[0x12] = 0x60
assert lora.recv() is None and lora.crc_errors == 1, "a corrupt packet is counted, not returned"

assert lora.recv(timeout_ms=5) is None, "gives up when nothing arrives"

assert r[0x33] == 0x27 and r[0x3B] == 0x1D, "IQ normal by default"
lora.configure(frequency=869_525_000, spreading_factor=12, invert_iq=True, sync_word=0x34,
               preamble_length=16)
assert r[0x06:0x09] == b"\xd9\x61\x99", "869.525MHz"
assert r[0x1E] == 0xC4 and r[0x26] == 0x0C, "SF12, still with CRC, now slow"
assert r[0x33] == 0x66 and r[0x3B] == 0x19 and r[0x39] == 0x34, "IQ inverted, LoRaWAN sync word"
assert r[0x20:0x22] == b"\x00\x10", "a longer preamble"
assert r[0x01] == 0x85, "still listening after a change"
try:
    lora.configure(power=3)
    raise AssertionError("accepted an unknown setting")
except TypeError:
    pass

lora.sleep()
assert r[0x01] == 0x80, "LoRa, asleep"

print("sx127x: ok")
