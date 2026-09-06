# Button
This is a simple button example script. It will turn an LED on when the button is pressed.

## Connections

<img alt="connections" src="https://github.com/StevenSlaa/Micropython-examples/blob/ff4d2d5b8c2057cb4a459ede48c6f21413e595e1/Button/res/circuit.png" height="300px">

## Output

When the button is pressed the onboard led (at least for the ESP32) will turn on. It will turn of when the button is released.

The state is printed twenty times a second as well:

```
Button: 1
Button: 1
Button: 0
Button: 0
```

## Plotter

Open the **Plotter** tab beside the REPL to see the button as a square wave. It is the
quickest way to see a switch bouncing: a clean press is one step, a bouncy one is a burst of
spikes on the edge.

## Tested
This example has been tested on the following microcontroller running Micropython:
- ESP32 Devkit v1
- ESP32S3 (FeatherS3)
