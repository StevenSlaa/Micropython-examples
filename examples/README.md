# Examples

Every directory here is one example: a script, a `README.md` explaining it, and an
`example.json` describing it. The IDE reads them from `manifest.json` in the repository root.

New here? Start with the five **Basics**. They are meant to be read in order, and each one ends
with what to try next.

An example names the drivers it needs in `requires`, and the IDE offers to install them when you
open it. Examples with no driver need nothing at all.

<!-- generated:start -->
### Basics

Five short examples, in order. Start here if you have not used a microcontroller before.

| Example | What it does | Needs |
| --- | --- | --- |
| [1. Blink an LED — digital write](blink) | The first program on any microcontroller. | — |
| [2. Button — digital read](button) | When the button is pressed the onboard led (at least for the ESP32) will turn on. | — |
| [3. Analog Read — measuring a knob](analog-read) | Measures a voltage with the analog to digital converter and prints it as a raw number, as volts and as a percentage. | — |
| [4. PWM — analog write](pwm) | This example will show you how to create a fading LED animation with a PWM Signal. | — |
| [5. Dimmer — putting them together](dimmer) | Reads a potentiometer and dims an LED to match, showing how to map any input range onto any output range. | — |

### Sensors

Reading the world: temperature, distance, movement, light and magnetic fields.

| Example | What it does | Needs |
| --- | --- | --- |
| [DHT Sensor Example](dht-sensor) | In this example the microcontroller should display the temperature and humidity in the console. | [dht](../drivers/dht) |
| [I2C BMP280 Example](i2c-bmp280) | In this example the microcontroller reads the temperature and pressure from the connected BMP280 sensor and prints it on the terminal. | [bmp280](../drivers/bmp280) |
| [I2C Compass (GY-271) Example](i2c-compass-gy271) | In this example the microcontroller reads the magnetic field from a GY-271 or HW-246 compass module and prints the three axes and a heading in degrees. | [gy271](../drivers/gy271) |
| [I2C MPU-6050](i2c-mpu-6050) | In this example the microcontrollers reads values from the MPU-6050 accelerometer and gyroscope. | [mpu6050](../drivers/mpu6050) |
| [VCNL4040 Sensor Example](i2c-proximity-vcnl4040) | In this example the microcontroller reads proximity and ambient light from a VCNL4040 sensor, printing the light level in lux and reporting when something comes near. | [vcnl4040](../drivers/vcnl4040) |
| [TOF10120 Sensor Example](i2c-tof-tof10120) | In this example the microcontroller should display the distance that the sensor has measured. | — |
| [VL6180X Sensor Example](i2c-tof-vl6180x) | In this example the microcontroller measures the distance to a nearby object with a VL6180X time of flight sensor, checks whether the reading is valid, and also prints the ambient light level. | [vl6180x](../drivers/vl6180x) |
| [Ultrasonic Distance Sensor (HC-SR04)](ultrasonic-distance-sensor-hc-sr04) | The HC-SR04 ultrasonic sensor uses sonar to determine the distance to an object. | [hcsr04](../drivers/hcsr04) |

### Displays and LEDs

Showing something, from a character display to a matrix or a strip of colour.

| Example | What it does | Needs |
| --- | --- | --- |
| [I2C Liquid Crystal Display Example](i2c-liquid-crystal-display) | In this example the microcontroller should display some text on a Liquid Crystal Display (16x2) over I2C. | [i2c-lcd](../drivers/i2c-lcd) |
| [0.42 inch OLED (ESP32-C3 SuperMini)](oled-042-esp32c3) | Drives the 72x40 OLED built into an ESP32-C3 SuperMini, which is an SH1106 rather than the SSD1306 these boards are usually sold as, and needs its multiplex ratio and display offset set to work at all. | [sh1106](../drivers/sh1106) |
| [P9813 RGB LED Example](p9813-rgb-led) | In this example the microcontroller shows the plain colours on a chain of P9813 RGB LEDs and then cycles a rainbow along it. | [p9813](../drivers/p9813) |
| [Seven Segment Display (74HC595) Example](seven-segment-74hc595) | In this example the microcontroller drives a single 7-segment display through a 74HC595 shift register, counting 0 to 9 and then through the hex letters, using three pins instead of eight. | [sr74hc595](../drivers/sr74hc595) |
| [SPI LED Matrix (MAX7219) Example](spi-led-matrix-max7219) | In this example the microcontroller shows text on a chain of MAX7219 8x8 LED matrix modules and scrolls a message across them. | [max7219](../drivers/max7219) |
| [SPI ST7789 Display Example](spi-st7789-display) | In this example the microcontroller should display some text on a ST7789 240x240 Display over SPI. | [st7789py](../drivers/st7789py) |
| [TM1637 7-Segment Display Example](tm1637-7-segment-display) | In this example the microcontroller writes numbers and text to a TM1637 four digit 7-segment display, then counts minutes and seconds with a blinking colon. | [tm1637](../drivers/tm1637) |

### Motion

Making something move, with motors and servos.

| Example | What it does | Needs |
| --- | --- | --- |
| [DC Motor (L293D / L298N) Example](dc-motor-l293d) | In this example the microcontroller drives a DC motor through an H bridge, ramping the speed up, coasting, running backwards and braking. | [motor](../drivers/motor) |
| [Servo](servo) | In this example the microcontroller drives a hobby servo: a positional one to an angle and back, or a 360 degree one at a speed in both directions. | [servo](../drivers/servo) |
| [Stepper Motor](stepper) | In this example the microcontroller turns a stepper motor a quarter turn at a time, back to where it started, and then releases it. | [stepper](../drivers/stepper) |

