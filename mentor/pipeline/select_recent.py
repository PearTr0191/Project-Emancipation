"""Second-pass selection: recent-cycle content, newest-first priority.

- All image posts (carousels + photos) from the recency window
- Reels flagged by novelty/regulation keywords
- Top-engagement recent reels for coverage
Excludes codes already in manifest.json.
Writes new_candidates.json ordered newest-first.
"""

from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WINDOW_START = dt.datetime(2025, 9, 1, tzinfo=dt.timezone.utc)

NOVELTY_KEYWORDS = [
    "fafsa", "financial aid", "new sat", "dsat", "digital sat", "test optional",
    "test-optional", "common app update", "new rule", "rules changed", "change",
    "2026", "2027", "this year", "no longer", "now require", "banned", "ai ",
    "chatgpt", "policy", "update", "deadline change", "early decision",
]

CORE_TOPICS = [
    "essay", "activity", "interview", "school list", "recommendation",
    "senior", "junior", "timeline", "checklist", "waitlist", "deferral",
]


def main() -> None:
    idx = json.loads((ROOT / "posts_index.json").read_text(encoding="utf-8"))
    man = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    existing = {it["code"] for it in man["items"]}

    cands: list[dict[str, object]] = []
    for r in idx["records"]:
        if r["code"] in existing:
            continue
        ts = r.get("taken_at")
        if not ts:
            continue
        d = dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)
        if d < WINDOW_START:
            continue
        cap = (r["caption"] or "").lower()
        novelty = [k for k in NOVELTY_KEYWORDS if k in cap]
        core = [k for k in CORE_TOPICS if k in cap]
        is_image = r["product_type"] in {"carousel_container", "feed"}
        tier = 0
        if is_image:
            tier = 1
        elif novelty:
            tier = 2
        elif core:
            tier = 3
        else:
            tier = 4
        score = (
            -r["taken_at"] / 1e9
            + (5.0 if is_image else 0.0)
            + 1.5 * len(novelty)
            + 0.5 * len(core)
            + min(1.5, math.log10(max(r["like_count"], 10)) - 1.0)
        )
        cands.append({
            "code": r["code"],
            "taken_at": ts,
            "date": d.date().isoformat(),
            "product_type": r["product_type"],
            "like_count": r["like_count"],
            "tier": tier,
            "novelty": novelty,
            "core": core,
            "caption_preview": (r["caption"] or "")[:200].replace("\n", " | "),
            "_score": round(score, 3),
        })

    # newest-first strict ordering (user requirement); tiers only inform caps below
    cands.sort(key=lambda x: x["taken_at"], reverse=True)

    images = [c for c in cands if c["tier"] == 1]
    novelty_reels = [c for c in cands if c["tier"] == 2]
    core_reels = [c for c in cands if c["tier"] == 3]
    other_reels = [c for c in cands if c["tier"] == 4]

    selected = images[:60] + novelty_reels[:40] + core_reels[:25] + other_reels[:10]
    selected.sort(key=lambda x: x["taken_at"], reverse=True)

    out = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "window_start": WINDOW_START.date().isoformat(),
        "pool_in_window": len(cands),
        "selected": len(selected),
        "breakdown": {
            "image_posts": len(images[:60]),
            "novelty_reels": len(novelty_reels[:40]),
            "core_reels": len(core_reels[:25]),
            "other_reels": len(other_reels[:10]),
        },
        "items": selected,
    }
    (ROOT / "new_candidates.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"pool in window: {len(cands)} | selected: {len(selected)}")
    print("breakdown:", out["breakdown"])
    print("\nnewest 15:")
    for c in selected[:15]:
        print(f"  [{c['date']}] {c['product_type']:<18} T{c['tier']} {c['code']} :: {str(c['caption_preview'])[:90]}")


if __name__ == "__main__":
    main()
