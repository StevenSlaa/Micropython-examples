# Button (digital read)
This is a simple button example script. It will turn an LED on when the button is pressed.

## What you will learn

- How to read a pin instead of driving one
- Why a button needs a pull-up resistor, and what goes wrong without one
- Why pressing a button reads as 0 rather than 1

## What a digital read is

`button.value()` asks one question about a pin: is there a voltage on it? The answer is 1 or 0,
and there is nothing in between.

The awkward part is not the press. It is what the pin reads when the button is *not* pressed.

A switch does one thing: it connects two wires when you push it. While it is open, it connects
nothing — so the pin is attached to nothing at all. A pin attached to nothing is not 0. It is a
tiny aerial, picking up whatever electrical noise is in the room, and it will read 1 and 0 at
random. That is called a floating pin, and it is behind a great many "my button presses itself"
problems.

The fix is in the third argument:

```python
button = Pin(12, Pin.IN, Pin.PULL_UP)
```

`PULL_UP` switches on a resistor inside the chip that gently holds the pin up at 3.3V. Now an
open switch reads 1, reliably, every time — and the button's job becomes pulling the pin down to
GND, which reads 0.

Which is why **a press reads 0**, and why the button's other leg goes to GND rather than to
3.3V. It feels upside down the first time. The script writes it out as
`pressed = not button.value()` so the rest of the code can say what it means.

## If it does not work

| What you see | What it usually means |
| --- | --- |
| Pressed flickers between 0 and 1 on its own | The pull-up is missing, or the button's other leg is not on GND |
| Always 1, never 0 | The button is wired to 3.3V rather than GND, or to a different pin |
| Always 0, never 1 | The button is stuck closed, or its two legs are on the wrong pair of pins |
| A burst of spikes on each press | Contact bounce, which is real and normal — see the plotter note below |

Push buttons have four legs, and they are joined in pairs before you press anything. If it
behaves as though it is permanently pressed, turn it a quarter turn.

## Connections

<img alt="connections" src="https://github.com/StevenSlaa/Micropython-examples/blob/ff4d2d5b8c2057cb4a459ede48c6f21413e595e1/Button/res/circuit.png" height="300px">

## Output

When the button is pressed the onboard led (at least for the ESP32) will turn on. It will turn of when the button is released.

The state is printed twenty times a second as well, as 1 while the button is held:

```
Pressed: 0
Pressed: 0
Pressed: 1
Pressed: 1
```

The pin itself reads the other way round — 1 when nothing is happening — which is what the
`not` in the script is for. Printing what you mean, rather than what the pin says, is worth the
extra word.

## Plotter

Open the **Plotter** tab beside the REPL to see the button as a square wave, 1 while held. It is
the quickest way to see a switch bouncing: a clean press is one step, a bouncy one is a burst of
spikes on the edge. The [keypad driver](../../drivers/keypad) exists mostly to deal with that.

## Tested
This example has been tested on the following microcontroller running Micropython:
- ESP32 Devkit v1
- ESP32S3 (FeatherS3)

---

**The five basics:** [1. Blink](../blink) · [3. Analog Read](../analog-read) · [4. PWM](../pwm) · [5. Dimmer](../dimmer)
