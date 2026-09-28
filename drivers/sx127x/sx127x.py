# Driver for Semtech SX1276/77/78/79 LoRa radios (SPI), as fitted to the LilyGO T3 LoRa32 and
# most other ESP32 LoRa boards. LoRa mode, point to point: this is not LoRaWAN.
# Datasheet: https://www.semtech.com/products/wireless-rf/lora-connect/sx1276

from micropython import const
from time import sleep_ms, ticks_diff, ticks_ms

_FIFO = const(0x00)
_OP_MODE = const(0x01)
_FRF_MSB = const(0x06)
_PA_CONFIG = const(0x09)
_OCP = const(0x0B)
_LNA = const(0x0C)
_FIFO_ADDR_PTR = const(0x0D)
_FIFO_TX_BASE = const(0x0E)
_FIFO_RX_BASE = const(0x0F)
_FIFO_RX_CURRENT = const(0x10)
_IRQ_FLAGS = const(0x12)
_RX_NB_BYTES = const(0x13)
_PKT_SNR = const(0x19)
_PKT_RSSI = const(0x1A)
_MODEM_CONFIG_1 = const(0x1D)
_MODEM_CONFIG_2 = const(0x1E)
_PREAMBLE_MSB = const(0x20)
_PAYLOAD_LENGTH = const(0x22)
_MODEM_CONFIG_3 = const(0x26)
_INVERT_IQ = const(0x33)
_SYNC_WORD = const(0x39)
_INVERT_IQ_2 = const(0x3B)
_VERSION = const(0x42)
_PA_DAC = const(0x4D)

_LORA = const(0x80)  # in OP_MODE; can only be changed while asleep
_SLEEP = const(0x00)
_STANDBY = const(0x01)
_TX = const(0x03)
_RX_CONTINUOUS = const(0x05)

_RX_DONE = const(0x40)
_CRC_ERROR = const(0x20)
_VALID_HEADER = const(0x10)
_TX_DONE = const(0x08)

_BANDWIDTHS = (7800, 10400, 15600, 20800, 31250, 41700, 62500, 125000, 250000, 500000)
_SETTINGS = ("frequency", "bandwidth", "spreading_factor", "coding_rate", "crc", "sync_word",
             "invert_iq")


