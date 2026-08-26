"""One-time cleanup: strip repeated boilerplate from transcript markdowns."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPTS = ROOT / "mentor" / "transcripts"

BLOCK_MARKERS = [
    "mother passed away",
    "aboutgrades",
    "about grades",
    "dreamedofgettingintoanivyleagueschoolbutdidn",
    "acceptedintoharvard",
    "firstdayofsenior",
    "tasharvard",
    "uilgiielise",
    "inhighschool",
    "uilgilana",
    "extracurricularsforyourmajorherearesomeideas",
    "metyou",
    "swipe",
    "thetruthfailed",
    "beforefromcancer",
    "@ultimateivyleagueguide",
    "elise pham\n@ultimateivyleagueguide",
    "isnatalie",
    "uilgielise",
    "uilgilrene",
]

LYRIC_JUNK_PREFIXES = [
    "hey ladies drop it down",
]


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def is_junk_block(block: str) -> bool:
    n = norm(block)
    if len(n) < 10:
        return True
    return any(m.replace(" ", "") in n for m in BLOCK_MARKERS)


def clean_slides(raw_slides: str) -> str | None:
    blocks = [b.strip() for b in raw_slides.split("\n---\n")]
    kept: list[str] = []
    seen: set[str] = set()
    for b in blocks:
        lines = [ln.rstrip() for ln in b.splitlines()]
        cleaned_lines = [ln for ln in lines if norm(ln) and "@ultimateivyleagueguide" not in ln.lower() and norm(ln) != "elisepham"]
        clean = "\n".join(cleaned_lines).strip()
        if not clean or is_junk_block(clean):
            continue
        key = norm(clean)[:90]
        if key in seen:
            continue
        seen.add(key)
        kept.append(clean)
    return "\n\n---\n\n".join(kept) if kept else None


def main() -> None:
    total_before = total_after = 0
    touched = stripped_transcript = stripped_slides = dropped_files = 0
    for p in sorted(TRANSCRIPTS.glob("*.md")):
        raw = p.read_text(encoding="utf-8")
        total_before += len(raw)
        fm_m = re.match(r"(---\n.*?\n---\n)", raw, re.S)
        fm = fm_m.group(1) if fm_m else ""
        body = raw[len(fm):]

        cap_m = re.search(r"## Caption\n\n(.*?)(?=\n## |\Z)", body, re.S)
        caption = cap_m.group(1).strip() if cap_m else ""
        tr_m = re.search(r"## Transcript\n\n(.*?)(?=\n## |\Z)", body, re.S)
        transcript = tr_m.group(1).strip() if tr_m else ""
        sl_m = re.search(r"## Slides \(OCR\)\n\n(.*?)\Z", body, re.S)
        slides_raw = sl_m.group(1).strip() if sl_m else ""

        words = transcript.split()
        if transcript and (len(words) < 8 or any(transcript.lower().startswith(p) for p in LYRIC_JUNK_PREFIXES)):
            transcript = ""
            stripped_transcript += 1

        slides = clean_slides(slides_raw)
        if slides_raw and not slides:
            stripped_slides += 1

        parts = []
        if caption:
            parts.append("## Caption\n\n" + caption)
        if transcript:
            parts.append("## Transcript\n\n" + transcript)
        if slides:
            parts.append("## Slides (OCR)\n\n" + slides)

        if not parts:
            p.unlink()
            dropped_files += 1
            continue

        out = fm + "\n" + "\n\n".join(parts) + "\n"
        if len(out) != len(raw):
            touched += 1
        total_after += len(out)
        p.write_text(out, encoding="utf-8")
    print(f"files={len(list(TRANSCRIPTS.glob('*.md')))} dropped={dropped_files} touched={touched}")
    print(f"junk transcripts removed={stripped_transcript} empty slide-sections removed={stripped_slides}")
    print(f"size {total_before:,} -> {total_after:,} chars ({100 * (1 - total_after / max(total_before, 1)):.0f}% smaller)")


if __name__ == "__main__":
    main()
