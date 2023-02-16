# I2C Liquid Crystal Display

In this example the microcontroller should display some text on a Liquid Crystal Display (16x2) over I2C. Keep in mind that the LCD needs an I2C Backpack for this example to work.

## Connections

| LCD | ESP32  |
|-----|--------|
| VCC | VIN    |
| GND | GND    |
| SDA | GPIO21 |
| SCL | GPIO22 |


## Output
```
Temperature: 14.0 C
Temperature: 57.2 F
Humidity: 91.0 %
```

## Tested
This example has been tested on the following microcontroller running Micropython:
- ESP32 Devkit