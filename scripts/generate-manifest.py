#!/usr/bin/env python3
"""Generate the Pulsar IoT MicroPython library manifest from example folders."""
from pathlib import Path
import hashlib, json, re, subprocess

ROOT = Path(__file__).resolve().parents[1]
COMMIT = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
BASE = f"https://raw.githubusercontent.com/StevenSlaa/Micropython-examples/{COMMIT}"

def file_entry(path, folder):
    data = path.read_bytes()
    rel = path.relative_to(ROOT).as_posix().replace(" ", "%20")
    return {"path": path.relative_to(folder).as_posix(), "url": f"{BASE}/{rel}",
            "sha256": hashlib.sha256(data).hexdigest(),
            "mime": "text/x-python" if path.suffix == ".py" else "text/plain"}

examples = []
for folder in sorted(p for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")):
    readme, scripts = folder / "README.md", sorted(folder.glob("*.py"))
    if not readme.exists() or not scripts: continue
    markdown = readme.read_text(errors="replace")
    title = next((line[2:].strip() for line in markdown.splitlines() if line.startswith("# ")), folder.name)
    paragraphs = [p.strip().replace("\n", " ") for p in re.split(r"\n\s*\n", markdown)
                  if p.strip() and not p.lstrip().startswith(("#", "!", "<", "```", "-", ">"))]
    tested = re.search(r"## Tested(.*?)(?:\n## |\Z)", markdown, re.S | re.I)
    tags = {"esp32" if "ESP32" in line.upper() else "pico" if "PICO" in line.upper() else None
            for line in (tested.group(1).splitlines() if tested else [])}
    files = scripts + ([*sorted((folder / "lib").glob("*"))] if (folder / "lib").exists() else [])
    examples.append({"id": re.sub(r"[^a-z0-9]+", "-", folder.name.lower()).strip("-"),
        "title": title, "description": (paragraphs[0] if paragraphs else f"MicroPython example for {title}.")[:240],
        "boardTags": sorted(t for t in tags if t) or ["esp32"],
        "files": [file_entry(p, folder) for p in files if p.is_file()],
        "readme": file_entry(readme, folder) | {"mime": "text/markdown"}})

manifest = {"schema": "pulsar.micropython.library/v1",
            "catalog": {"id": "micropython-examples", "name": "MicroPython Examples", "version": COMMIT[:12]},
            "examples": examples, "drivers": []}
(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
