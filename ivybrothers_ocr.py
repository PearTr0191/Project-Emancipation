"""ivybrothers_ocr.py — Bulk OCR pass over downloaded slide images.

For each code dir in ivybrothers_assets/, OCR all slide_NN.jpg files and
insert a '## Slide text' section into mentor/transcripts/<code>.md (between
## Slides and ## Page meta). Resumable: the section-presence check IS the
resume mechanism. Run after/concurrent with ivybrothers_pipeline.py.

OCR quality gate (2026-09-21): 5-sample test passed — tesseract 5.4.0 reads
Ivy Brothers' text-on-image slides accurately (minor quote-encoding artifacts).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except (AttributeError, OSError):
    pass

ROOT = Path(r"D:\Project Emancipation")
TRANSCRIPTS_DIR = ROOT / "mentor" / "transcripts"
ASSETS_DIR = ROOT / "ivybrothers_assets"

TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
MAX_SLIDE_CHARS = 1200
PROGRESS_EVERY = 25

SLIDE_NUM_RE = re.compile(r"^slide_(\d+)\.jpg$")


def ocr_image(img_path: Path) -> str:
    import pytesseract
    from PIL import Image

    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    txt = pytesseract.image_to_string(Image.open(img_path))
    clean = " ".join(txt.split())
    return clean[:MAX_SLIDE_CHARS]


def slide_text_section(code: str) -> str | None:
    code_dir = ASSETS_DIR / code
    if not code_dir.exists():
        return None
    slides = []
    for p in code_dir.glob("slide_*.jpg"):
        m = SLIDE_NUM_RE.match(p.name)
        if m:
            slides.append((int(m.group(1)), p))
    if not slides:
        return None
    lines = []
    for num, p in sorted(slides):
        try:
            text = ocr_image(p)
        except Exception as exc:
            text = f"(OCR failed: {type(exc).__name__})"
        label = f"slide_{num:02d}" if text.startswith("(OCR failed") else f"slide_{num:02d}"
        lines.append(f"- {label}: {text}" if text else f"- {label}: (empty)")
    return "## Slide text\n\n" + "\n".join(lines) + "\n\n"


def needs_ocr(md_path: Path) -> bool:
    body = md_path.read_text(encoding="utf-8", errors="replace")
    if "## Slide text" in body:
        return False
    if "## Slides" not in body:
        return False
    return "(none captured)" not in body.split("## Slide text")[0].split("## Slides")[1][:400]


def insert_section(body: str, section: str) -> str:
    marker = "## Page meta"
    if marker in body:
        return body.replace(marker, section + marker, 1)
    return body.rstrip() + "\n\n" + section


def main() -> int:
    import pytesseract  # noqa: F401 — fail fast if missing

    if not TRANSCRIPTS_DIR.exists():
        sys.exit(f"missing {TRANSCRIPTS_DIR}")
    codes: list[str] = []
    for p in TRANSCRIPTS_DIR.glob("*.md"):
        head = p.read_text(encoding="utf-8", errors="replace")[:300]
        m = re.search(r"^code:\s*(\S+)\s*$", head, re.MULTILINE)
        if m and (ASSETS_DIR / m.group(1)).exists():
            codes.append((p, m.group(1)))
    todo = [(p, c) for p, c in codes if needs_ocr(p)]
    print(f"[ocr] transcripts_with_assets={len(codes)} todo={len(todo)}", flush=True)

    done = 0
    started = time.time()
    for i, (md_path, code) in enumerate(todo, 1):
        try:
            section = slide_text_section(code)
            if section:
                body = md_path.read_text(encoding="utf-8", errors="replace")
                md_path.write_text(insert_section(body, section), encoding="utf-8")
                done += 1
        except Exception as exc:
            print(f"[ocr] FAILED {code}: {type(exc).__name__}: {str(exc)[:150]}", flush=True)
        if i % PROGRESS_EVERY == 0:
            rate = i / max(time.time() - started, 1)
            print(f"[ocr] {i}/{len(todo)} done={done} rate={rate:.1f}/s", flush=True)
    print(f"[ocr] finished processed={done}/{len(todo)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
