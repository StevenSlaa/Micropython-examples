# I2C BMP280 Example

In this example the microcontroller reads the temperature and pressure from the connected BMP280 sensor and prints it on the terminal.

<img alt="component" src="https://github.com/StevenSlaa/Micropython-examples/blob/1e6ba049f0c62bf137cfceba978d2491be60b1a1/I2C%20BMP280/res/component.png" height="300px">

## Requires
This example needs the [BMP280](../../drivers/bmp280) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Output
```
Temperature: 17.65 C  Pressure: 1014.9 hPa
Temperature: 17.19 C  Pressure: 1014.7 hPa
Temperature: 17.04 C  Pressure: 1014.6 hPa
Temperature: 17.00 C  Pressure: 1014.5 hPa
Temperature: 17.31 C  Pressure: 1014.5 hPa
```

Pressure is printed in hectopascal, which is the same number weather forecasts use, and is
100 pascal.

## Plotter

Open the **Plotter** tab beside the REPL to graph temperature and pressure together. Pressure
barely moves indoors; carrying the board up a flight of stairs is enough to see it fall.

## Tested
This example has been tested on the following microcontroller running Micropython:
- ESP32 Devkit v1
- ESP32S3 (FeatherS3)
