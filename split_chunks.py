"""Split the phase-1 output into one chunk per book section for repair."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "winning-essays.phase1.md"
OUTDIR = ROOT / "chunks"

text = SRC.read_text(encoding="utf-8")
parts = re.split(r"(?m)^(## .*)$", text)

# parts = [preamble, heading, body, heading, body, ...]
sections: list[tuple[str, str]] = []
if parts[0].strip():
    sections.append(("preamble", parts[0]))
for i in range(1, len(parts), 2):
    sections.append((parts[i].strip(), parts[i + 1]))

OUTDIR.mkdir(exist_ok=True)
for old in OUTDIR.glob("chunk_*.md"):
    old.unlink()

manifest: list[tuple[str, str, int]] = []
for idx, (heading, body) in enumerate(sections, start=1):
    slug = re.sub(r"[^A-Za-z0-9]+", "_", heading).strip("_").lower() or "preamble"
    path = OUTDIR / f"chunk_{idx:02d}_{slug[:24]}.md"
    path.write_text(heading + body, encoding="utf-8")
    words = len((heading + body).split())
    manifest.append((path.name, heading, words))
    print(f"{path.name:38s} {words:6d} words   {heading}")

total = sum(w for _, _, w in manifest)
print(f"\nchunks: {len(manifest)}   total words: {total}")
