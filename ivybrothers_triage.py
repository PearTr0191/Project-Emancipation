"""ivybrothers_triage.py — Theme-classify all Ivy Brothers transcripts.

Reads:  mentor/transcripts/*.md (handle: ivybrothersofficial)
Writes: manifest_ivybrothers.json  (all items + themes + coverage, manifest schema)
        prioritized_read.json      (ranked shortlist per theme for the curated pass)

Does NOT append to knowledge/ files — the 2026-08-31 cleanup established that
KB files hold only curated signal; the curated distillation pass reads
prioritized_read.json and synthesizes by hand.

Run AFTER ivybrothers_pipeline.py --phase extract and ivybrothers_ocr.py.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except (AttributeError, OSError):
    pass

ROOT = Path(r"D:\Project Emancipation")
TRANSCRIPTS_DIR = ROOT / "mentor" / "transcripts"
MANIFEST_PATH = ROOT / "manifest_ivybrothers.json"
PRIORITIZED_PATH = ROOT / "prioritized_read.json"
HANDLE = "ivybrothersofficial"

# Same rubric as distill_loop.py (2026-08-31 run), extended with Ivy-Brothers-
# specific phrasing: this account's format is school-specific slide series
# ("X Backdoor Revealed", "What X Is Really Looking For", legacy/donation posts).
THEME_KEYWORDS: dict[str, list[tuple[str, int]]] = {
    "essays": [
        ("personal statement", 4), ("common app essay", 4), ("supplemental essay", 4),
        ("essay hook", 4), ("why us", 3), ("college essay", 3), ("essay prompt", 3),
        ("essay", 2), ("additional info", 2), ("commonapp", 1), ("activity essay", 2),
    ],
    "activities": [
        ("activities list", 5), ("extracurricular", 3), ("passion project", 4),
        ("tier 1", 3), ("tier 2", 3), ("three tiers", 3), ("summer program", 2),
        ("internship", 2), ("nonprofit", 2), ("leadership role", 2),
        ("club president", 2), ("spike", 3), ("award", 2), ("national award", 3),
    ],
    "timeline": [
        ("november 1", 4), ("nov 1", 4), ("deadline", 3), ("early decision", 3),
        ("early action", 3), ("regular decision", 3), ("ea deadline", 3),
        ("ed deadline", 3), ("application deadline", 3), ("checklist", 2),
        ("rising senior", 3), ("rising junior", 3), ("junior year", 2),
        ("senior year", 2), ("sophomore", 2), ("freshman", 2), ("summer before", 2),
        ("january", 2), ("deferral", 3), ("waitlist", 3),
    ],
    "school_list": [
        ("school list", 5), ("college list", 4), ("dream school", 3),
        ("safety school", 3), ("target school", 3), ("reach school", 3),
        ("common data set", 3), ("net price calculator", 3), ("backdoor", 4),
        ("really looking for", 4), ("legacy", 3), ("donat", 2), ("get into", 2),
        ("feeder", 3), ("harvard", 2), ("stanford", 2), ("yale", 2), ("princeton", 2),
        ("mit", 2), ("upenn", 2), ("penn", 2), ("columbia", 2), ("brown", 2),
        ("dartmouth", 2), ("cornell", 2), ("northwestern", 2), ("duke", 2),
        ("johns hopkins", 2), ("jhu", 2), ("georgia tech", 2), ("nyu", 2),
        ("usc", 2), ("ucla", 2), ("michigan", 2), ("notre dame", 2),
        ("vanderbilt", 2), ("rice", 2), ("berkeley", 2), ("georgetown", 2),
        ("uva", 2), ("unc", 2), ("ivy league", 2), ("ivy", 1),
    ],
    "interviews": [
        ("interview", 4), ("tell me about yourself", 4), ("greatest weakness", 4),
        ("alumni interview", 3), ("interview prep", 3), ("interview question", 3),
        ("mock interview", 2),
    ],
    "testing": [
        ("sat", 3), ("dsat", 3), ("digital sat", 3), ("act", 2), ("toefl", 2),
        ("ielts", 2), ("test prep", 2), ("test optional", 3), ("ap score", 2),
        ("ap exam", 2), ("superscore", 3), ("score choice", 3),
    ],
    "recommendations": [
        ("letter of recommendation", 4), ("recommendation letter", 4),
        ("teacher rec", 3), ("counselor rec", 3), ("brag sheet", 3),
        ("letter writer", 2), ("lor", 3), ("rec letter", 3), ("recommender", 3),
    ],
    "myths_mindset": [
        ("myth", 3), ("lie", 2), ("common mistake", 3), ("stop doing", 3),
        ("won't say", 3), ("wont say", 3), ("trap", 3), ("rejected", 2),
        ("imposter", 2), ("burnout", 2), ("truth", 2), ("mistake", 2),
    ],
    "study_skills": [
        ("study", 3), ("studying", 3), ("focus", 2), ("productivity", 3),
        ("flashcard", 2), ("note-taking", 2), ("memorize", 2), ("gpa", 3),
        ("finals", 2), ("exam", 2), ("grade", 2),
    ],
}

THEME_NAMES = list(THEME_KEYWORDS.keys())


def parse_transcript(path: Path) -> dict | None:
    """Return {code, date, kind, caption, slide_text, slide_count, likes} or None.

    Filters on the `handle: ivybrothersofficial` front-matter line — without it
    the folder's ~1045 UILG-era transcripts get swept in (first run bug:
    items=1489 instead of 444, coverage dominated by UILG).
    """
    txt = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^code:\s*(\S+)\s*$", txt, re.MULTILINE)
    if not m:
        return None
    hm = re.search(r"^handle:\s*(\S+)\s*$", txt, re.MULTILINE)
    if not hm or hm.group(1) != HANDLE:
        return None
    code = m.group(1)
    dm = re.search(r"^date:\s*(\S+)\s*$", txt, re.MULTILINE)
    date = dm.group(1) if dm else None
    sm = re.search(r"\*Source: ivybrothersofficial (p|reel) ", txt)
    kind = sm.group(1) if sm else "p"
    cap_m = re.search(r"## Caption\s*\n(.*?)(?=\n## |\Z)", txt, re.DOTALL)
    caption = cap_m.group(1).strip() if cap_m else ""
    slide_m = re.search(r"## Slide text\s*\n(.*?)(?=\n## |\Z)", txt, re.DOTALL)
    slide_text = slide_m.group(1).strip() if slide_m else ""
    slide_count = len(re.findall(r"- ivybrothers_assets/", txt))
    likes_m = re.search(r"^([\d,]+) likes", caption, re.MULTILINE)
    likes = int(likes_m.group(1).replace(",", "")) if likes_m else None
    return {
        "code": code, "date": date, "kind": kind, "caption": caption,
        "slide_text": slide_text, "slide_count": slide_count, "likes": likes,
    }


def classify(text: str) -> list[str]:
    """Ranked theme list (score >= 3, top 4). cross_cutting is fallback only."""
    text_low = text.lower()
    scores: Counter = Counter()
    for theme, kws in THEME_KEYWORDS.items():
        for kw, weight in kws:
            if kw in text_low:
                scores[theme] += weight
    ranked = [(t, s) for t, s in scores.items() if s >= 3]
    ranked.sort(key=lambda x: x[1], reverse=True)
    real = [t for t, _ in ranked if t != "cross_cutting"]
    return real[:4] if real else ["cross_cutting"]


def main() -> int:
    if not TRANSCRIPTS_DIR.exists():
        sys.exit(f"missing {TRANSCRIPTS_DIR}")
    items: list[dict] = []
    for p in TRANSCRIPTS_DIR.glob("*.md"):
        parsed = parse_transcript(p)
        if not parsed:
            continue
        text = parsed["caption"] + "\n" + parsed["slide_text"]
        themes = classify(text)
        cap = parsed["caption"]
        # Strip engagement preamble from the preview; keep the caption body
        prev = re.sub(r"^[\d,]+ likes, [\d,]+ comments? - ivybrothersofficial on [^:]+:\s*", "", cap)
        prev = prev.replace("\n", " ").strip()[:280]
        items.append({
            "code": parsed["code"],
            "date": parsed["date"],
            "kind": parsed["kind"],
            "themes": themes,
            "like_count": parsed["likes"],
            "slide_count": parsed["slide_count"],
            "caption_preview": prev,
            "has_slide_text": bool(parsed["slide_text"]),
        })

    coverage: Counter = Counter()
    for it in items:
        for t in it["themes"]:
            coverage[t] += 1

    manifest = {
        "username": "ivybrothersofficial",
        "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pool_size": len(items),
        "theme_coverage": dict(coverage),
        "items": items,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    # Ranked shortlist per theme for the curated pass: signal density = theme
    # score + slide-text presence bonus; recency as tiebreaker.
    prio: dict[str, list[dict]] = {t: [] for t in THEME_NAMES}
    for it in items:
        for t in it["themes"]:
            if t == "cross_cutting":
                continue
            bonus = 2 if it["has_slide_text"] else 0
            prio[t].append({**it, "priority": it["slide_count"] + bonus})
    for t in prio:
        prio[t].sort(key=lambda x: (x["priority"], x["date"] or ""), reverse=True)
        prio[t] = prio[t][:14]
    PRIORITIZED_PATH.write_text(json.dumps(prio, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[triage] items={len(items)} coverage={dict(coverage)}", flush=True)
    print(f"[triage] shortlists: {', '.join(f'{t}={len(v)}' for t, v in prio.items())}", flush=True)
    print(f"[saved] {MANIFEST_PATH}", flush=True)
    print(f"[saved] {PRIORITIZED_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
