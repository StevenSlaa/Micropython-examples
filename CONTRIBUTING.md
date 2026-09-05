# Contributing examples

Each contribution belongs in its own directory under `examples/`:

- Use a lowercase hyphenated directory name.
- Add `example.json`, `README.md`, and at least one `.py` file.
- Set `entry` in `example.json` to the script users should open first.
- Put reusable Python modules in `lib/` and images or datasheets in `res/`.
- Keep README image links relative to the example directory where possible.
- Run `python3 scripts/generate-manifest.py` before opening a pull request.

The generator validates metadata, hashes downloadable files, and updates `manifest.json`. Commit
that generated file with the example changes. Do not add executable installers or archives; the IDE
only installs declared Python files from trusted, hashed manifests.
