---
example: i2c-mpu-6050
author: Steven Slaa
---

# I2C MPU-6050

In this example the microcontrollers reads values from the MPU-6050 accelerometer and gyroscope. It also reads the onboard temperature sensor of the module.

<img alt="connections" src="https://github.com/StevenSlaa/Micropython-examples/blob/f5ef3bed8fac0e379a0fa9e9e35f7617a5f39d7c/I2C%20MPU-6050/res/component.png" height="300px">

## Requires
This example needs the [MPU-6050](../../drivers/mpu6050) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

<img alt="connections" src="" height="300px">

## Output

```
AcX: -2588  AcY: -400  AcZ: 13012
AcX: -2536  AcY: -432  AcZ: 12996
AcX: -2548  AcY: -380  AcZ: 13068
AcX: -2552  AcY: -260  AcZ: 13028
AcX: -2600  AcY: -296  AcZ: 12976
```

`get_values()` also returns `GyX`, `GyY`, `GyZ` and `Tmp`. Swap them into the print at the
bottom of the script to watch the gyroscope or the on-chip temperature instead; three values
of a similar size plot better together than seven of wildly different ones.

## Plotter

Open the **Plotter** tab beside the REPL to graph the three acceleration axes. Tilting the
board trades gravity between them; tapping the desk shows up as a spike.

## Tested
This example has been tested on the following microcontroller running MicroPython:
- ESP32 Devkit v1
- ESP32S3 (FeatherS3)
