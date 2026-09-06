# MicroPython Examples

A contributor friendly collection of MicroPython examples and hardware drivers for sensors,
displays, and actuators.

```
examples/<example-id>/    example.json, README.md, the script, res/ images
drivers/<driver-id>/      driver.json, README.md, the driver modules
manifest.json             generated catalog, do not edit by hand
```

Examples never carry driver code. A driver lives once in `drivers/`, and every example that needs
it names it in `requires`. The IDE installs those modules to `/lib` on the board.

## Add an example

1. Create a directory under `examples/` using a lowercase, hyphenated name.
2. Add `example.json`, `README.md`, and one or more Python files. Put images or datasheets in `res/`.
3. List the driver ids the script imports in `requires`.
4. Run `python3 scripts/generate-manifest.py` and commit `manifest.json` with your change.

```json
{
  "id": "i2c-bmp280",
  "title": "I2C BMP280 Example",
  "description": "Reads temperature and pressure from a BMP280 and prints it.",
  "boardTags": ["esp32", "esp32s3", "pico"],
  "entry": "I2C BMP280.py",
  "requires": ["bmp280"]
}
```

## Add a driver

1. Create a directory under `drivers/` named exactly like the driver id.
2. Add `driver.json`, `README.md`, and the module files. Every `.py` in the directory is installed
   to `/lib`, so keep the file names the ones users `import`.
3. Run `python3 scripts/generate-manifest.py`.

```json
{
  "id": "bmp280",
  "name": "BMP280",
  "version": "1.0.0",
  "description": "Temperature and pressure driver for the Bosch BMP280 over I2C or SPI.",
  "boardTags": ["esp32", "esp32s3", "pico"],
  "license": "MIT",
  "source": "https://github.com/dafvid/micropython-bmp280"
}
```

`license` and `source` are optional; fill them in for anything you did not write yourself.

Examples print one named value per reading, on a single line, so the IDE plotter can graph them
without any extra work: `Temperature: 17.6 C  Pressure: 1014.9 hPa`. The rules are in
[CONTRIBUTING.md](CONTRIBUTING.md).

See [CONTRIBUTING.md](CONTRIBUTING.md) for the review rules and [drivers/README.md](drivers/README.md)
for the current driver list.
