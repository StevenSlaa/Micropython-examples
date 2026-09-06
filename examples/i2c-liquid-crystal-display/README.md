---
example: i2c-liquid-crystal-display
author: Steven Slaa
---

# I2C Liquid Crystal Display Example

In this example the microcontroller should display some text on a Liquid Crystal Display (16x2) over I2C. Keep in mind that the LCD needs an I2C Backpack for this example to work.

<img alt="component" src="https://github.com/StevenSlaa/Micropython-examples/blob/7983ad38af327f70dbb2f8daf5f691a32e17937b/I2C%20Liquid%20Crystal%20Display/res/component.png" height="300px">

## Requires
This example needs the [I2C character LCD](../../drivers/i2c-lcd) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

<img alt="connections" src="https://github.com/StevenSlaa/Micropython-examples/blob/3548e739fd7f46f988f4fe8fe86e8b875a6e1791/I2C%20Liquid%20Crystal%20Display/res/circuit.png" height="300px">

## Output
<img alt="output" src="https://github.com/StevenSlaa/Micropython-examples/blob/1c1e7031981718a746f92ffb90fc53b857962e73/I2C%20Liquid%20Crystal%20Display/res/output.jpg" height="300px">

## Tested
This example has been tested on the following microcontroller running Micropython:
- ESP32 Devkit v1
- ESP32S3 (FeatherS3)
