# Run with: python3 -B drivers/dht/test_dht_sensor.py
# A sensor that can be told to fail, and a clock that can be watched, so the retries and the
# minimum interval can be checked without waiting two seconds a reading.
import sys, types

clock = [0]
slept = []
sys.modules["time"] = types.SimpleNamespace(
    ticks_ms=lambda: clock[0],
    ticks_diff=lambda a, b: a - b,
    sleep_ms=lambda ms: (slept.append(ms), clock.__setitem__(0, clock[0] + ms)),
)


class _FakeDHT:
    def __init__(self, pin, failures=0):
        self.pin = pin
        self.failures = failures
        self.measures = 0
        self._temperature = 21.5
        self._humidity = 48.0

    def measure(self):
        self.measures += 1
        if self.failures:
            self.failures -= 1
            raise OSError("checksum error")

    def temperature(self):
        return self._temperature

    def humidity(self):
        return self._humidity


made = []


def _make(kind):
    def build(pin):
        sensor = _FakeDHT(pin, failures=_make.failures)
        sensor.kind = kind
        made.append(sensor)
        return sensor

    return build


_make.failures = 0
sys.modules["dht"] = types.SimpleNamespace(DHT11=_make("dht11"), DHT22=_make("dht22"))
from dht_sensor import DHTSensor, dew_point  # noqa: E402

# The model picks the firmware class and the interval the datasheet asks for.
assert DHTSensor(0, "dht22").interval_ms == 2000
assert DHTSensor(0, "dht11").interval_ms == 1000
assert made[-1].kind == "dht11" and made[-2].kind == "dht22"
try:
    DHTSensor(0, "dht99")
    raise AssertionError("an unknown model must be refused")
except ValueError:
    pass

# A good reading comes straight back, and is kept for the derived values.
clock[0], slept[:] = 0, []
sensor = DHTSensor(0, "dht22")
assert sensor.temperature is None and sensor.fahrenheit is None, "nothing before the first read"
assert sensor.read() == (21.5, 48.0)
assert sensor.fahrenheit == 70.7, sensor.fahrenheit
assert not slept, "the first reading does not wait"

# The second reading waits out the rest of the interval rather than failing or repeating itself.
clock[0] += 300
sensor.read()
assert slept == [1700], slept

# A checksum failure is normal; the retry is what matters.
clock[0], slept[:] = 0, []
_make.failures = 2
sensor = DHTSensor(0, "dht22")
assert sensor.read() == (21.5, 48.0), "two failures then a good reading"
assert made[-1].measures == 3, made[-1].measures
assert slept == [2000, 2000], "and it waits the interval between attempts"

# A sensor that never answers raises, rather than returning something invented.
clock[0] = 0
_make.failures = 99
sensor = DHTSensor(0, "dht11", retries=2)
try:
    sensor.read()
    raise AssertionError("a sensor that always fails must raise")
except OSError:
    pass
assert made[-1].measures == 2, "it gave up after the retries it was given"
_make.failures = 0

# Dew point, against figures from a psychrometric table.
assert abs(dew_point(20.0, 50.0) - 9.26) < 0.05, dew_point(20.0, 50.0)
assert abs(dew_point(30.0, 80.0) - 26.16) < 0.05, dew_point(30.0, 80.0)
assert abs(dew_point(20.0, 100.0) - 20.0) < 0.05, "saturated air condenses at its own temperature"
assert dew_point(20.0, 0.0) < -20, "no division by zero at zero humidity"

clock[0] = 0
sensor = DHTSensor(0, "dht22")
assert sensor.dew_point is None, "nothing before the first read"
sensor.read()
assert abs(sensor.dew_point - dew_point(21.5, 48.0)) < 0.001

print("dht_sensor: ok")
