---
driver: dht
author: Steven Slaa
---

# DHT11 and DHT22 readings

Temperature and humidity from the blue DHT11 and the white DHT22, the two sensors in every
starter kit.

**The protocol is already in the firmware.** MicroPython freezes a `dht` module into the ESP32,
ESP8266 and RP2 builds, written in C because the wire protocol is timed in microseconds and
Python cannot hit that reliably. This driver builds on it rather than repeating it, and adds the
three things the bare module leaves to you:

- **Retries.** These sensors fail a checksum every few readings and raise `OSError`. One bad
  reading is normal; a program that does not expect it stops at the first one.
- **The minimum interval.** A DHT11 wants a second between readings and a DHT22 two. Asking
  sooner gives you the same numbers again, or an error. The driver waits out the difference.
- **Fahrenheit and dew point**, which is the reading people actually want from a humidity
  sensor: the temperature at which the air would start to condense.

If all you want is a number and you will handle the errors yourself, `import dht` needs nothing
installed at all.

## Install

Install it from the Pulsar IoT library panel, or copy `dht_sensor.py` to `/lib` on the board.

The file is deliberately not called `dht.py`: that name in `/lib` would shadow the firmware
module this depends on.

## Usage

```python
from machine import Pin
from dht_sensor import DHTSensor

sensor = DHTSensor(Pin(15), "dht22")     # or "dht11"

temperature, humidity = sensor.read()
print(temperature, "C", humidity, "%")
print(sensor.fahrenheit, "F")
print(sensor.dew_point, "C dew point")
```

`read()` retries a few times before giving up, and waits for the sensor to be ready, so a loop
can simply call it:

```python
while True:
    try:
        print(sensor.read())
    except OSError:
        print("The sensor did not answer at all")
```

## Notes

- `read()` blocking for up to two seconds is the sensor's minimum interval being waited out, not
  a hang. Pass `interval_ms=0` if you are timing the loop yourself and know it is long enough.
- An `OSError` that survives every retry is usually the wiring rather than the weather: the data
  pin needs a pull-up resistor of about 10k to 3.3V, and bare modules on three pins often have
  one fitted already while a bare sensor on four pins does not.
- The DHT11 reports whole degrees and whole percent, so its readings step rather than drift. The
  DHT22 gives tenths, is accurate to about half a degree, and costs more.
- The DHT21 and the AM2301 are DHT22s in a different case: use `"dht22"` for them.
- Humidity above about 80% for a long time makes these sensors read high afterwards, sometimes
  for days. That is the part, not the driver.
- `dew_point(temperature, humidity)` is exported and pure, if you want it for readings from
  somewhere else.

## Tests

`python3 -B drivers/dht/test_dht_sensor.py` checks the retries, the interval, the model choice
and the dew point maths against a psychrometric table, off-board.

Used by: [dht-sensor](../../examples/dht-sensor)
