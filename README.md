# MicroPython Examples

A contributor friendly collection of MicroPython examples for sensors, displays, and actuators.

## Add an example

1. Create a directory under `examples/` using a lowercase, hyphenated name.
2. Add an `example.json`, a `README.md`, and one or more Python files.
3. Put reusable modules in `lib/` and documentation images or datasheets in `res/`.
4. Run `python3 scripts/generate-manifest.py` and review the generated `manifest.json`.
5. Commit the example and manifest together.

`example.json` is the metadata contract:

```json
{
  "id": "button",
  "title": "Button",
  "description": "Turns an LED on while a button is pressed.",
  "boardTags": ["esp32", "esp32s3"],
  "entry": "button.py"
}
```

The IDE loads `manifest.json`, keeps README files available for preview, and installs files from `lib/` as managed drivers when declared by a catalog.
