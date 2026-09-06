#!/usr/bin/env python3
"""Validate examples and drivers, and generate the immutable Pulsar IoT catalog."""
from pathlib import Path
import hashlib, json, mimetypes, os

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
DRIVERS = ROOT / "drivers"
VERSION = os.environ.get("CATALOG_VERSION", "1.0.0")
BASE = "https://raw.githubusercontent.com/StevenSlaa/Micropython-examples/refs/heads/main"

# Examples are listed in this order, in the manifest and so in the IDE's library panel, where
# each group is a heading with this line under it. A group that is not on this list still works:
# it simply goes at the end, in alphabetical order, without a description.
GROUPS = (
    ("Basics", "Five short examples, in order. Start here if you have not used a microcontroller before."),
    ("Sensors", "Reading the world: temperature, distance, movement, light and magnetic fields."),
    ("Displays and LEDs", "Showing something, from a character display to a matrix or a strip of colour."),
    ("Motion", "Making something move, with motors and servos."),
    ("Input", "Taking something in from a person: knobs, keypads and card readers."),
    ("Remote control", "Talking over infrared, in both directions."),
    ("Between boards", "Getting two boards to talk to each other, by radio or down a wire."),
    ("Networking", "Wifi, access points, name lookups and MQTT. Needs a board with a radio: an ESP32 or a Pico W."),
    ("Storage and time", "Remembering things after the power goes, and knowing what time it is."),
    ("Tools", "Finding out what is really on the bus."),
)
GROUP_ORDER = [name for name, _ in GROUPS]
GROUP_DESCRIPTIONS = dict(GROUPS)

def entry(path: Path, relative_to: Path):
    data = path.read_bytes()
    relative = path.relative_to(ROOT).as_posix().replace(" ", "%20")
    return {"path": path.relative_to(relative_to).as_posix(), "url": f"{BASE}/{relative}",
            "sha256": hashlib.sha256(data).hexdigest(),
            "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream"}

def write_front_matter(readme: Path, fields: dict):
    """Puts the author at the top of a README, as YAML front matter.

    Written from example.json and driver.json rather than by hand, so the two always agree.
    GitHub renders it as a table; the IDE hides it and shows the author on the card instead.
    """
    text = readme.read_text()
    if text.startswith("---\n"):
        _, _, text = text[4:].partition("---\n")
        text = text.lstrip("\n")
    lines = "\n".join(f"{key}: {value}" for key, value in fields.items() if value)
    readme.write_text(f"---\n{lines}\n---\n\n{text}")


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
    write_front_matter(folder / "README.md", {"driver": metadata["id"], "author": metadata.get("author")})
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
    group = metadata.get("group", "Other")
    # Within a group, examples are listed by this and then by id. Only a set meant to be read
    # in sequence needs it; everything else leaves it out and lands in alphabetical order.
    order = metadata.get("order", 0)
    if not isinstance(order, int): fail(folder, "order must be a whole number")
    requires = metadata.get("requires", [])
    if not isinstance(requires, list): fail(folder, "requires must be a list of driver ids")
    for driver_id in requires:
        if driver_id not in driver_ids: fail(folder, f"requires unknown driver {driver_id}")
    files = [entry(entry_path, folder)] + [entry(p, folder) for p in sorted(folder.glob("*.py")) if p != entry_path]
    write_front_matter(folder / "README.md", {"example": metadata["id"], "author": metadata.get("author")})
    assets = folder / "res"
    examples.append({"id": metadata["id"], "title": metadata["title"], "description": metadata["description"],
                     "boardTags": metadata["boardTags"], "author": metadata.get("author", ""),
                     "group": group, "order": order, "requires": requires, "files": files,
                     "readme": {**entry(folder / "README.md", folder), "mime": "text/markdown"},
                     "assets": [entry(p, folder) for p in sorted(assets.rglob("*")) if p.is_file()] if assets.exists() else []})

examples.sort(key=lambda example: (
    GROUP_ORDER.index(example["group"]) if example["group"] in GROUP_ORDER else len(GROUP_ORDER),
    example["group"],
    example["order"],
    example["id"],
))
# The order was only ever about sorting; the manifest is already sorted, so it does not travel.
for example in examples:
    del example["order"]
unlisted = sorted({e["group"] for e in examples if e["group"] not in GROUP_ORDER})
if unlisted:
    print(f"Note: groups not in GROUPS, listed last: {', '.join(unlisted)}")

# The example index in examples/README.md is generated, so it cannot drift from the metadata.
rows = []
for example in examples:
    if not rows or rows[-1][0] != example["group"]:
        rows.append((example["group"], []))
    needs = ", ".join(f"[{d}](../drivers/{d})" for d in example["requires"]) or "\u2014"
    summary = example["description"].split(". ")[0].rstrip(".")
    rows[-1][1].append(f"| [{example['title']}]({example['id']}) | {summary}. | {needs} |")
index = EXAMPLES / "README.md"
head, _, rest = index.read_text().partition("<!-- generated:start -->")
_, _, tail = rest.partition("<!-- generated:end -->")
sections = "\n\n".join(
    f"### {group}\n\n"
    + (f"{GROUP_DESCRIPTIONS[group]}\n\n" if group in GROUP_DESCRIPTIONS else "")
    + "| Example | What it does | Needs |\n| --- | --- | --- |\n"
    + "\n".join(lines)
    for group, lines in rows
)
index.write_text(f"{head}<!-- generated:start -->\n{sections}\n<!-- generated:end -->{tail}")

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

# Only the groups that have something in them, in the order the examples are already in.
group_names = []
for example in examples:
    if example["group"] not in group_names:
        group_names.append(example["group"])
groups = [{"name": name, **({"description": GROUP_DESCRIPTIONS[name]} if name in GROUP_DESCRIPTIONS else {})}
          for name in group_names]

manifest = {"schema": "pulsar.micropython.library/v1",
            "catalog": {"id": "micropython-examples", "name": "MicroPython Examples", "version": VERSION},
            "groups": groups, "examples": examples, "drivers": drivers}
(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Generated {len(examples)} examples and {len(drivers)} drivers")
