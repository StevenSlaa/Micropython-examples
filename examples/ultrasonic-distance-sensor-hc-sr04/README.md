---
example: ultrasonic-distance-sensor-hc-sr04
author: Steven Slaa
---

# Ultrasonic Distance Sensor (HC-SR04)

The HC-SR04 ultrasonic sensor uses sonar to determine the distance to an object. 
This sensor reads from 2cm to 400cm with an accuracy of 0.3cm.
In this example, the microcontroller reads the distance from the sensor and displays it on the console in centimeters.

<img alt="component" height="300px" src="https://github.com/StevenSlaa/Micropython-examples/blob/c18098d828263c775e02b8f9aa97694fdf396903/Ultrasonic%20Distance%20Sensor%20(HC-SR04)/res/component.png"/>

## Requires
This example needs the [HC-SR04](../../drivers/hcsr04) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.


## Connections

<img alt="connections" src="https://github.com/StevenSlaa/Micropython-examples/blob/79149a3ea3dbd0870895c86d246d96333fec9457/Ultrasonic%20Distance%20Sensor%20(HC-SR04)/res/circuit.png" height="300px">

## Output
```
Distance: 3.230241 cm
Distance: 3.402062 cm
Distance: 3.608247 cm
Distance: 4.484536 cm
Distance: 4.793814 cm
Distance: 4.639175 cm
Distance: 5.378007 cm
Distance: 6.494845 cm
Distance: 5.876288 cm
Distance: 7.783505 cm
Distance: 7.938144 cm
Distance: 8.505155 cm
```

## Plotter

Open the **Plotter** tab beside the REPL to graph the distance. The occasional wild spike is
the sensor missing an echo, which is worth seeing before you rely on a single reading.

## Tested
This example has been tested on the following microcontroller running Micropython:
- ESP32 Devkit v1
- ESP32S3 (FeatherS3)
