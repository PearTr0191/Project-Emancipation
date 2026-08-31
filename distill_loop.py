"""distill_loop.py — Append UILG transcripts to the 9-theme knowledge base.

Reads:
  D:\\Project Emancipation\\mentor\\transcripts\\  (all *.md with `code: <X>` header)
  D:\\Project Emancipation\\pipeline_state.json    (codes added by this run)
  D:\\Project Emancipation\\mentor\\knowledge\\    (existing KB files)

Writes:
  D:\\Project Emancipation\\manifest_delta.json    (new manifest entries)
  Appends to each knowledge/<theme>.md as needed
  D:\\Project Emancipation\\mentor\\knowledge\\_distill_state.json (resumable)

Theme -> KB file mapping (preserves existing filenames):
  essays          -> common-app-essay.md
  timeline        -> timelines-deadlines.md
  activities      -> activities-list.md
  school_list     -> school-list-strategy.md
  interviews      -> interviews.md
  testing         -> recommendations-and-testing.md  (split: testing & recs co-located)
  recommendations -> recommendations-and-testing.md
  myths_mindset   -> myths-red-flags.md
  study_skills    -> career-major-strategy.md          (closest existing sink for now)
  cross-cutting   -> core-theme.md

To avoid duplicating work, the script reads `_distill_state.json` (created on
first run) and skips any code already in `distilled_codes`.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Project Emancipation")
TRANSCRIPTS_DIR = ROOT / "mentor" / "transcripts"
KB_DIR = ROOT / "mentor" / "knowledge"
STATE_PATH = ROOT / "pipeline_state.json"
DELTA_PATH = ROOT / "manifest_delta.json"
DISTILL_STATE_PATH = KB_DIR / "_distill_state.json"

# Map: theme -> KB file. Note: testing & recommendations co-located in
# recommendations-and-testing.md; study_skills shares with career-major-strategy
# because there's no dedicated file in the current knowledge/ directory.
THEME_TO_KB = {
    "essays": "common-app-essay.md",
    "timeline": "timelines-deadlines.md",
    "activities": "activities-list.md",
    "school_list": "school-list-strategy.md",
    "interviews": "interviews.md",
    "testing": "recommendations-and-testing.md",
    "recommendations": "recommendations-and-testing.md",
    "myths_mindset": "myths-red-flags.md",
    "study_skills": "career-major-strategy.md",
    "cross_cutting": "core-theme.md",
}

# Keyword → theme scores. Weighted by frequency in caption + transcript.
# Order matters: more specific phrases first to avoid false matches.
THEME_KEYWORDS: dict[str, list[tuple[str, int]]] = {
    "essays": [
        ("personal statement", 4), ("common app essay", 4), ("supplemental essay", 4),
        ("why us", 3), ("essay hook", 4), ("college essay", 3), ("essay prompt", 3),
        ("ppf framework", 3), ("narrative arc", 2), ("writing your essay", 2),
        ("essay draft", 2), ("common statement", 3), ("additional info", 2),
    ],
    "activities": [
        ("activities list", 5), ("extracurricular", 3), ("passion project", 4),
        ("tier 1", 3), ("tier 2", 3), ("tier 3", 3), ("three tiers", 3),
        ("summer program", 2), ("internship", 2), ("nonprofit", 2),
        ("competition", 2), ("leadership role", 2), ("founder", 2),
        ("club president", 2), ("started", 1), ("launched", 1), ("built", 1),
    ],
    "timeline": [
        ("august", 2), ("september", 1), ("october", 1), ("november 1", 4),
        ("nov 1", 4), ("deadline", 3), ("early decision", 3), ("early action", 3),
        ("regular decision", 3), ("ea deadline", 3), ("ed deadline", 3),
        ("application deadline", 3), ("checklist", 2), ("rising senior", 3),
        ("rising junior", 3), ("sophomore year", 2), ("junior year", 2),
        ("senior year", 2), ("freshman year", 1), ("summer before", 2),
    ],
    "school_list": [
        ("school list", 5), ("college list", 4), ("dream school", 3),
        ("safety school", 3), ("target school", 3), ("reach school", 3),
        ("common data set", 3), ("net price calculator", 3), ("fit", 2),
        ("how to pick", 3), ("ivy league school", 3),
        ("harvard", 2), ("stanford", 2), ("yale", 2), ("princeton", 2),
        ("columbia", 2), ("penn", 1), ("cornell", 1), ("dartmouth", 1),
        ("brown", 1), ("ucla", 1), ("nyu", 1), ("usc", 1),
    ],
    "interviews": [
        ("interview", 4), ("tell me about yourself", 4), ("greatest weakness", 4),
        ("alumni interview", 3), ("interview prep", 3), ("interview question", 3),
        ("interview tips", 3), ("mock interview", 2),
    ],
    "testing": [
        ("sat", 3), ("dsat", 3), ("digital sat", 3), ("act", 2), ("toefl", 2),
        ("ielts", 2), ("test prep", 2), ("test optional", 3), ("ap score", 2),
        ("ap exam", 2), ("score", 1),
    ],
    "recommendations": [
        ("letter of recommendation", 4), ("recommendation letter", 4),
        ("teacher rec", 3), ("counselor rec", 3), ("brag sheet", 3),
        ("letter writer", 2), ("lor", 3), ("rec letter", 3),
    ],
    "myths_mindset": [
        ("myth", 3), ("lie", 2), ("myths", 3), ("common mistake", 3),
        ("don't make", 2), ("stop doing", 3), ("college admissions myths", 4),
        ("ivy league admissions", 3), ("myth:", 3), ("rejected", 2),
        ("accepted to", 2), ("imposter", 2), ("burnout", 2),
    ],
    "study_skills": [
        ("study", 3), ("studying", 3), ("focus", 2), ("productivity", 3),
        ("flashcard", 2), ("note-taking", 2), ("reading", 2), ("memorize", 2),
        ("exam prep", 3), ("finals", 2), ("textbook", 2), ("note ", 1),
    ],
    "cross_cutting": [
        ("ultimate ivy league guide", 1), ("ultimate mentor", 1),
        ("ultimatementor", 1), ("#uilg", 1),
    ],
}

THEME_NAMES = list(THEME_KEYWORDS.keys())


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_transcript(path: Path) -> tuple[str, str] | None:
    """Return (code, full_text) or None if the file isn't a real transcript."""
    txt = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^code:\s*(\S+)\s*$", txt, re.MULTILINE)
    if not m:
        return None
    return m.group(1), txt