### Input

Taking something in from a person: knobs, keypads and card readers.

| Example | What it does | Needs |
| --- | --- | --- |
| [Matrix Keypad (4x4) Example](keypad-4x4) | In this example the microcontroller reads a membrane matrix keypad, collects the digits typed into a code, and checks it when the hash key is pressed. | [keypad](../drivers/keypad) |
| [Rotary Encoder](rotary-encoder) | In this example the microcontroller reads a rotary encoder, counting up and down within a range as the knob is turned, and resetting when it is pressed. | [rotary](../drivers/rotary) |
| [SPI RFID RC522 Example](spi-rfid-rc522) | In this example the microcontroller reads the id of any MIFARE card or tag held against an RFID-RC522 reader, and prints the contents of one block from it. | [mfrc522](../drivers/mfrc522) |

### Remote control

Talking over infrared, in both directions.

| Example | What it does | Needs |
| --- | --- | --- |
| [IR Remote (NEC) Example](ir-remote-nec) | In this example the microcontroller decodes button presses from an infrared remote control with a 38kHz receiver module, prints which button was pressed and toggles the onboard LED. | [ir-receiver](../drivers/ir-receiver) |
| [IR Remote Send (NEC) Example](ir-remote-send) | In this example the microcontroller sends NEC remote control codes from an infrared LED, using the ESP32's RMT peripheral where it exists and a PWM carrier everywhere else. | [ir-transmitter](../drivers/ir-transmitter) |

### Between boards

Getting two boards to talk to each other, by radio or down a wire.

| Example | What it does | Needs |
| --- | --- | --- |
| [nRF24 Radio: Sending](nrf24-send) | In this example the microcontroller sends a counter over a 2.4GHz radio link once a second, and reports whether each packet was acknowledged by the other board. | [nrf24l01](../drivers/nrf24l01) |
| [nRF24 Radio: Receiving](nrf24-receive) | In this example the microcontroller listens for packets over a 2.4GHz radio link, prints the counter in each one and reports any that went missing. | [nrf24l01](../drivers/nrf24l01) |
| [RS-485 Link (MAX485)](rs485-link) | In this example two boards talk to each other over RS-485: one asks a question every second and the other answers, over a pair of wires that works across a building. | [rs485](../drivers/rs485) |

### Networking

Wifi, access points, name lookups and MQTT. Needs a board with a radio: an ESP32 or a Pico W.

| Example | What it does | Needs |
| --- | --- | --- |
| [1. Joining a Wifi Network](wifi-connect) | Connects to a wifi network using the network module directly, showing the status codes as it goes and printing the address, gateway and DNS server it was given. | — |
| [2. Scanning for Networks](wifi-scan) | Lists the wifi networks in range with their channel, signal strength and whether they are open, strongest first. | — |
| [3. Running an Access Point](wifi-access-point) | Turns the board into a wifi network of its own and serves a small web page to any phone or laptop that joins it, which is how a device with no screen gets set up. | [wifi](../drivers/wifi) |
| [4. DNS and Fetching a Page](wifi-dns) | Looks up several hostnames to see which DNS server the router handed out and how long each lookup takes, then fetches a page over a plain socket. | [wifi](../drivers/wifi) |
| [5. MQTT](mqtt) | Publishes readings to an MQTT broker and listens for commands coming back, which is how most small devices send their data somewhere useful. | [wifi](../drivers/wifi), [umqtt](../drivers/umqtt) |

### Bluetooth

Finding devices, being one, and connecting to one over Bluetooth Low Energy.

| Example | What it does | Needs |
| --- | --- | --- |
| [1. Scanning for BLE Devices](ble-scan) | Lists the Bluetooth Low Energy devices advertising nearby, with their signal strength, whether they can be connected to and which services they offer. | [aioble](../drivers/aioble) |
| [2. A BLE Peripheral](ble-peripheral) | Turns the board into a Bluetooth device that advertises a temperature service, which a phone or another board can connect to, read from and subscribe to. | [aioble](../drivers/aioble) |
| [3. A BLE Central](ble-central) | Finds the peripheral from the previous example, connects to it, reads its temperature and then subscribes so new readings arrive on their own. | [aioble](../drivers/aioble) |

### Storage and time

Remembering things after the power goes, and knowing what time it is.

| Example | What it does | Needs |
| --- | --- | --- |
| [I2C EEPROM Example](i2c-eeprom) | In this example the microcontroller stores a boot counter and a message in an I2C EEPROM, so they survive the power being cut, and reads them back. | [eeprom](../drivers/eeprom) |
| [I2C RTC (DS3231) Example](i2c-rtc-ds3231) | In this example the microcontroller reads the date, time and temperature from a DS3231 real time clock module, and copies the time into the board's own clock so it survives a reset. | [ds3231](../drivers/ds3231) |

### Tools

Finding out what is really on the bus.

| Example | What it does | Needs |
| --- | --- | --- |
| [I2C Scanner Example](i2c-scanner) | In this example the microcontrollers scans for devices connected over I2C and displays them to the user on the console. | — |
<!-- generated:end -->

Adding one is a directory with `example.json`, `README.md` and a script — see
[CONTRIBUTING.md](../CONTRIBUTING.md). The table above is written by
`scripts/generate-manifest.py`, and the `group` field in `example.json` decides which section an
example lands in.
