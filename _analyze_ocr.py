"""Structural analysis of winning-essays.md OCR artifacts. Read-only."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

SRC = Path(__file__).resolve().parent / "winning-essays.md"
lines: list[str] = SRC.read_text(encoding="utf-8").split("\n")

PAGENUM = re.compile(r"^[\s]*(\d{1,3}|[ivxlcdmIVXLCDM]{1,7})[\s]*$")
NOT_SOFT = re.compile(r"\u00ac")  # the ¬ OCR soft-hyphen artifact

print("=" * 70)
print("1. BARE PAGE-NUMBER-LIKE LINES")
pagenums: list[int] = [i for i, ln in enumerate(lines) if PAGENUM.match(ln)]
print(f"count = {len(pagenums)}")
print("values:", " ".join(sorted({lines[i].strip() for i in pagenums})))

print("=" * 70)
print("2. LINE FOLLOWING A PAGE-NUMBER (candidate running headers)")
after: Counter[str] = Counter()
for i in pagenums:
    if i + 1 < len(lines):
        after[lines[i + 1].strip()] += 1
for txt, n in after.most_common():
    print(f"{n:4d}  {txt[:78]}")

print("=" * 70)
print("3. PAGE-NUMBER LINES NOT PRECEDED BY PROSE (decorative garbage blocks)")
for i in pagenums:
    prev = lines[i - 1].strip() if i else ""
    nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
    prev_is_pn = bool(PAGENUM.match(prev))
    if prev_is_pn or (not prev or PAGENUM.match(nxt)):
        print(f"  L{i+1}: prev=[{prev[:40]}] cur=[{lines[i].strip()}] next=[{nxt[:40]}]")

print("=" * 70)
print("4. SOFT-HYPHEN (¬) OCCURRENCES")
soft = [i for i, ln in enumerate(lines) if NOT_SOFT.search(ln)]
print(f"lines containing ¬ = {len(soft)}")
tail = [i for i in soft if NOT_SOFT.search(lines[i][NOT_SOFT.search(lines[i]).start() :])]
print(f"  ...ending with ¬ (line-wrap split) = {len(tail)}")
inline = [i for i in soft if i not in tail]
print(f"  ...¬ mid-line (not a wrap) = {len(inline)}")
for i in inline[:25]:
    print(f"    L{i+1}: {lines[i].strip()[:95]}")

print("=" * 70)
print("5. LINES ENDING IN REAL HYPHEN")
hy = [i for i, ln in enumerate(lines) if re.search(r"(\w)-\s*$", ln)]
print(f"count = {len(hy)}")
for i in hy[:30]:
    nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
    print(f"  L{i+1}: ...{lines[i].strip()[-42:]}  ||  next: {nxt[:38]}")

print("=" * 70)
print("6. NON-ASCII CHARACTER INVENTORY")
nonascii: Counter[str] = Counter()
for ln in lines:
    for ch in ln:
        if ord(ch) > 126:
            nonascii[ch] += 1
for ch, n in nonascii.most_common():
    print(f"  U+{ord(ch):04X} {ch!r} x{n}")

print("=" * 70)
print("7. EMPTY / WHITESPACE-ONLY LINES")
print(f"  truly empty = {sum(1 for ln in lines if ln == '')}")
print(f"  ws-only     = {sum(1 for ln in lines if ln.strip() == '' and ln != '')}")
print(f"  leading/trailing-space lines = {sum(1 for ln in lines if ln != ln.strip())}")
