"""Locate epigraph blocks and subtitle lines. Read-only."""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parent / "winning-essays.md"
lines: list[str] = SRC.read_text(encoding="utf-8").split("\n")
EM = "\u2014"

reviews = [i for i, l in enumerate(lines) if l.strip() == "REVIEW"]
bylines = [
    i
    for i, l in enumerate(lines)
    if l.strip().startswith(EM) and len(l.strip()) <= 45
]

print(f"REVIEW markers: {len(reviews)}")
print(f"em-dash short lines: {len(bylines)}")

print("\n--- em-dash lines NOT inside a review (epigraph attributions) ---")
for b in bylines:
    last_review = max((r for r in reviews if r < b), default=-1)
    if b - last_review > 60:
        ctx = " / ".join(l.strip()[:52] for l in lines[b - 3 : b + 2])
        print(f"L{b+1}: {lines[b].strip()}")
        print(f"      ctx: {ctx}")

print("\n--- em-dash lines INSIDE a review, count check ---")
inside = [b for b in bylines if b - max((r for r in reviews if r < b), default=-1) <= 60]
print(f"inside={len(inside)}  outside={len(bylines) - len(inside)}")

print("\n--- every em-dash line, in order, with review context ---")
for b in bylines:
    last_review = max((r for r in reviews if r < b), default=-1)
    tag = "REVIEW " if b - last_review <= 60 else "EPIGRAPH"
    print(f"{tag} L{b+1}: {lines[b].strip()!r}")
