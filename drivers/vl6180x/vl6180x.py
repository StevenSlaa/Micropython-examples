# Driver for the ST VL6180X time of flight range and ambient light sensor.
#
# The register map and the mandatory start-up sequence below come from ST's datasheet and
# application note AN4545; the same sequence appears in ST's own and Adafruit's drivers.
# Datasheet: https://www.st.com/resource/en/datasheet/vl6180x.pdf

from micropython import const
from time import sleep_ms, ticks_add, ticks_diff, ticks_ms

VL6180X_ADDRESS = const(0x29)

# Analogue gain for the light sensor. The names are the multiplier, not the register value.
GAIN_1 = const(0x06)
GAIN_1_25 = const(0x05)
GAIN_1_67 = const(0x04)
GAIN_2_5 = const(0x03)
GAIN_5 = const(0x02)
GAIN_10 = const(0x01)
GAIN_20 = const(0x00)
GAIN_40 = const(0x07)
_GAIN_VALUES = {
    GAIN_1: 1.0,
    GAIN_1_25: 1.25,
    GAIN_1_67: 1.67,
    GAIN_2_5: 2.5,
    GAIN_5: 5.0,
    GAIN_10: 10.0,
    GAIN_20: 20.0,
    GAIN_40: 40.0,
}

_MODEL_ID = const(0x000)
_INTERRUPT_CONFIG = const(0x014)
_INTERRUPT_CLEAR = const(0x015)
_FRESH_OUT_OF_RESET = const(0x016)
_SYSRANGE_START = const(0x018)
_MAX_CONVERGENCE_TIME = const(0x01C)
_RANGE_OFFSET = const(0x024)
_SYSALS_START = const(0x038)
_ALS_GAIN = const(0x03F)
_ALS_INTEGRATION_HI = const(0x040)
_ALS_INTEGRATION_LO = const(0x041)
_RANGE_STATUS = const(0x04D)
_INTERRUPT_STATUS = const(0x04F)
_ALS_VALUE = const(0x050)
_RANGE_VALUE = const(0x062)

# Register, value pairs. The 0x0000-0x02ff block is ST's undocumented tuning; the rest is the
# recommended public configuration. Skipping any of it gives a sensor that reads, but badly.
_STARTUP = (
    (0x0207, 0x01), (0x0208, 0x01), (0x0096, 0x00), (0x0097, 0xFD), (0x00E3, 0x00),
    (0x00E4, 0x04), (0x00E5, 0x02), (0x00E6, 0x01), (0x00E7, 0x03), (0x00F5, 0x02),
    (0x00D9, 0x05), (0x00DB, 0xCE), (0x00DC, 0x03), (0x00DD, 0xF8), (0x009F, 0x00),
    (0x00A3, 0x3C), (0x00B7, 0x00), (0x00BB, 0x3C), (0x00B2, 0x09), (0x00CA, 0x09),
    (0x0198, 0x01), (0x01B0, 0x17), (0x01AD, 0x00), (0x00FF, 0x05), (0x0100, 0x05),
    (0x0199, 0x05), (0x01A6, 0x1B), (0x01AC, 0x3E), (0x01A7, 0x1F), (0x0030, 0x00),
    (0x0011, 0x10),  # interrupt on new sample ready
    (0x010A, 0x30),  # averaging sample period
    (0x003F, 0x46),  # light and dark gain
    (0x0031, 0xFF),  # auto calibrate every 255 measurements
    (0x0040, 0x63),  # 100ms light integration time
    (0x002E, 0x01),  # one temperature calibration of the ranging sensor
    (0x001B, 0x09),  # 100ms between ranging measurements
    (0x003E, 0x31),  # 500ms between light measurements
    (0x0014, 0x24),  # interrupt on new sample ready threshold event
)

# RESULT__RANGE_STATUS >> 4. Anything but 0 means the millimetres are not to be trusted.
RANGE_ERRORS = {
    0: "ok",
    1: "system error",
    2: "system error",
    3: "system error",
    4: "system error",
    5: "system error",
    6: "early convergence estimate failed",
    7: "no convergence, nothing in range",
    8: "ignore threshold hit",
    11: "signal to noise too low, target too dark or too far",
    12: "raw reading underflow",
    13: "raw reading overflow",
    14: "reading underflow, target too close",
    15: "reading overflow, target too far",
}


