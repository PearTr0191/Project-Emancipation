"""Digest for the recent-cycle batch (posts NOT in original manifest)."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRANSCRIPTS = ROOT / "mentor" / "transcripts"

BOILERPLATE_MARKERS = [
    "mother passed away", "the truth", "aboutgrades", "about grades",
    "dreamed of getting into an lvy", "accepted into harvard",
    "first day of senior", "beagile", "swipe", "uilg ie", "inhigh school",
    "elise pham", "@ultimateivyleagueguide",
]


def is_noise(line: str) -> bool:
    low = line.strip().lower()
    if not low or len(low) < 3:
        return True
    return any(m in low for m in BOILERPLATE_MARKERS)


def main() -> None:
    cands = json.loads((ROOT / "new_candidates.json").read_text(encoding="utf-8"))
    parts: list[str] = []
    for it in sorted(cands["items"], key=lambda x: x["taken_at"], reverse=True):
        code = it["code"]
        p = TRANSCRIPTS / f"{code}.md"
        if not p.exists():
            continue
        raw = p.read_text(encoding="utf-8")
        section = [f"### {code} ({it['date']}) {it['product_type']} novelty={','.join(it.get('novelty', [])) or '-'}"]
        cap_m = re.search(r"## Caption\n\n(.*?)(?=\n## |\Z)", raw, re.S)
        if cap_m:
            section.append("[CAPTION]\n" + cap_m.group(1).strip())
        tr_m = re.search(r"## Transcript\n\n(.*?)(?=\n## |\Z)", raw, re.S)
        if tr_m:
            t = tr_m.group(1).strip()
            if len(t.split()) >= 25:
                section.append("[SPEECH]\n" + t)
        sl_m = re.search(r"## Slides \(OCR\)\n\n(.*?)\Z", raw, re.S)
        if sl_m:
            blocks = [b.strip() for b in sl_m.group(1).split("---")]
            uniq: list[str] = []
            seen: set[str] = set()
            for b in blocks:
                lines = [ln for ln in b.splitlines() if not is_noise(ln)]
                clean = "\n".join(lines).strip()
                if len(clean) < 12:
                    continue
                norm = re.sub(r"[^a-z0-9]", "", clean.lower())[:80]
                if norm in seen:
                    continue
                seen.add(norm)
                uniq.append(clean)
            if uniq:
                section.append("[SLIDES]\n" + "\n---\n".join(uniq[:10]))
        parts.append("\n".join(section))
    out = ROOT / "mentor" / "distill_digest_batch2.txt"
    text = "\n\n=====\n\n".join(parts)
    out.write_text(text, encoding="utf-8")
    print("digest chars:", len(text), "| posts:", len(parts))


if __name__ == "__main__":
    main()
