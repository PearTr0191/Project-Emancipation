"""Selection pass: score, tag, dedupe, and pick the curated subset.

Reads posts_index.json -> writes manifest.json.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

THEME_KEYWORDS: dict[str, list[str]] = {
    "essays": [
        "essay", "common app essay", "personal statement", "supplemental",
        "why this essay", "college essay", "uc essays", "piq", "writing your",
    ],
    "activities": [
        "activity", "extracurricular", "spike", "passion project", "summer program",
        "research program", "internship", "award", "honor", "common app activities",
    ],
    "school_list": [
        "school list", "reach school", "safety school", "target school", "why us",
        "why this college", "demonstrated interest", "early decision", "early action",
        "restrictive early action", "ed vs ea",
    ],
    "testing": ["sat", "dsat", "act ", "psat", "test optional", "test-optional", "superscore"],
    "timeline": [
        "rising senior", "senior year", "junior year", "9th grade", "10th grade",
        "11th grade", "12th grade", "checklist", "timeline", "application opens",
        "deadline", "november 1", "january 1", "summer before",
    ],
    "interviews": ["interview", "tell me about yourself", "alumni interview"],
    "recommendations": ["recommendation letter", "letter of rec", "teacher rec", "counselor rec"],
    "myths_mindset": [
        "myth", "misconception", "rejected", "rejection", "denied", "waitlist",
        "deferral", "not enough", "perfect on paper", "truth about", "nobody tells you",
    ],
    "study_skills": [
        "study", "exam", "gpa", "grades", "finals", "memorize", "note-taking", "procrastination",
    ],
}

PROMO_PATTERNS = [
    r"link in bio",
    r"comment \w+ (for|and)",
    r"dm me",
    r"revision services",
    r"e-?book",
    r"\$\d+",
    r"#sponsored",
    r"#ad\b",
    r"selling out",
    r"website in my bio",
    r"apply (now|today)",
    r"free guide",
    r"sign up",
    r"1:1|one-on-one",
]

ED_SIGNALS = [
    "how to", "mistake", "strategy", "framework", "step", "checklist", "guide to",
    "what colleges", "admissions officers", "ao ", "stand out", "red flag", "green flag",
    "here's how", "here is how", "the truth", "actually work", "why you", "should you",
    "before you", "if you're", "if you are",
]


def norm_text(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()


def classify(caption_lower: str) -> tuple[list[str], float]:
    themes: set[str] = set()
    for theme, kws in THEME_KEYWORDS.items():
        for kw in kws:
            if re.search(r"\b" + re.escape(kw.strip()), caption_lower):
                themes.add(theme)
                break
    return sorted(themes), float(len(themes))


def dedupe_key(caption: str) -> str:
    lines = [ln.strip().lower() for ln in caption.splitlines() if ln.strip()]
    if not lines:
        return ""
    hook = norm_text(lines[0])
    words = [w for w in hook.split() if w not in {"the", "a", "an", "to", "your", "you", "how", "my"}]
    return " ".join(words[:6])


def main() -> None:
    data = json.loads((ROOT / "posts_index.json").read_text(encoding="utf-8"))
    recs = data["records"]

    scored: list[dict[str, object]] = []
    for r in recs:
        cap = r["caption"] or ""
        low = cap.lower()
        themes, breadth = classify(low)
        promo_hits = sum(1 for p in PROMO_PATTERNS if re.search(p, low))
        ed_hits = sum(1 for s in ED_SIGNALS if s in low)

        # base educational value from themes present
        priority_themes = {"essays", "activities", "school_list", "testing", "timeline",
                           "interviews", "recommendations", "myths_mindset"}
        prio = len(set(themes) & priority_themes)
        score = 3.0 * prio + 1.0 * breadth + 1.5 * ed_hits - 2.0 * promo_hits
        if promo_hits == 0 and ed_hits > 0:
            score += 1.0
        # senior-execution weighting
        if {"essays", "school_list", "timeline", "interviews"} & set(themes):
            score += 1.5
        # engagement tiebreak (log scale, capped)
        import math
        score += min(2.0, math.log10(max(r["like_count"], 10)) - 1.0)
        # carousels are dense slide-documents: slight boost
        if r["product_type"] == "carousel_container":
            score += 0.8
        scored.append({
            "code": r["code"], "taken_at": r["taken_at"], "product_type": r["product_type"],
            "like_count": r["like_count"], "themes": themes, "promo_hits": promo_hits,
            "ed_hits": ed_hits, "score": round(score, 2),
            "caption_preview": cap[:220].replace("\n", " | "),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    # dedupe similar hooks while walking ranked order
    seen_hooks: dict[str, int] = {}
    families: defaultdict[str, list[str]] = defaultdict(list)
    picked: list[dict[str, object]] = []
    THEME_TARGETS = {
        "essays": 14, "timeline": 12, "activities": 10, "school_list": 8,
        "interviews": 6, "testing": 6, "recommendations": 4, "myths_mindset": 10,
        "study_skills": 3,
    }
    theme_counts: defaultdict[str, int] = defaultdict(int)
    TARGET_TOTAL = 72

    for item in scored:
        if len(picked) >= TARGET_TOTAL:
            break
        dk = dedupe_key(str(item["caption_preview"]))
        if dk:
            if seen_hooks.get(dk, 0) >= 1:
                continue
        themes = item["themes"] or ["general"]
        # require at least one target theme not already saturated (unless very high score)
        useful = any(t in THEME_TARGETS and theme_counts[t] < THEME_TARGETS[t] for t in themes)
        if not useful and item["score"] < 8.0:
            continue
        if dk:
            seen_hooks[dk] = seen_hooks.get(dk, 0) + 1
        picked.append(item)
        for t in themes:
            theme_counts[t] += 1
        fam = dk or "none"
        families[fam].append(str(item["code"]))

    manifest = {
        "username": data["username"],
        "selected_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "total_pool": len(recs),
        "selected": len(picked),
        "theme_coverage": {t: theme_counts[t] for t in THEME_TARGETS},
        "items": picked,
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"selected {len(picked)} of {len(recs)}")
    print("coverage:", dict(manifest["theme_coverage"]))
    print("\ntop 25:")
    for it in picked[:25]:
        print(f"  [{it['code']}] {it['score']:>5} {it['themes']} :: {str(it['caption_preview'])[:110]}")


if __name__ == "__main__":
    main()
