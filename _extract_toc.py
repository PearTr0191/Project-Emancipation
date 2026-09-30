"""Extract the 50 essay names from the OCR'd table of contents. Read-only."""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parent / "winning-essays.md"
lines: list[str] = SRC.read_text(encoding="utf-8").split("\n")

RUNNING_HEADERS = {
    "Contents", "Introduction", "Identity", "Introspection",
    "Overcoming Obstacles", "Foreign Life", "Passion", "Inspiration",
    "Experiences", "Acknowledgments",
}
SECTION_RE = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII)\.")
PAGENUM = re.compile(r"^\d{1,3}$|^[ivxlcdm]{1,7}$|^[IVXLCDM]{1,7}$")

# The contents block runs from "CONTENTS" to the ACKNOWLEDGMENTS heading.
end = next(i for i, l in enumerate(lines) if l.strip() == "ACKNOWLEDGMENTS")

names: list[str] = []
for raw in lines[:end]:
    text = raw.replace("\u00ac", "").strip()
    if not text:
        continue
    if PAGENUM.match(text) or SECTION_RE.match(text) or text in RUNNING_HEADERS:
        continue
    names.append(text)

print(f"extracted {len(names)} names:\n")
for i, n in enumerate(names, 1):
    print(f"{i:2d}. {n}")

# Cross-check against the names that appear as recto running headers in the body.
body = lines[end:]
body_names: dict[str, int] = {}
for i, raw in enumerate(body):
    t = raw.replace("\u00ac", "").strip()
    if PAGENUM.match(raw.replace("\u00ac", "").strip()):
        nxt = body[i + 1].replace("\u00ac", "").strip() if i + 1 < len(body) else ""
        if nxt and 0 < len(nxt) <= 34 and nxt not in RUNNING_HEADERS:
            body_names[nxt] = body_names.get(nxt, 0) + 1

print(f"\nbody header strings ({len(body_names)}):")
for n, c in sorted(body_names.items()):
    match = any(
        n.lower().replace(".", "").replace(" ", "") == b.lower().replace(".", "").replace(" ", "")
        for b in names
    )
    flag = "" if match else "   <-- NO TOC MATCH"
    print(f"  {c}x  {n}{flag}")
