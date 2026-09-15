# Driver for the Silergy SY6970 single-cell LiPo charger, as fitted to LilyGO boards such as the
# T-Display-S3 Long. It is register compatible with TI's BQ25895.
# Register map and scaling: lewisxhe's XPowersLib, https://github.com/lewisxhe/XPowersLib
#
# Every register is one byte. Voltages are in millivolts and currents in milliamps.

from micropython import const

SY6970_ADDRESS = const(0x6A)

_INPUT_LIMIT = const(0x00)
_ADC = const(0x02)
_CONFIG = const(0x03)
_CHARGE_LIMIT = const(0x04)
_CHARGE_VOLTAGE = const(0x06)
_TIMER = const(0x07)
_STATUS = const(0x0B)
_FAULTS = const(0x0C)
_BATTERY_VOLTAGE = const(0x0E)
_SYSTEM_VOLTAGE = const(0x0F)
_INPUT_VOLTAGE = const(0x11)
_CHARGE_CURRENT = const(0x12)

# charge_state values, in the order of their 2 bit code
CHARGE_STATES = ("not charging", "pre-charge", "fast charging", "charged")
# input values, in the order of their 3 bit code
INPUTS = ("none", "USB host", "USB charging port", "USB charger", "fast charger", "adapter", "adapter", "OTG")


class SY6970:
    """An SY6970 battery charger on `i2c`.

    The chip starts with a watchdog that resets all its settings every 40 seconds unless software
    keeps talking to it. With `watchdog=False`, the default, it is switched off so settings stay.
    The chip's voltage and current measurements are switched on, once a second.
    """

    def __init__(self, i2c, address=SY6970_ADDRESS, watchdog=False):
        self.i2c = i2c
        self.address = address
        try:
            self._update(_ADC, 0xC0, 0xC0)  # start measuring, continuously
            if not watchdog:
                self._update(_TIMER, 0x30, 0x00)
        except OSError:
            raise OSError("No SY6970 found at I2C address 0x%02X. Check the wiring and the address." % address)

    def _read(self, register):
        return self.i2c.readfrom_mem(self.address, register, 1)[0]

    def _update(self, register, mask, value):
        self.i2c.writeto_mem(self.address, register, bytes(((self._read(register) & ~mask & 0xFF) | value,)))

    @property
    def charge_enabled(self):
        """Whether the chip may charge the battery. Switch it off when no battery is connected."""
        return bool(self._read(_CONFIG) & 0x10)

    @charge_enabled.setter
    def charge_enabled(self, enabled):
        self._update(_CONFIG, 0x10, 0x10 if enabled else 0x00)

    @property
    def charge_state(self):
        """One of CHARGE_STATES: "not charging", "pre-charge", "fast charging" or "charged"."""
        return CHARGE_STATES[self._read(_STATUS) >> 3 & 0x03]

    @property
    def input(self):
        """What powers the board from outside, one of INPUTS, such as "USB host" or "none"."""
        return INPUTS[self._read(_STATUS) >> 5]

    @property
    def power_good(self):
        """True while the input supply is good enough to run the board and charge."""
        return bool(self._read(_STATUS) & 0x04)

    @property
    def battery_voltage(self):
        """Battery voltage in mV, or 0 when the chip measures nothing there."""
        steps = self._read(_BATTERY_VOLTAGE) & 0x7F
        return 2304 + 20 * steps if steps else 0

    @property
    def system_voltage(self):
        """The voltage the chip supplies to the board, in mV."""
        return 2304 + 20 * (self._read(_SYSTEM_VOLTAGE) & 0x7F)

    @property
    def input_voltage(self):
        """USB or other input voltage in mV, or 0 when there is none."""
        value = self._read(_INPUT_VOLTAGE)
        return 2600 + 100 * (value & 0x7F) if value & 0x80 else 0

    @property
    def charge_current(self):
        """Current flowing into the battery in mA, 0 when not charging."""
        if self._read(_STATUS) >> 3 & 0x03 == 0:
            return 0  # the register keeps its last value after charging stops
        return 50 * (self._read(_CHARGE_CURRENT) & 0x7F)

    @property
    def charge_current_limit(self):
        """The most current, in mA, the chip charges with: 0 to 5056 in steps of 64."""
        return 64 * (self._read(_CHARGE_LIMIT) & 0x7F)

    @charge_current_limit.setter
    def charge_current_limit(self, milliamps):
        self._update(_CHARGE_LIMIT, 0x7F, min(max(milliamps, 0), 5056) // 64)

    @property
    def input_current_limit(self):
        """The most current, in mA, the chip draws from its input: 100 to 3250 in steps of 50."""
        return 100 + 50 * (self._read(_INPUT_LIMIT) & 0x3F)

    @input_current_limit.setter
    def input_current_limit(self, milliamps):
        self._update(_INPUT_LIMIT, 0x3F, (min(max(milliamps, 100), 3250) - 100) // 50)

    @property
    def charge_voltage(self):
        """The voltage, in mV, the battery is charged to: 3840 to 4608 in steps of 16."""
        return 3840 + 16 * (self._read(_CHARGE_VOLTAGE) >> 2)

    @charge_voltage.setter
    def charge_voltage(self, millivolts):
        self._update(_CHARGE_VOLTAGE, 0xFC, (min(max(millivolts, 3840), 4608) - 3840) // 16 << 2)

    @property
    def faults(self):
        """The fault register; 0 means no faults. The chip clears it when it is read.

        0x80 watchdog expired, 0x40 boost fault, 0x30 charge fault, 0x08 battery over-voltage,
        0x07 temperature sensor.
        """
        return self._read(_FAULTS)
