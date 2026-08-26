"""Sample captions for classifier calibration."""

from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    data = json.loads((ROOT / "posts_index.json").read_text(encoding="utf-8"))
    recs = data["records"]
    random.seed(11)
    for r in random.sample(recs, 25):
        cap = (r["caption"] or "").replace("\n", " | ")[:180]
        print(f"[{r['code']}] {r['product_type']} likes={r['like_count']}")
        print(f"  {cap}")
        print()
    print("=== top-engagement sample ===")
    for r in sorted(recs, key=lambda x: x["like_count"], reverse=True)[:15]:
        cap = (r["caption"] or "").replace("\n", " | ")[:150]
        print(f"[{r['code']}] {r['like_count']} :: {cap}")


if __name__ == "__main__":
    main()
