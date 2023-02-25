# I2C MPU-6050

In this example the microcontrollers reads values from the MPU-6050 accelerometer and gyroscope. It also reads the onboard temperature sensor of the module.

<img alt="connections" src="https://github.com/StevenSlaa/Micropython-examples/blob/adffd6056a8a4bac9a3405aee203a59e8154fbd3/I2C%20MPU-6050/res/component.jpg" height="300px">

## Connections

<img alt="connections" src="" height="300px">

## Output

```
{'GyZ': 169, 'GyY': 138, 'GyX': -467, 'Tmp': 20.53, 'AcZ': 13012, 'AcY': -400, 'AcX': -2588}
{'GyZ': 167, 'GyY': 149, 'GyX': -488, 'Tmp': 20.53, 'AcZ': 12996, 'AcY': -432, 'AcX': -2536}
{'GyZ': 179, 'GyY': 139, 'GyX': -486, 'Tmp': 20.53, 'AcZ': 13068, 'AcY': -380, 'AcX': -2548}
{'GyZ': 166, 'GyY': 134, 'GyX': -493, 'Tmp': 20.57706, 'AcZ': 13028, 'AcY': -260, 'AcX': -2552}
{'GyZ': 171, 'GyY': 130, 'GyX': -474, 'Tmp': 20.67117, 'AcZ': 12976, 'AcY': -296, 'AcX': -2600}
```

## Tested
This example has been tested on the following microcontroller running MicroPython:
- ESP32 Devkit v1
- ESP32S3 (FeatherS3)
