# Readings from a DHT11 or DHT22 temperature and humidity sensor.
#
# The protocol itself is already in the firmware: MicroPython freezes a `dht` module into the
# ESP32, ESP8266 and RP2 builds, written in C because the timing is measured in microseconds
# and Python cannot hit it reliably. This builds on that rather than repeating it, and adds the
# parts the bare module leaves to you:
#
#   - retries, because these sensors fail a checksum every few reads and raise
#   - the minimum interval between readings, which is 1 second for a DHT11 and 2 for a DHT22
#   - Fahrenheit and dew point
#
# The file is called dht_sensor.py on purpose: a file named dht.py in /lib would shadow the
# firmware module this depends on.

from math import log
from time import sleep_ms, ticks_diff, ticks_ms

_INTERVALS = {"dht11": 1000, "dht22": 2000}


def dew_point(temperature, humidity):
    """The temperature at which this air would start to condense, in Celsius.

    The Magnus formula, good to about a tenth of a degree between -40C and 50C. Below 1%
    humidity it is meaningless, so that is clamped rather than dividing by zero.
    """
    humidity = min(max(humidity, 1.0), 100.0)
    gamma = (17.62 * temperature) / (243.12 + temperature) + log(humidity / 100.0)
    return (243.12 * gamma) / (17.62 - gamma)


class DHTSensor:
    """A DHT11 or DHT22 on `pin`.

    `model` is "dht11" or "dht22"; the DHT21 and AM2301 are DHT22s in a different case.
    """

    def __init__(self, pin, model="dht22", retries=3, interval_ms=None):
        model = model.lower()
        if model not in _INTERVALS:
            raise ValueError("model must be dht11 or dht22")
        import dht

        self.sensor = dht.DHT11(pin) if model == "dht11" else dht.DHT22(pin)
        self.model = model
        self.retries = retries
        self.interval_ms = _INTERVALS[model] if interval_ms is None else interval_ms
        self.temperature = None
        self.humidity = None
        self._last = None

    def _wait_for_the_interval(self):
        """These sensors return the same reading, or an error, if asked again too soon."""
        if self._last is None:
            return
        waited = ticks_diff(ticks_ms(), self._last)
        if waited < self.interval_ms:
            sleep_ms(self.interval_ms - waited)

    def read(self):
        """Returns (temperature in Celsius, humidity in percent), retrying on a bad reading.

        Raises OSError if every attempt fails, which usually means the wiring rather than the
        weather: a missing pull-up resistor, or a data pin that is not the one in the code.
        """
        error = None
        for attempt in range(self.retries):
            self._wait_for_the_interval()
            self._last = ticks_ms()
            try:
                self.sensor.measure()
                self.temperature = self.sensor.temperature()
                self.humidity = self.sensor.humidity()
                return (self.temperature, self.humidity)
            except OSError as failure:
                # A checksum failure is normal every few reads; only the last one is a problem.
                error = failure
        raise error

    @property
    def fahrenheit(self):
        """The last temperature in Fahrenheit, or None before the first read."""
        return None if self.temperature is None else self.temperature * 9 / 5 + 32

    @property
    def dew_point(self):
        """The dew point of the last reading, in Celsius, or None before the first read."""
        if self.temperature is None or self.humidity is None:
            return None
        return dew_point(self.temperature, self.humidity)