class VL6180X:
    """A VL6180X on `i2c`. Ranges to about 100mm, or 200mm against something white and matt.

    `offset` is added to every range reading, in millimetres, to trim the part to part
    variation: put a target at a known distance, and correct what you see.
    """

    def __init__(self, i2c, address=VL6180X_ADDRESS, offset=0, timeout=500):
        self.i2c = i2c
        self.address = address
        self.offset = offset
        self.timeout = timeout
        if self._read(_MODEL_ID) != 0xB4:
            raise OSError("No VL6180X at 0x%02x" % address)
        # Written every time, not only when the sensor's fresh-out-of-reset flag is set. The
        # flag clears on the first run and stays clear while the sensor keeps its power, which a
        # board being reset over USB does not touch: keying off it leaves an untuned sensor that
        # answers every register but cannot see anything.
        for register, value in _STARTUP:
            self._write(register, value)
        self._write(_FRESH_OUT_OF_RESET, 0x00)

    def _read(self, register, length=1):
        data = self.i2c.readfrom_mem(self.address, register, length, addrsize=16)
        return data[0] if length == 1 else int.from_bytes(data, "big")

    def _write(self, register, value):
        self.i2c.writeto_mem(self.address, register, bytes([value]), addrsize=16)

    def _wait(self, shift):
        """Blocks until the sensor flags a new sample, in the range or the light half."""
        deadline = ticks_add(ticks_ms(), self.timeout)
        while ((self._read(_INTERRUPT_STATUS) >> shift) & 0x07) != 0x04:
            if ticks_diff(deadline, ticks_ms()) <= 0:
                raise OSError("The VL6180X did not finish a measurement in time")
            sleep_ms(1)

    @property
    def range(self):
        """Distance to the target in millimetres, from a single measurement."""
        self._write(_SYSRANGE_START, 0x01)
        self._wait(0)
        millimetres = self._read(_RANGE_VALUE)
        self._write(_INTERRUPT_CLEAR, 0x07)
        return millimetres + self.offset

    @property
    def range_status(self):
        """0 when the last range reading was good, otherwise a key of RANGE_ERRORS."""
        return self._read(_RANGE_STATUS) >> 4

    def lux(self, gain=GAIN_1):
        """Ambient light in lux. Use a higher gain in a dim room, a lower one in daylight."""
        if gain not in _GAIN_VALUES:
            raise ValueError("Use one of the GAIN_ constants")
        config = (self._read(_INTERRUPT_CONFIG) & ~0x38) | (0x04 << 3)
        self._write(_INTERRUPT_CONFIG, config)
        self._write(_ALS_INTEGRATION_HI, 0x00)
        self._write(_ALS_INTEGRATION_LO, 100)  # 100ms, which the 0.32 factor below assumes
        self._write(_ALS_GAIN, 0x40 | gain)
        self._write(_SYSALS_START, 0x01)
        self._wait(3)
        counts = self._read(_ALS_VALUE, 2)
        self._write(_INTERRUPT_CLEAR, 0x07)
        return counts * 0.32 / _GAIN_VALUES[gain]

    @property
    def convergence_time(self):
        """Milliseconds the sensor may spend gathering light for one range reading, 1 to 63.

        Raise it when readings come back as "early convergence estimate failed" or "signal to
        noise too low" against a target that is dark, angled, or near the far end of the range;
        the cost is a slower measurement.
        """
        return self._read(_MAX_CONVERGENCE_TIME)

    @convergence_time.setter
    def convergence_time(self, milliseconds):
        self._write(_MAX_CONVERGENCE_TIME, max(1, min(63, milliseconds)))

    @property
    def part_to_part_offset(self):
        """The sensor's own range offset register, in millimetres, signed."""
        value = self._read(_RANGE_OFFSET)
        return value - 256 if value > 127 else value

    @part_to_part_offset.setter
    def part_to_part_offset(self, millimetres):
        self._write(_RANGE_OFFSET, millimetres & 0xFF)
