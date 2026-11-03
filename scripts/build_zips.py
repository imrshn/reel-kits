#!/usr/bin/env python3
"""Zip every kit in kits/<name>/ into dist/<zip_name>, inside a top folder named by kit.json."""
import json
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".venv", "node_modules", "__pycache__", ".work"}
SKIP_FILES = {"kit.json", ".DS_Store"}


def build(kit_dir: Path, dist: Path) -> Path:
    meta = json.loads((kit_dir / "kit.json").read_text())
    out = dist / meta["zip_name"]
    top = meta["zip_folder"]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(kit_dir):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for f in sorted(files):
                if f in SKIP_FILES:
                    continue
                p = Path(root) / f
                rel = p.relative_to(kit_dir)
                info = zipfile.ZipInfo(f"{top}/{rel.as_posix()}", date_time=(2026, 1, 1, 0, 0, 0))
                info.external_attr = (0o755 if p.suffix == ".py" else 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, p.read_bytes())
    return out


def main() -> None:
    names = sys.argv[1:] or sorted(d.name for d in (ROOT / "kits").iterdir() if (d / "kit.json").exists())
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    for n in names:
        out = build(ROOT / "kits" / n, dist)
        print(f"{n}\t{out}")


if __name__ == "__main__":
    main()
