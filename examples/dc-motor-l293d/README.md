# DC Motor (L293D / L298N) Example

In this example the microcontroller drives a DC motor through an H bridge: ramping the speed up
a step at a time, coasting to a stop, running backwards, and then braking.

Works with an L293D chip or an L298N module, and with the DRV8833 and TB6612 boards, which are
all wired the same way from the board's side.

## Requires
This example needs the [DC motor on an H bridge](../../drivers/motor) driver installed on the
board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

Three pins to the driver, and a separate supply for the motor.

| Driver | ESP32 | Pico |
| --- | --- | --- |
| IN1 | 12 | 12 |
| IN2 | 14 | 13 |
| ENA (enable) | 13 | 14 |
| Motor supply | its own battery or supply | its own battery or supply |
| GND | GND, shared with the board | GND, shared with the board |

**Do not run the motor from the board's 3.3V pin or from USB.** A motor starting or stalling
pulls far more current than a USB port provides, and puts spikes back down the supply that reset
the board. Give it its own supply and join the grounds.

On an L293D, IN1 and IN2 are pins 2 and 7, the enable is pin 1, the motor goes on pins 3 and 6,
and both VCC1 (logic) and VCC2 (motor) need connecting — as do all four ground pins, which are
also the chip's heatsink.

On an L298N module, the enable is jumpered high out of the box. Either take the jumper off and
wire ENA to a pin, or leave it on and set `enable_pin = None` at the top of the script.

## Output
```
Speed: 0.1 forward
Speed: 0.2 forward
...
Speed: 1.0 forward
Coasting
Speed: -0.6 backwards
Braking
```

## Tuning it

If the first few steps make the motor hum without turning, raise `minimum` at the top of the
script until `0.1` moves the shaft. Every motor is different, and there is no way to work it out
except by watching this run.

If the motor runs the wrong way, swap its two wires — or pass `reverse=True` to `Motor`, which
is the tidier answer when two motors face opposite ways on a robot.

A motor that turns weakly at full speed is usually the bridge, not the code: an L293D or L298N
loses about two volts, so a 6V motor on a 6V supply only sees four.

## Plotter

Open the **Plotter** tab beside the REPL to see the speed as it steps up, drops to zero, goes
negative and stops. It is a quick way to see what the script is asking for, though the motor
itself has no feedback: an H bridge cannot tell you what the shaft is really doing.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.
