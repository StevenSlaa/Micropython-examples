# Contributing

Every contribution is one directory: an example under `examples/`, or a driver under `drivers/`.
Run `python3 scripts/generate-manifest.py` before opening a pull request and commit the generated
`manifest.json` with your change. CI regenerates it and fails on a difference.

## Examples

- Use a lowercase hyphenated directory name.
- Add `example.json`, `README.md`, and at least one `.py` file.
- Set `entry` to the script users should open first.
- List every driver the script imports in `requires`. An example with a `lib/` directory is
  rejected; move the module to `drivers/` instead.
- Put images and datasheets in `res/`, and keep README links relative to the example directory.
- Say which boards you actually tested on, under `## Tested`.

## Drivers

- The directory name is the driver id: lowercase, hyphenated, and what examples put in `requires`.
- Add `driver.json`, `README.md`, and the module files. All `.py` files in the directory are
  installed flat into `/lib`, so name them the way users import them.
- Keep drivers free of example code: no pin numbers, no `while True`, no prints on import.
- Bump `version` in `driver.json` when the module changes; installs compare that version.
- Credit upstream code. Set `license` and `source` in `driver.json`, keep the original header
  comment in the file, and repeat the credit at the bottom of the driver README.
- A driver with real logic of its own (colour maths, unit conversion, a parser) gets a
  `test_<name>.py` next to it that runs on plain CPython, stubbing whatever firmware module it
  needs. `test_*.py` files stay in the repository and are never installed to a board. Vendored
  upstream drivers need no test.
- Leave the tuning knobs in place — timeouts, addresses, offsets, calibration constants — as
  constructor arguments with sensible defaults. Real hardware drifts from the datasheet.

A driver README covers: what the part is, how to install it, a short usage snippet, the gotchas
(addresses, wiring, speed limits), and the credits.

## Not accepted

Executable installers, archives, or vendored dependency trees. The IDE only installs the plain
Python files listed in a hashed manifest.