def classify(text: str) -> list[str]:
    """Return ranked theme list for the given text (top themes only)."""
    text_low = text.lower()
    scores: dict[str, int] = Counter()
    for theme, kws in THEME_KEYWORDS.items():
        for kw, weight in kws:
            if kw in text_low:
                scores[theme] += weight
    # Keep themes with score >= 3
    ranked = [(t, s) for t, s in scores.items() if s >= 3]
    ranked.sort(key=lambda x: x[1], reverse=True)
    if not ranked:
        return ["cross_cutting"]
    # cross_cutting is a fallback only — never append it alongside real themes.
    real = [t for t, _ in ranked if t != "cross_cutting"]
    return real[:4] if real else ["cross_cutting"]


def distill_summary(code: str, text: str, themes: list[str]) -> str:
    """Build a distillation entry: extract key claims + quote a representative
    line. Cap length aggressively to keep the KB scannable."""
    # Pull the caption section as the most readable signal
    cap_m = re.search(r"## Caption\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    caption = (cap_m.group(1).strip() if cap_m else text).strip()

    # Truncate intelligently: take first ~350 chars, break at sentence boundary
    summary = caption
    if len(summary) > 380:
        cut = summary[:380]
        last_period = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
        if last_period > 200:
            summary = cut[: last_period + 1]
        else:
            summary = cut + "…"

    theme_str = ", ".join(themes)
    return f"### {code} [{theme_str}]\n\n{summary}\n"


def already_in_kb(kb_path: Path, code: str) -> bool:
    if not kb_path.exists():
        return False
    head = kb_path.read_text(encoding="utf-8", errors="replace")
    return f"### {code} [" in head or f"### {code}\n" in head or f"[{code}]" in head


def load_distill_state() -> dict:
    if DISTILL_STATE_PATH.exists():
        return json.loads(DISTILL_STATE_PATH.read_text(encoding="utf-8"))
    return {"distilled_codes": [], "last_run": None}


def save_distill_state(s: dict) -> None:
    DISTILL_STATE_PATH.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")


def load_pool() -> dict:
    posts = json.loads((ROOT / "posts_index.json").read_text(encoding="utf-8"))["records"]
    return {r["code"]: r for r in posts}


def main() -> int:
    pool = load_pool()
    distill_state = load_distill_state()
    distilled = set(distill_state["distilled_codes"])

    pipeline_state = json.loads(STATE_PATH.read_text(encoding="utf-8")) if STATE_PATH.exists() else {"done_codes": []}
    # Codes added by THIS run = pipeline_state.done_codes minus the already-distilled set
    newly_done = [c for c in pipeline_state["done_codes"] if c not in distilled]

    print(f"[distill] newly_done_in_pipeline={len(newly_done)} already_distilled={len(distilled)}", flush=True)

    manifest_delta: list[dict] = []
    # Append to KB files, keyed by theme
    kb_appends: dict[str, list[str]] = {}

    for code in newly_done:
        md_path = TRANSCRIPTS_DIR / f"{code}.md"
        if not md_path.exists():
            continue
        parsed = parse_transcript(md_path)
        if not parsed:
            continue
        _, text = parsed
        themes = classify(text)
        entry = distill_summary(code, text, themes)
        # Add to each theme's KB file (if not already present)
        for theme in themes:
            kb_file = THEME_TO_KB.get(theme)
            if not kb_file:
                continue
            kb_path = KB_DIR / kb_file
            if already_in_kb(kb_path, code):
                continue
            kb_appends.setdefault(kb_file, []).append(entry)

        # Record a manifest entry
        rec = pool.get(code, {})
        manifest_delta.append({
            "code": code,
            "taken_at": rec.get("taken_at"),
            "product_type": rec.get("product_type"),
            "like_count": rec.get("like_count"),
            "themes": themes,
            "caption_preview": (rec.get("caption") or "")[:280],
        })
        distill_state["distilled_codes"].append(code)

    # Apply KB appends
    for kb_file, entries in kb_appends.items():
        kb_path = KB_DIR / kb_file
        with kb_path.open("a", encoding="utf-8") as f:
            f.write("\n---\n\n")
            f.write(f"## Distilled items (2026-08-31 batch)\n\n")
            f.write("".join(entries))
        print(f"[kb] appended {len(entries)} entries to {kb_file}", flush=True)

    DELTA_PATH.write_text(json.dumps({"items": manifest_delta}, indent=2, ensure_ascii=False), encoding="utf-8")
    distill_state["last_run"] = now_iso()
    save_distill_state(distill_state)
    print(f"[distill] manifest_delta={len(manifest_delta)} kb_files_touched={len(kb_appends)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
