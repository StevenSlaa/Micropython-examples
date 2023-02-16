# DHT Sensor Example

In this example the microcontroller should display the temperature and humidity in the console.
This information is collected from a DHT11 or DHT22 sensor.

## Connections

| DHT | ESP32  |
|-----|--------|
| VCC | 3.3V   |
| GND | GND    |
| DAT | GPIO15 |


## Output
```
Temperature: 14.0 C
Temperature: 57.2 F
Humidity: 91.0 %
```

## Tested
This example has been tested on the following microcontroller running Micropython:
- ESP32 Devkit