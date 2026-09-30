"""Analyze line-wrap geometry so paragraphs can be rebuilt. Read-only."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

SRC = Path(__file__).resolve().parent / "winning-essays.md"
lines: list[str] = SRC.read_text(encoding="utf-8").split("\n")

# Body region only: skip front matter (1-138) which is a TOC.
body = lines[138:]

print("=" * 70)
print("LINE LENGTH HISTOGRAM (body, 139+)")
lens = [len(ln) for ln in body if ln.strip()]
hist = Counter(lens)
for n in sorted(hist):
    bar = "#" * min(hist[n], 60)
    print(f"{n:3d} | {bar} {hist[n]}")

print("=" * 70)
print("CUMULATIVE: what fraction of lines are <= N chars")
for cap in (40, 45, 48, 50, 52, 54, 56, 58, 60, 62):
    c = sum(1 for L in lens if L <= cap)
    print(f"  <= {cap:2d}: {c:5d} / {len(lens)}  ({100*c/len(lens):.1f}%)")

print("=" * 70)
print("SAMPLE: candidate paragraph-final lines (short + terminal punct)")
print("vs candidate mid-paragraph line ends at the same length band.\n")
short_term = [ln for ln in body if 20 <= len(ln.strip()) <= 52
              and re.search(r"[.!?][\"'\u2019\u201d]?$", ln.strip())]
print(f"short+terminal-punct count = {len(short_term)}")
for ln in short_term[:15]:
    print(f"   [{len(ln.strip()):2d}] {ln.strip()[:80]}")

print("\nshort but NO terminal punct (likely mid-paragraph wraps):")
short_noterm = [ln for ln in body if 30 <= len(ln.strip()) <= 52
                and not re.search(r"[.!?][\"'\u2019\u201d]?$", ln.strip())]
for ln in short_noterm[:15]:
    print(f"   [{len(ln.strip()):2d}] {ln.strip()[:80]}")

print("=" * 70)
print("TWO-LINE HEADERS? lines matching roman-numeral section pattern")
for i, ln in enumerate(body):
    s = ln.strip()
    if re.match(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)\.\s*[A-Z]", s) and len(s) < 30:
        print(f"  L{139+i}: [{len(s):2d}] {s!r}  next: {body[i+1].strip()[:50]!r}")
