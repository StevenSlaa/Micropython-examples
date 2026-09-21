---
driver: ov3660
author: Steven Slaa
---

# OV3660 camera

The OmniVision OV3660 is the three megapixel camera on the Seeed XIAO ESP32-S3 Sense
expansion board. It talks over a parallel DVP bus: eight data lines, a pixel clock at 20MHz,
and a small I2C bus on the side for its settings.

## Firmware first

**A stock MicroPython build cannot use this camera, and this module cannot change that.** Frames
arrive faster than Python can read pins, so the driver is the C `camera` module inside the
firmware, using the ESP32-S3's LCD_CAM peripheral and DMA. Flash a build that includes it:

> [cnadler86/micropython-camera-API](https://github.com/cnadler86/micropython-camera-API)
> publishes prebuilt binaries, including one for the XIAO ESP32-S3 Sense.

Without it, `import ov3660` fails with `ImportError: no module named 'camera'`.

## Install

Install it from the Pulsar IoT library panel, or copy `ov3660.py` to `/lib` on the board.

## Usage

```python
from ov3660 import camera, FrameSize

cam = camera(frame_size=FrameSize.SVGA)
photo = cam.capture()          # a JPEG, as bytes
with open("/photo.jpg", "wb") as file:
    file.write(photo)
cam.deinit()
```

`camera()` returns the firmware's own `Camera` object, so everything that documents applies:
`capture()`, `reconfigure()`, `deinit()`, and the `set_*` settings. `FrameSize`, `PixelFormat`
and `GrabMode` are re-exported here so an example only imports one module.

## Settings

| Argument | Default | What it does |
| --- | --- | --- |
| `frame_size` | `FrameSize.SVGA` | 800x600. `QQVGA` to `QXGA`, the sensor's full 2048x1536. |
| `pixel_format` | `PixelFormat.JPEG` | `RGB565` and `GRAYSCALE` are raw, and much larger. |
| `jpeg_quality` | `12` | 0 to 63, and **lower is better**, which is backwards from most software. |
| `pins` | `XIAO_ESP32S3_SENSE` | The pin map. Another board with an OV3660 brings its own. |
| `vflip` | `True` | See below. |
| `brightness` | `1` | -2 to 2. |
| `saturation` | `-2` | -2 to 2. |

Anything else, `xclk_freq`, `fb_count`, `grab_mode`, passes straight to the firmware.

## Gotchas

- **The picture is upside down without `vflip`.** An OV3660 reads out the other way up from the
  OV2640 that most ESP32 camera code was written for, and it comes out pale and oversaturated
  besides. The three defaults above are what the esp32-camera component applies itself when it
  recognises this sensor. They are a starting point: your light is not the light they were
  picked in, so pass your own, or `None` to leave the sensor's default alone.
- **Camera already in use.** The firmware driver survives a soft reset, so running a script
  twice without `deinit()` fails on the second run. Press the reset button, or call `deinit()`
  when the script ends.
- **A large frame needs PSRAM.** The XIAO ESP32-S3 Sense has 8MB of it and is fine up to QXGA.
  A board without PSRAM manages QVGA at best.
- **The pins are not wired, they are etched.** The sensor sits on the board-to-board connector
  under the expansion board. There is nothing to connect and nothing to get wrong.
- The same pin map drives the OV2640 that ships on some XIAO Sense boards, but the corrections
  above are the OV3660's; pass `vflip=None, brightness=None, saturation=None` for that sensor.

## Credits

The sensor driver is the [esp32-camera](https://github.com/espressif/esp32-camera) component,
exposed to MicroPython by [cnadler86](https://github.com/cnadler86/micropython-camera-API).
This module is the board's pin map and the OV3660's corrections around it.
