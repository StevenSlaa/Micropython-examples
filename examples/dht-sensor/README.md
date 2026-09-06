# DHT Sensor Example

In this example the microcontroller should display the temperature and humidity in the console.
This information is collected from a DHT11 or DHT22 sensor.

<img alt="component" src="https://github.com/StevenSlaa/Micropython-examples/blob/7bb0472f84f346c6a3762f9aee1ea712502284be/DHT%20Sensor/res/component.png" height="300px">

## Connections

<img alt="connections" src="https://github.com/StevenSlaa/Micropython-examples/blob/5c8e8bb6d6d74850cfbfbe9cf72e1260d307763b/DHT%20Sensor/res/circuit.png" height="300px">


## Output
```
Temperature: 14.0 C  Fahrenheit: 57.2 F  Humidity: 91.0 %
Temperature: 14.0 C  Fahrenheit: 57.2 F  Humidity: 91.1 %
Temperature: 14.1 C  Fahrenheit: 57.4 F  Humidity: 90.8 %
```

## Plotter

Open the **Plotter** tab beside the REPL to graph temperature and humidity as they change.
Breathe on the sensor and both climb.

## Tested
This example has been tested on the following microcontroller running Micropython:
- ESP32 Devkit v1
- ESP32S3 (FeatherS3)
