# Drivers

Hardware drivers installed to `/lib` on the board. Each directory is one driver; the directory
name is the id examples put in their `requires` list.

<!-- generated:start -->
| Driver | Modules | Used by |
| --- | --- | --- |
| [bmp280](bmp280) | `bmp280.py` | [i2c-bmp280](../examples/i2c-bmp280) |
| [dht](dht) | `dht_sensor.py` | [dht-sensor](../examples/dht-sensor) |
| [ds3231](ds3231) | `ds3231.py` | [i2c-rtc-ds3231](../examples/i2c-rtc-ds3231) |
| [eeprom](eeprom) | `eeprom.py` | [i2c-eeprom](../examples/i2c-eeprom) |
| [gy271](gy271) | `gy271.py` | [i2c-compass-gy271](../examples/i2c-compass-gy271) |
| [hcsr04](hcsr04) | `hcsr04.py` | [ultrasonic-distance-sensor-hc-sr04](../examples/ultrasonic-distance-sensor-hc-sr04) |
| [i2c-lcd](i2c-lcd) | `i2c_lcd.py`, `lcd_api.py` | [i2c-liquid-crystal-display](../examples/i2c-liquid-crystal-display) |
| [ir-receiver](ir-receiver) | `ir_receiver.py` | [ir-remote-nec](../examples/ir-remote-nec) |
| [ir-transmitter](ir-transmitter) | `ir_transmitter.py` | [ir-remote-send](../examples/ir-remote-send) |
| [keypad](keypad) | `keypad.py` | [keypad-4x4](../examples/keypad-4x4) |
| [max7219](max7219) | `max7219.py` | [spi-led-matrix-max7219](../examples/spi-led-matrix-max7219) |
| [mfrc522](mfrc522) | `mfrc522.py` | [spi-rfid-rc522](../examples/spi-rfid-rc522) |
| [motor](motor) | `motor.py` | [dc-motor-l293d](../examples/dc-motor-l293d) |
| [mpu6050](mpu6050) | `mpu6050.py` | [i2c-mpu-6050](../examples/i2c-mpu-6050) |
| [p9813](p9813) | `p9813.py` | [p9813-rgb-led](../examples/p9813-rgb-led) |
| [pixels](pixels) | `pixels.py` | — |
| [rotary](rotary) | `rotary.py` | [rotary-encoder](../examples/rotary-encoder) |
| [servo](servo) | `servo.py` | [servo](../examples/servo) |
| [sr74hc595](sr74hc595) | `sr74hc595.py` | [seven-segment-74hc595](../examples/seven-segment-74hc595) |
| [ssd1306](ssd1306) | `ssd1306.py` | — |
| [st7789py](st7789py) | `st7789py.py`, `vga2_16x32.py` | [spi-st7789-display](../examples/spi-st7789-display) |
| [stepper](stepper) | `stepper.py` | [stepper](../examples/stepper) |
| [tc74](tc74) | `tc74.py` | — |
| [tm1637](tm1637) | `tm1637.py` | [tm1637-7-segment-display](../examples/tm1637-7-segment-display) |
| [vcnl4040](vcnl4040) | `vcnl4040.py` | [i2c-proximity-vcnl4040](../examples/i2c-proximity-vcnl4040) |
| [vl6180x](vl6180x) | `vl6180x.py` | [i2c-tof-vl6180x](../examples/i2c-tof-vl6180x) |
<!-- generated:end -->

Adding one is a directory with `driver.json`, `README.md`, and the modules — see
[CONTRIBUTING.md](../CONTRIBUTING.md). The table above is written by
`scripts/generate-manifest.py`.
