#!/usr/bin/env python3
"""Validate examples and generate the immutable Pulsar IoT catalog."""
from pathlib import Path
import hashlib, json, mimetypes, os, re, sys

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
VERSION = os.environ.get("CATALOG_VERSION", "1.0.0")
BASE = "https://raw.githubusercontent.com/StevenSlaa/Micropython-examples/refs/heads/main"

def entry(path: Path):
    data = path.read_bytes()
    relative = path.relative_to(ROOT).as_posix().replace(" ", "%20")
    return {"path": path.relative_to(path.parents[1]).as_posix(), "url": f"{BASE}/{relative}",
            "sha256": hashlib.sha256(data).hexdigest(),
            "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream"}

def fail(folder, message):
    raise ValueError(f"{folder.name}: {message}")

result=[]; ids=set()
for folder in sorted(p for p in EXAMPLES.iterdir() if p.is_dir()):
    metadata_path, readme = folder / "example.json", folder / "README.md"
    if not metadata_path.exists(): fail(folder, "missing example.json")
    if not readme.exists(): fail(folder, "missing README.md")
    metadata=json.loads(metadata_path.read_text())
    required=("id", "title", "description", "boardTags", "entry")
    if any(not metadata.get(key) for key in required): fail(folder, f"metadata must contain {required}")
    if metadata["id"] in ids: fail(folder, f"duplicate id {metadata['id']}")
    ids.add(metadata["id"])
    entry_path=folder / metadata["entry"]
    if not entry_path.is_file() or entry_path.suffix != ".py": fail(folder, "entry must point to a Python file")
    files=[entry(entry_path)]
    lib=folder / "lib"
    if lib.exists(): files += [entry(p) for p in sorted(lib.rglob("*")) if p.is_file()]
    assets=folder / "res"
    asset_entries=[entry(p) for p in sorted(assets.rglob("*")) if p.is_file()] if assets.exists() else []
    result.append({**{key: metadata[key] for key in required[:-1]}, "files": files,
                   "readme": {**entry(readme), "path": "README.md", "mime": "text/markdown"},
                   "assets": asset_entries})
manifest={"schema":"pulsar.micropython.library/v1", "catalog":{"id":"micropython-examples", "name":"MicroPython Examples", "version":VERSION}, "examples":result, "drivers":[]}
(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Generated {len(result)} examples")
