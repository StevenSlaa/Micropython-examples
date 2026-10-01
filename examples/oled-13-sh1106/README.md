---
example: oled-13-sh1106
author: Steven Slaa
---

# 1.3 inch OLED (SH1106, 128x64)

Drives a 1.3 inch 128x64 OLED from a Raspberry Pi Pico. It cycles through four scenes:

1. A border and title, to check the geometry: all four edges should sit on the edge of the glass.
2. Bouncing balls.
3. A scrolling sine wave.
4. A dashboard with the Pico's internal temperature, uptime and a graph of the last readings.

128x64 is the panel the SH1106 was made for, so the driver needs no setup or offsets.

## Requires
This example needs the [SH1106 OLED](../../drivers/sh1106) driver installed on the board.
> Install it from the library panel in the Pulsar IoT IDE, or copy the driver's `.py`
> files into `/lib` on the microcontroller yourself.

## Connections

| OLED | Pico |
| --- | --- |
| VCC | 3V3 |
| GND | GND |
| SDA | GP6 |
| SCL | GP7 |

The display is at I2C address `0x3C`.

## Troubleshooting

- **`OSError: [Errno 5] EIO` with hardware `I2C`**: the module can answer a scan but fail every
  write when the pull-ups are weak. That is why the example uses `SoftI2C`.
- **Image shifted two pixels, with noise in an edge column**: the module is really an SSD1306.
  Use the [ssd1306](../../drivers/ssd1306) driver instead.
- **Temperature a few degrees off**: the RP2040 sensor is uncalibrated. Set `temp_trim` in
  `dashboard()`.
