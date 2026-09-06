# Written by Steven Slaa

from machine import Pin
from dht_sensor import DHTSensor

# Configuration
# pin the sensor's data leg is connected to
data_pin = 15
# "dht11" for the blue sensor, "dht22" for the white one. A DHT21 or AM2301 is a dht22.
model = "dht11"

# The driver waits out the sensor's minimum interval between readings on its own, and retries
# the checksum failures these sensors produce every few readings.
sensor = DHTSensor(Pin(data_pin), model)

while True:
    try:
        temperature, humidity = sensor.read()
    except OSError:
        # Every retry failed, which usually means the wiring rather than the weather.
        print("The sensor did not answer")
        continue

    # One line per reading, with a name for each value: the IDE plotter draws a series per
    # name, so two lines both called Temperature would land in the same one.
    print(
        "Temperature: %3.1f C  Fahrenheit: %3.1f F  Humidity: %3.1f %%  Dew point: %3.1f C"
        % (temperature, sensor.fahrenheit, humidity, sensor.dew_point)
    )
