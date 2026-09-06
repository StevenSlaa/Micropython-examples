# PWM

This example will show you how to create a fading LED animation with a PWM Signal. 
This example can of course also be used to control servo's, motor drivers, buzzers, analog output, etc.

## Connections

<img alt="connections" src="https://github.com/StevenSlaa/Micropython-examples/blob/f38e5477158664c2d6bfed5009aa8b868ddc54a6/PWM/res/circuit.png" height="300px">

## Output

LED should be slowly fading in and fade out. Every 32nd step is printed, so the console shows
the ramp without being flooded:

```
Duty: 0
Duty: 32
Duty: 64
Duty: 96
```

## Plotter

Open the **Plotter** tab beside the REPL to see the duty cycle as a triangle wave, which is
exactly the ramp the LED brightness is following.

## Tested
This example has been tested on the following microcontroller running MicroPython:
- ESP32 Devkit v1
- ESP32S3 (FeatherS3)
