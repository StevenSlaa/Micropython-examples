# I2C Liquid Crystal Display

In this example the microcontroller should display some text on a Liquid Crystal Display (16x2) over I2C. Keep in mind that the LCD needs an I2C Backpack for this example to work.

<img alt="component" src="https://github.com/StevenSlaa/Micropython-examples/blob/7983ad38af327f70dbb2f8daf5f691a32e17937b/I2C%20Liquid%20Crystal%20Display/res/component.png" height="300px">

## Prerequisites
Before running the code, you have to copy all the files from the `lib` folder to the 

## Connections

| LCD | ESP32  |
|-----|--------|
| VCC | VIN    |
| GND | GND    |
| SDA | GPIO21 |
| SCL | GPIO22 |


## Output
<img alt="output" src="https://github.com/StevenSlaa/Micropython-examples/blob/1c1e7031981718a746f92ffb90fc53b857962e73/I2C%20Liquid%20Crystal%20Display/res/output.jpg" height="300px">

## Tested
This example has been tested on the following microcontroller running Micropython:
- ESP32 Devkit