class SX127x:
    """A LoRa radio on `spi`, selected by the `cs` pin. `reset` is optional but recommended.

    The radio settings must match on both ends, or nothing is heard: frequency, bandwidth,
    spreading factor, coding rate and sync word. `xtal` is there to trim a crystal that runs off.
    """

    def __init__(self, spi, cs, reset=None, frequency=868_000_000, bandwidth=125_000,
                 spreading_factor=9, coding_rate=5, tx_power=17, sync_word=0x12,
                 preamble_length=8, crc=True, xtal=32_000_000):
        self.spi = spi
        self.cs = cs
        self.xtal = xtal
        self.rssi = None  # of the last packet received, in dBm
        self.snr = None  # of the last packet received, in dB
        self.crc_errors = 0
        self._listening = False
        cs.init(cs.OUT, value=1)

        if reset:
            reset.init(reset.OUT, value=0)
            sleep_ms(1)
            reset(1)
            sleep_ms(10)

        version = self._get(_VERSION)
        if version != 0x12:
            raise OSError("no SX127x found (version 0x%02x), check the wiring" % version)

        self._mode(_SLEEP)
        self._write(_FIFO_TX_BASE, 0)
        self._write(_FIFO_RX_BASE, 0)
        self._write(_LNA, 0x23)  # maximum gain, boosted
        self._write(_PREAMBLE_MSB, bytes((preamble_length >> 8, preamble_length & 0xFF)))
        self._set_power(tx_power)
        self.configure(frequency=frequency, bandwidth=bandwidth, spreading_factor=spreading_factor,
                       coding_rate=coding_rate, crc=crc, sync_word=sync_word, invert_iq=False)

    def configure(self, **settings):
        """Changes radio settings between packets; anything left out keeps its value.

        Takes the constructor's names, plus `invert_iq`: LoRaWAN gateways send with it inverted,
        so that devices do not hear each other.
        """
        for name, value in settings.items():
            if name not in _SETTINGS:
                raise TypeError("unknown setting " + name)
            setattr(self, name, value)
        if self.bandwidth not in _BANDWIDTHS:
            raise ValueError("bandwidth must be one of %s" % (_BANDWIDTHS,))
        if not 7 <= self.spreading_factor <= 12:
            raise ValueError("spreading_factor must be 7 to 12")
        if not 5 <= self.coding_rate <= 8:
            raise ValueError("coding_rate must be 5 to 8, meaning 4/5 to 4/8")

        self._mode(_STANDBY)
        frf = (self.frequency << 19) // self.xtal
        self._write(_FRF_MSB, bytes((frf >> 16, frf >> 8 & 0xFF, frf & 0xFF)))
        self._write(_MODEM_CONFIG_1,
                    _BANDWIDTHS.index(self.bandwidth) << 4 | (self.coding_rate - 4) << 1)
        self._write(_MODEM_CONFIG_2, self.spreading_factor << 4 | (0x04 if self.crc else 0))
        # Symbols longer than 16ms need low data rate optimisation; bit 2 turns on automatic gain.
        slow = (1 << self.spreading_factor) * 1000 > 16 * self.bandwidth
        self._write(_MODEM_CONFIG_3, (0x08 if slow else 0) | 0x04)
        self._write(_SYNC_WORD, self.sync_word)
        self._write(_INVERT_IQ, 0x66 if self.invert_iq else 0x27)
        self._write(_INVERT_IQ_2, 0x19 if self.invert_iq else 0x1D)
        if self._listening:
            self._mode(_RX_CONTINUOUS)

    def _read(self, register, length=1):
        self.cs(0)
        self.spi.write(bytes((register & 0x7F,)))
        data = self.spi.read(length)
        self.cs(1)
        return data

    def _get(self, register):
        return self._read(register)[0]

    def _write(self, register, data):
        self.cs(0)
        self.spi.write(bytes((register | 0x80,)))
        self.spi.write(bytes((data,)) if isinstance(data, int) else data)
        self.cs(1)

    def _mode(self, mode):
        self._write(_OP_MODE, _LORA | mode)

    def _set_power(self, dbm):
        # Through the PA_BOOST pin, which is the one wired to the antenna on nearly every module.
        dbm = min(max(dbm, 2), 20)
        if dbm > 17:
            self._write(_PA_DAC, 0x87)  # the +20dBm mode
            self._write(_OCP, 0x20 | 17)  # current limit 140mA
            dbm -= 3
        else:
            self._write(_PA_DAC, 0x84)
            self._write(_OCP, 0x20 | 11)  # current limit 100mA
        self._write(_PA_CONFIG, 0x80 | (dbm - 2))

    def send(self, data, timeout_ms=10_000):
        """Transmits up to 255 bytes and waits until they are gone. Nothing confirms delivery.

        At spreading factor 12 a full packet takes several seconds, hence the long timeout.
        """
        if not 0 < len(data) <= 255:
            raise ValueError("a packet is 1 to 255 bytes")
        self._mode(_STANDBY)
        self._write(_FIFO_ADDR_PTR, 0)
        self._write(_FIFO, data)
        self._write(_PAYLOAD_LENGTH, len(data))
        self._write(_IRQ_FLAGS, 0xFF)
        self._mode(_TX)
        start = ticks_ms()
        while not self._get(_IRQ_FLAGS) & _TX_DONE:
            if ticks_diff(ticks_ms(), start) > timeout_ms:
                self._mode(_STANDBY)
                raise OSError("send timed out")
            sleep_ms(1)
        self._write(_IRQ_FLAGS, 0xFF)
        if self._listening:
            self.receive()

    def receive(self):
        """Starts listening. Packets are then collected with recv(), and sending resumes it."""
        self._listening = True
        self._write(_IRQ_FLAGS, 0xFF)
        self._mode(_RX_CONTINUOUS)

    def recv(self, timeout_ms=0):
        """The next packet as bytes, or None if none arrives within `timeout_ms`.

        A packet that has started arriving when time runs out is still waited for. Sets `rssi`
        and `snr` for the packet returned.
        """
        start = ticks_ms()
        while True:
            flags = self._get(_IRQ_FLAGS)
            if flags & _RX_DONE:
                break
            if not flags & _VALID_HEADER and ticks_diff(ticks_ms(), start) >= timeout_ms:
                return None
            sleep_ms(1)
        self._write(_IRQ_FLAGS, 0xFF)
        if flags & _CRC_ERROR:
            self.crc_errors += 1
            return None
        length = self._get(_RX_NB_BYTES)
        self._write(_FIFO_ADDR_PTR, self._get(_FIFO_RX_CURRENT))
        data = self._read(_FIFO, length)

        snr = self._get(_PKT_SNR)
        self.snr = (snr - 256 if snr > 127 else snr) / 4
        # The offset depends on which of the chip's two receive ports the band uses.
        self.rssi = self._get(_PKT_RSSI) - (157 if self.frequency > 525_000_000 else 164)
        if self.snr < 0:
            self.rssi += self.snr  # below the noise floor the register alone reads too high
        return data

    def sleep(self):
        """Stops listening and drops the radio to about a microamp until the next send()."""
        self._listening = False
        self._mode(_SLEEP)
