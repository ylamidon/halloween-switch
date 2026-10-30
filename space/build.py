"""Assembles the folder to push to the Hugging Face Space: python space/build.py [dest] (default: .tmp/space)."""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
dest = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".tmp" / "space"

for name in ("app.py", "LICENSE", "THIRD_PARTY_NOTICES.md"):
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / name, dest / name)
for name in ("pipeline", "workflows"):
    shutil.rmtree(dest / name, ignore_errors=True)
    shutil.copytree(ROOT / name, dest / name, ignore=shutil.ignore_patterns("__pycache__"))
for f in (ROOT / "space").glob("*.txt"):
    shutil.copy2(f, dest / f.name)
shutil.copy2(ROOT / "space" / "README.md", dest / "README.md")
print(dest)
