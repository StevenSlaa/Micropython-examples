---
example: camera-ov3660
author: Steven Slaa
---

# OV3660 Camera Example

In this example the microcontroller takes a photo with the OV3660 camera on a XIAO ESP32-S3
Sense and saves it to the board as a JPEG, once every five seconds. Open `/photo.jpg` from the
file panel to see it.

## Firmware

**This example does not run on a stock MicroPython build.** The camera is driven by a C module
in the firmware, so the board needs a build that has one:
[micropython-camera-API](https://github.com/cnadler86/micropython-camera-API) publishes a
prebuilt binary for the XIAO ESP32-S3 Sense. On a stock build the first line fails with
`ImportError: no module named 'camera'`.

## Requires
This example needs the [OV3660](../../drivers/ov3660) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Wiring

None. The camera sits on the board-to-board connector between the XIAO and its Sense expansion
board, so the only thing to get wrong is seating the two boards crookedly.

## Output
```
Camera started
Bytes: 41893
Bytes: 41766
Bytes: 39204
Bytes: 52011
Bytes: 51488
```

## Plotter

Open the **Plotter** tab beside the REPL to graph the size of each photo. A JPEG of a dark or a
flat scene compresses smaller, so the line drops when you cover the lens and jumps when
something detailed moves in front of it. It is a crude light and motion sensor that happens to
also be a camera.

## Things to try

- `size = FrameSize.QXGA` for the sensor's full 2048x1536, at about a second a frame.
- The picture arrives upside down without the driver's `vflip`, and washed out without its
  `brightness` and `saturation`. All three are arguments to `camera()`; see the
  [driver README](../../drivers/ov3660) for what they do.
- Saving every photo under its own name fills the flash in a few minutes. An SD card in the
  Sense board's slot is the place for that.

## Tested
This example has been tested on the following microcontroller running Micropython:
- Seeed XIAO ESP32-S3 Sense, with the camera-enabled firmware above
