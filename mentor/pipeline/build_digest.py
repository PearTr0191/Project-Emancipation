"""Build a compact distillation digest: captions + unique OCR lines + real speech."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPTS = ROOT / "mentor" / "transcripts"

BOILERPLATE_MARKERS = [
    "mother passed away",
    "the truth",
    "aboutgrades",
    "about grades",
    "dreamed of getting into an lvy",
    "accepted into harvard",
    "first day of senior",
    "extracurriculars\nfor your major",
    "beagile",
    "swipe",
    "uilg ie",
    "inhigh school",
    "elise pham",
    "@ultimateivyleagueguide",
    "isnatalie",
]


def is_noise(line: str) -> bool:
    low = line.strip().lower()
    if not low:
        return True
    if len(low) < 3:
        return True
    for m in BOILERPLATE_MARKERS:
        if m in low:
            return True
    return False


def main() -> None:
    man = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    parts: list[str] = []
    for it in sorted(man["items"], key=lambda x: x["taken_at"], reverse=True):
        code = it["code"]
        p = TRANSCRIPTS / f"{code}.md"
        if not p.exists():
            continue
        raw = p.read_text(encoding="utf-8")
        date = it.get("taken_at")
        date_s = __import__("datetime").datetime.utcfromtimestamp(date).date().isoformat() if date else "?"
        section = [f"### {code} ({date_s}) themes={','.join(it.get('themes', []))}"]
        cap_m = re.search(r"## Caption\n\n(.*?)(?=\n## |\Z)", raw, re.S)
        if cap_m:
            section.append("[CAPTION]\n" + cap_m.group(1).strip())
        tr_m = re.search(r"## Transcript\n\n(.*?)(?=\n## |\Z)", raw, re.S)
        if tr_m:
            t = tr_m.group(1).strip()
            # drop obvious music lyrics / ultra-short
            words = t.split()
            if len(words) >= 25 and not t.lower().startswith("hey ladies"):
                section.append("[SPEECH]\n" + t)
        sl_m = re.search(r"## Slides \(OCR\)\n\n(.*?)\Z", raw, re.S)
        if sl_m:
            blocks = [b.strip() for b in sl_m.group(1).split("---")]
            uniq: list[str] = []
            seen_norm: set[str] = set()
            for b in blocks:
                lines = [ln for ln in b.splitlines() if not is_noise(ln)]
                clean = "\n".join(lines).strip()
                if len(clean) < 12:
                    continue
                norm = re.sub(r"[^a-z0-9]", "", clean.lower())[:80]
                if norm in seen_norm:
                    continue
                seen_norm.add(norm)
                uniq.append(clean)
            if uniq:
                section.append("[SLIDES]\n" + "\n---\n".join(uniq[:8]))
        parts.append("\n".join(section))
    out = ROOT / "mentor" / "distill_digest_batch1.txt"
    out.write_text("\n\n=====\n\n".join(parts), encoding="utf-8")
    print("digest chars:", len("\n\n=====\n\n".join(parts)), "| posts:", len(parts))


if __name__ == "__main__":
    main()
