#!/usr/bin/env python3
"""Validate examples and drivers, and generate the immutable Pulsar IoT catalog."""
from pathlib import Path
import hashlib, json, mimetypes, os

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
DRIVERS = ROOT / "drivers"
VERSION = os.environ.get("CATALOG_VERSION", "1.0.0")
BASE = "https://raw.githubusercontent.com/StevenSlaa/Micropython-examples/refs/heads/main"

def entry(path: Path, relative_to: Path):
    data = path.read_bytes()
    relative = path.relative_to(ROOT).as_posix().replace(" ", "%20")
    return {"path": path.relative_to(relative_to).as_posix(), "url": f"{BASE}/{relative}",
            "sha256": hashlib.sha256(data).hexdigest(),
            "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream"}

def fail(folder, message):
    raise ValueError(f"{folder.parent.name}/{folder.name}: {message}")

def read_metadata(folder: Path, name: str, required: tuple[str, ...]):
    path = folder / name
    if not path.exists(): fail(folder, f"missing {name}")
    if not (folder / "README.md").exists(): fail(folder, "missing README.md")
    metadata = json.loads(path.read_text())
    if any(not metadata.get(key) for key in required): fail(folder, f"{name} must contain {required}")
    return metadata

drivers = []
for folder in sorted(p for p in DRIVERS.iterdir() if p.is_dir()) if DRIVERS.exists() else []:
    metadata = read_metadata(folder, "driver.json", ("id", "name", "version", "description", "boardTags"))
    if metadata["id"] != folder.name: fail(folder, f"id must match the directory name")
    # test_*.py stays in the repository; only the modules themselves go to the board.
    files = [entry(p, folder) for p in sorted(folder.rglob("*.py")) if not p.name.startswith("test_")]
    if not files: fail(folder, "must contain at least one Python file")
    drivers.append({**metadata, "files": files,
                    "readme": {**entry(folder / "README.md", folder), "mime": "text/markdown"}})

driver_ids = {driver["id"] for driver in drivers}

examples, ids = [], set()
for folder in sorted(p for p in EXAMPLES.iterdir() if p.is_dir()):
    metadata = read_metadata(folder, "example.json", ("id", "title", "description", "boardTags", "entry"))
    if metadata["id"] in ids: fail(folder, f"duplicate id {metadata['id']}")
    ids.add(metadata["id"])
    if (folder / "lib").exists(): fail(folder, "drivers belong in drivers/, declare them in requires")
    entry_path = folder / metadata["entry"]
    if not entry_path.is_file() or entry_path.suffix != ".py": fail(folder, "entry must point to a Python file")
    requires = metadata.get("requires", [])
    if not isinstance(requires, list): fail(folder, "requires must be a list of driver ids")
    for driver_id in requires:
        if driver_id not in driver_ids: fail(folder, f"requires unknown driver {driver_id}")
    files = [entry(entry_path, folder)] + [entry(p, folder) for p in sorted(folder.glob("*.py")) if p != entry_path]
    assets = folder / "res"
    examples.append({"id": metadata["id"], "title": metadata["title"], "description": metadata["description"],
                     "boardTags": metadata["boardTags"], "requires": requires, "files": files,
                     "readme": {**entry(folder / "README.md", folder), "mime": "text/markdown"},
                     "assets": [entry(p, folder) for p in sorted(assets.rglob("*")) if p.is_file()] if assets.exists() else []})

# The driver table in drivers/README.md is generated so it cannot drift from driver.json.
rows = ["| Driver | Modules | Used by |", "| --- | --- | --- |"]
for driver in drivers:
    modules = ", ".join(f"`{file['path']}`" for file in driver["files"])
    used_by = ", ".join(f"[{e['id']}](../examples/{e['id']})" for e in examples if driver["id"] in e["requires"])
    rows.append(f"| [{driver['id']}]({driver['id']}) | {modules} | {used_by or '—'} |")
index = DRIVERS / "README.md"
head, _, rest = index.read_text().partition("<!-- generated:start -->")
_, _, tail = rest.partition("<!-- generated:end -->")
index.write_text(f"{head}<!-- generated:start -->\n" + "\n".join(rows) + f"\n<!-- generated:end -->{tail}")

manifest = {"schema": "pulsar.micropython.library/v1",
            "catalog": {"id": "micropython-examples", "name": "MicroPython Examples", "version": VERSION},
            "examples": examples, "drivers": drivers}
(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Generated {len(examples)} examples and {len(drivers)} drivers")
