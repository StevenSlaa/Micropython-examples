# DHT Sensor Example

In this example the microcontroller should display the temperature and humidity in the console,
along with the dew point. This information is collected from a DHT11 or DHT22 sensor.

Set `model` at the top of the script to `"dht11"` for the blue sensor or `"dht22"` for the white
one.

## Requires
This example needs the [DHT11 and DHT22 readings](../../drivers/dht) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

The wire protocol itself is already in the firmware, as MicroPython's built-in `dht` module. The
driver adds what that leaves out: retrying the checksum failures these sensors produce every few
readings, waiting out the minimum interval between readings, and the dew point.

<img alt="component" src="https://github.com/StevenSlaa/Micropython-examples/blob/7bb0472f84f346c6a3762f9aee1ea712502284be/DHT%20Sensor/res/component.png" height="300px">

## Connections

<img alt="connections" src="https://github.com/StevenSlaa/Micropython-examples/blob/5c8e8bb6d6d74850cfbfbe9cf72e1260d307763b/DHT%20Sensor/res/circuit.png" height="300px">


## Output
```
Temperature: 14.0 C  Fahrenheit: 57.2 F  Humidity: 91.0 %  Dew point: 12.5 C
Temperature: 14.0 C  Fahrenheit: 57.2 F  Humidity: 91.1 %  Dew point: 12.5 C
Temperature: 14.1 C  Fahrenheit: 57.4 F  Humidity: 90.8 %  Dew point: 12.6 C
```

The dew point is the temperature at which this air would start to condense. Reaching it on a
window or a wall is what damp is.

There is no delay in the loop: `read()` waits out the sensor's own minimum interval, which is a
second for a DHT11 and two for a DHT22.

## Plotter

Open the **Plotter** tab beside the REPL to graph temperature, humidity and dew point as they
change. Breathe on the sensor and all three climb, humidity fastest.

## Tested
This example has been tested on the following microcontroller running Micropython:
- ESP32 Devkit v1
- ESP32S3 (FeatherS3)
