# Analog Read and Write (dimmer)

Turn a knob, and an LED gets brighter. Two examples you have already met, joined in the middle.

That join is the point of this one. Almost every project you build is something measured on one
side, something moved or lit or sounded on the other, and a few lines between them deciding how
one becomes the other. Those few lines look the same every time, and this is them.

## What you will learn

- How to map any input range onto any output range, without learning a formula for each pair
- Why writing the obvious-looking step out in full saves you later
- What "gamma" means, and why a linear fade does not look linear

## Wire it up

The [analog read](../analog-read) and [PWM](../pwm) examples at the same time, sharing nothing
but the board.

```
3.3V ───\/\/\/\/\/\─── GND          the knob
              │
            wiper ───── GPIO 34

GPIO 2 ───[ 330Ω ]───▶|─── GND      the LED
```

| | ESP32 | Pico |
| --- | --- | --- |
| Knob wiper | 34 | 26 |
| LED | 2 | 15 |

On an ESP32 the analog pin has to be between 32 and 39, or the reading stops changing as soon as
wifi comes on. Most boards already have an LED on pin 2 or 25 if you would rather not wire one.

## Run it

Turn the knob. The LED follows.

```
Raw:     0  Brightness: 0.0
Raw: 21845  Brightness: 33.3
Raw: 65535  Brightness: 100.0
```

## How it works: mapping one range onto another

An input and an output almost never share a scale. A knob gives 0 to 65535. A servo wants 40 to
115. A volume setting wants 0 to 30. A thermostat works in degrees. Sooner or later you need to
join two of them, and the temptation is to work out a formula for that particular pair.

Do not. Do it in two steps instead:

```python
fraction = raw / 65535          # step one: how far along, from 0.0 to 1.0
duty = int(fraction * 65535)    # step two: stretch that to what the output wants
```

Step one turns *anything* into a plain fraction. Step two turns a fraction into *anything*. In
between, your program does not care what the input was — which means you can swap the knob for a
light sensor, or a temperature, and only the first line changes.

Here both ends are 16-bit, so step two looks like it multiplies by exactly what step one divided
by, and does nothing. Write it out regardless. The day the LED becomes a servo:

```python
angle = int(40 + fraction * (115 - 40))
```

Only that line moves, and you can see at a glance that it is right. That is worth more than the
multiplication you saved.

## What PWM is doing

A pin cannot output half a volt. What it can do is switch between 0V and 3.3V a thousand times a
second and spend a chosen share of that time on. To your eye — or a motor, or a heater — that
behaves like something in between.

```python
led.duty_u16(0)       # off
led.duty_u16(32768)   # on half the time: half brightness
led.duty_u16(65535)   # fully on
```

That share is called the duty cycle. It is not really a dimmer at all; it is very fast blinking,
which is exactly what the [blink example](../blink) turns into when you make the
interval small enough.

## If it does not work

| What you see | What it usually means |
| --- | --- |
| The LED is on or off with nothing between | `duty_u16` is being given only 0 or 65535 — print `fraction` and check it moves |
| The numbers move but the LED does not | The LED is on a pin that cannot do PWM, or is wired the wrong way round |
| The LED flickers visibly | `frequency` is too low. A few hundred is the lower limit for a light |
| The reading never changes | On an ESP32, an ADC2 pin with wifi on. Use 32 to 39 |
| The LED is brightest with the knob turned down | The knob's outer legs are the other way round. Swap them, or invert it in code as below |

## Try changing

- **Turn it round:** `fraction = 1 - (raw / 65535)`. Turning the knob up now dims the LED.
- **Square it:** `fraction = fraction ** 2`. The fade suddenly looks much more even. Your eye
  does not respond to light in a straight line — halving the power looks far less than half as
  bright — so a straight mapping spends most of the knob's travel in a range that all looks the
  same. Correcting for that is called gamma, and it is why the
  [pixels driver](../../drivers/pixels) has a gamma setting for LED strips.
- **Drive something else.** A servo, using the mapping above and the pins from the
  [servo example](../servo). Same two lines, different second number.
- **Add a second knob** on another pin and a second LED, and watch them work independently.

## Plotter

Open the **Plotter** tab beside the REPL and turn the knob. Two lines move together: the raw
reading and the brightness as a percentage. They are the same information at two different
scales, which is a fair picture of what the mapping in the middle is for.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.

---

**The five basics:** [1. Blink](../blink) · [2. Button](../button) · [3. Analog Read](../analog-read) · [4. PWM](../pwm)
