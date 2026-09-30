"""Assemble the repaired chunks into the final cleaned book."""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHUNKS = ROOT / "chunks"
TARGET = ROOT / "winning-essays.md"
BACKUP = ROOT / "winning-essays.original.md"

SOFT_HYPHEN = "\u00ac"
RUNNING_HEADERS = (
    "50 Successful Harvard Application Essays",
    "Contents",
    "ACKNOWLEDGMENTS",
    "Acknowledgments",
)


def collect() -> list[Path]:
    fixed = sorted(CHUNKS.glob("FIXED_chunk_*.md"))
    plain = sorted(CHUNKS.glob("chunk_*.md"))
    if len(fixed) != len(plain):
        missing = {p.name.replace("chunk_", "") for p in plain} - {
            p.name.replace("FIXED_chunk_", "") for p in fixed
        }
        print(f"ERROR: missing repaired chunks for: {sorted(missing)}", file=sys.stderr)
        raise SystemExit(1)
    return fixed


def main() -> int:
    parts = collect()
    print(f"assembling {len(parts)} chunks\n")

    text = "\n".join(p.read_text(encoding="utf-8") for p in parts)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text).rstrip() + "\n"

    if not BACKUP.exists():
        shutil.copy2(TARGET, BACKUP)
        print(f"backup written: {BACKUP.name}")

    # ---- validation -----------------------------------------------------
    failures: list[str] = []
    sections = re.findall(r"(?m)^## ", text)
    essays = re.findall(r"(?m)^### ", text)
    reviews = re.findall(r"(?m)^\*\*Review\*\*$", text)
    bylines = re.findall(r"(?m)^\*— ", text)

    if len(sections) != 8:
        failures.append(f"expected 8 sections, found {len(sections)}")
    if len(essays) != 50:
        failures.append(f"expected 50 essays, found {len(essays)}")
    if len(reviews) != 50:
        failures.append(f"expected 50 reviews, found {len(reviews)}")
    if len(bylines) != 52:
        failures.append(f"expected 52 attributions, found {len(bylines)}")
    if SOFT_HYPHEN in text:
        failures.append(f"{text.count(SOFT_HYPHEN)} soft-hyphen artifacts remain")
    for h in RUNNING_HEADERS:
        if re.search(rf"(?m)^{re.escape(h)}$", text):
            failures.append(f"running header remains: {h!r}")
    if re.search(r"(?m)^\d{1,3}$", text):
        failures.append("bare page-number lines remain")

    print("checks")
    print(f"  sections            {len(sections)}")
    print(f"  essays              {len(essays)}")
    print(f"  reviews             {len(reviews)}")
    print(f"  attributions        {len(bylines)}")
    print(f"  soft hyphens        {text.count(SOFT_HYPHEN)}")
    print(f"  running headers     {sum(1 for h in RUNNING_HEADERS if h in text)}")
    print(f"  words               {len(text.split())}")
    print(f"  lines               {text.count(chr(10))}")

    if failures:
        print("\nVALIDATION FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    TARGET.write_text(text, encoding="utf-8")
    print(f"\nOK - wrote {TARGET.name} ({len(text.split())} words)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
