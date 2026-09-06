# Drivers

Hardware drivers installed to `/lib` on the board. Each directory is one driver; the directory
name is the id examples put in their `requires` list.

<!-- generated:start -->
| Driver | Modules | Used by |
| --- | --- | --- |
| [bmp280](bmp280) | `bmp280.py` | [i2c-bmp280](../examples/i2c-bmp280) |
| [hcsr04](hcsr04) | `hcsr04.py` | [ultrasonic-distance-sensor-hc-sr04](../examples/ultrasonic-distance-sensor-hc-sr04) |
| [i2c-lcd](i2c-lcd) | `i2c_lcd.py`, `lcd_api.py` | [i2c-liquid-crystal-display](../examples/i2c-liquid-crystal-display) |
| [mfrc522](mfrc522) | `mfrc522.py` | [spi-rfid-rc522](../examples/spi-rfid-rc522) |
| [mpu6050](mpu6050) | `mpu6050.py` | [i2c-mpu-6050](../examples/i2c-mpu-6050) |
| [pixels](pixels) | `pixels.py` | — |
| [ssd1306](ssd1306) | `ssd1306.py` | — |
| [st7789py](st7789py) | `st7789py.py`, `vga2_16x32.py` | [spi-st7789-display](../examples/spi-st7789-display) |
| [tc74](tc74) | `tc74.py` | — |
<!-- generated:end -->

Adding one is a directory with `driver.json`, `README.md`, and the modules — see
[CONTRIBUTING.md](../CONTRIBUTING.md). The table above is written by
`scripts/generate-manifest.py`.
