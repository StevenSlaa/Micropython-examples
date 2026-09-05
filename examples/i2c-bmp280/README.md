# I2C BMP280 Example

In this example the microcontroller reads the temperature and pressure from the connected BMP280 sensor and prints it on the terminal.

<img alt="component" src="https://github.com/StevenSlaa/Micropython-examples/blob/1e6ba049f0c62bf137cfceba978d2491be60b1a1/I2C%20BMP280/res/component.png" height="300px">

## Prerequisites
Before running the code, you have to copy all the files from the `lib` folder to your microcontroller.
> In Thonny, this can be done by opening a python script and then going to File -> Save As -> Microcontroller

## Output
```
Temperature:  17.65 °C
Pressure:  101492.5 Pa
Temperature:  17.19 °C
Pressure:  101474.5 Pa
Temperature:  17.04 °C
Pressure:  101463.4 Pa
Temperature:  17.0 °C
Pressure:  101453.6 Pa
Temperature:  17.31 °C
Pressure:  101453.5 Pa
```

## Tested
This example has been tested on the following microcontroller running Micropython:
- ESP32 Devkit v1
- ESP32S3 (FeatherS3)
