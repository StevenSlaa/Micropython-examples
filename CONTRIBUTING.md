# Contributing

Every contribution is one directory: an example under `examples/`, or a driver under `drivers/`.
Run `python3 scripts/generate-manifest.py` before opening a pull request and commit the generated
`manifest.json` with your change. CI regenerates it and fails on a difference.

## Examples

- Use a lowercase hyphenated directory name, usually the part it uses.
- A set meant to be read in sequence, like the basics, sets `order` in `example.json` to say
  which comes first. Leave it out otherwise: examples without one are listed alphabetically
  within their group.
- Add `example.json`, `README.md`, and at least one `.py` file.
- Set `entry` to the script users should open first.
- Put it in a `group`, which decides where it appears in the IDE's library panel and in the
  index in [examples/README.md](examples/README.md). The groups are listed in
  `scripts/generate-manifest.py`, in the order they are shown:
  **Basics**, **Sensors**, **Displays and LEDs**, **Motion**, **Input**, **Remote control**,
  **Storage and time**, **Tools**. A group of your own works too, and lands at the end; add it
  to that list if it deserves a place of its own. Leaving `group` out puts the example in
  "Other", which is visible in the index rather than silently hidden.
- List every driver the script imports in `requires`. An example with a `lib/` directory is
  rejected; move the module to `drivers/` instead.
- Put images and datasheets in `res/`, and keep README links relative to the example directory.
- Say which boards you actually tested on, under `## Tested`.
- Print readings in a shape the IDE plotter can graph, and add a `## Plotter` section saying
  what there is to see. The rules are short:
  - One line per sample, with every value on it. Two lines are two samples, so splitting
    temperature and humidity across two prints plots them against each other in time.
  - Name each value: `Temperature: 21.4`. A bare number still plots, as "Series 1".
  - Separate pairs with **two** spaces. One space lets the unit run into the next name, so
    `X: 1 uT Y: 2` gives a series called `uT Y`.
  - Units after the value are ignored, so `Distance: 43 mm  Light: 214 lux` is two clean series.
  - Four series is the maximum, and they share one scale: values of a similar size plot well
    together, a pressure in pascal next to a temperature does not.
  - Lines with no number are skipped, so error messages and headings do no harm.

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
  needs. Run it with `python3 -B` so it leaves no `__pycache__` behind. `test_*.py` files stay in
  the repository and are never installed to a board. Vendored upstream drivers need no test.
- Leave the tuning knobs in place — timeouts, addresses, offsets, calibration constants — as
  constructor arguments with sensible defaults. Real hardware drifts from the datasheet.

A driver README covers: what the part is, how to install it, a short usage snippet, the gotchas
(addresses, wiring, speed limits), and the credits.

## Not accepted

Executable installers, archives, or vendored dependency trees. The IDE only installs the plain
Python files listed in a hashed manifest.
