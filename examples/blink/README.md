# Blink an LED (digital write)

Turn a light on, wait, turn it off, wait, repeat. It is a small thing to build, and it is worth
building first, because it answers a question nothing else can: *is any of this working at all?*

If the light blinks, then the board is alive, the cable carries data, and MicroPython is
running. Everything you build after this stands on that.

## What you will learn

- What a digital output actually does to a pin
- Why a program on a microcontroller never ends
- Why an LED needs a resistor, and what happens when it does not get one

## Wire it up

There may be nothing to wire. Most boards have a small LED soldered on already, and this example
uses it: pin 2 on most ESP32 boards, pin 25 on a Pico. If yours blinks straight away, skip ahead.

To use your own LED, you need it and a resistor of around 330 ohms:

```
GPIO 2 ───[ 330Ω ]───▶|─── GND
                      LED
```

The LED only works one way round. Its longer leg is the positive side and goes towards the
resistor and the pin; the shorter leg, next to the flat edge of the plastic, goes to GND. Back
to front, it simply stays dark — no harm done, so it is worth trying the other way if nothing
lights.

**The resistor is not optional.** An LED does not limit how much current it takes; it will draw
whatever the pin will give, which is enough to damage both of them. The resistor is what keeps
that sensible. Any value from 220Ω to 1kΩ is fine here — a bigger one just means a dimmer LED.

## Run it

The LED turns on for half a second, off for half a second, and the console keeps pace:

```
LED: 1
LED: 0
LED: 1
LED: 0
```

## How it works

```python
led = Pin(led_pin, Pin.OUT)
```

This claims the pin. `Pin.OUT` means your program decides what voltage comes out of it. The
alternative, `Pin.IN`, means the pin listens and something else decides — that is what the
[button example](../button) uses. A pin does one or the other, never both at once.

```python
led.value(1)   # the pin is now at 3.3V
led.value(0)   # the pin is now at 0V
```

That is the whole of digital output. There is no half-on: a digital pin has two states, and the
number 1 or 0 chooses between them. `led.on()` and `led.off()` do exactly the same thing with
friendlier names, and `led.toggle()` flips whichever it currently is.

Nothing here is specific to LEDs. The same two lines switch a relay, a buzzer, or a transistor
driving something much larger. An LED is simply the cheapest way to see that it worked.

```python
while True:
```

A microcontroller has nowhere to go when a program ends. There is no desktop waiting behind it,
so almost every program you write for one will sit in a loop like this forever.

```python
sleep(interval)
```

Computers are fast and eyes are slow. Without the pause, the LED would still turn on and off,
thousands of times a second, and you would see a dim light that never appears to change.

## If it does not work

| What you see | What it usually means |
| --- | --- |
| Nothing at all, no console output | The board is not running the script. Check it is connected and try stopping and running again |
| Console counts, but no light | Wrong pin. Try 2, then 25, then `"LED"` — or you are looking at a different LED to the one you are driving |
| Your own LED stays dark | Back to front. Turn it round; it cannot be harmed by being the wrong way |
| The LED is on constantly | `interval` is very small, or a `sleep` line was lost |
| An error mentioning `machine` | The board is not running MicroPython, or it is running something else that has stopped |

## Plotter

Open the **Plotter** tab beside the REPL. The LED state draws a square wave, one step per half
second — a picture of what the pin is doing, which becomes far more interesting once the thing
being plotted is a real measurement.

## Try changing

- **`interval = 0.05`.** The blink turns into a flicker, and then into a light that just looks
  dimmer. Your eye has stopped keeping up. That effect is the entire idea behind
  [PWM](../pwm), which is how brightness and motor speed are controlled.
- **Two LEDs on different pins**, blinking alternately. One `Pin` object each, and one turns on
  where the other turns off.
- **Take the `sleep` lines out.** The LED appears to be on all the time, though it is actually
  spending half of it off. This is worth seeing once so it is not a surprise later.

## Next

[Button](../button) is the same idea in reverse: reading a pin instead of driving one.

## Tested
This example has not been run on hardware yet. If you try it, add your board here.

---

**The five basics:** [2. Button](../button) · [3. Analog Read](../analog-read) · [4. PWM](../pwm) · [5. Dimmer](../dimmer)
