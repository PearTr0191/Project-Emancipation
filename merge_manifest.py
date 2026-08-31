"""merge_manifest.py — Merge manifest_delta.json into manifest.json.

Reads:
  D:\\Project Emancipation\\manifest.json         (existing 72-item selection)
  D:\\Project Emancipation\\manifest_delta.json   (new items from distill run)

Writes:
  D:\\Project Emancipation\\manifest.json         (merged, with recomputed theme_coverage)

Backs up the original to manifest.json.bak.
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Project Emancipation")
MANIFEST = ROOT / "manifest.json"
DELTA = ROOT / "manifest_delta.json"
BACKUP = ROOT / "manifest.json.bak"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    if not MANIFEST.exists():
        print(f"[error] missing {MANIFEST}", flush=True)
        return 1
    if not DELTA.exists():
        print(f"[error] missing {DELTA} — run distill_loop.py first", flush=True)
        return 1

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    new_items = delta.get("items", [])

    if not new_items:
        print("[merge] no new items in delta — nothing to merge", flush=True)
        return 0

    # Backup original
    shutil.copy2(MANIFEST, BACKUP)
    print(f"[backup] -> {BACKUP}", flush=True)

    existing_codes = {it["code"] for it in manifest["items"]}
    added = []
    for it in new_items:
        if it["code"] in existing_codes:
            continue
        # Normalize to manifest schema
        manifest["items"].append({
            "code": it["code"],
            "taken_at": it.get("taken_at"),
            "product_type": it.get("product_type"),
            "like_count": it.get("like_count"),
            "themes": it.get("themes") or [],
            "promo_hits": 0,  # unknown for new items; recompute downstream if needed
            "ed_hits": 0,
            "score": None,
            "caption_preview": it.get("caption_preview", ""),
        })
        added.append(it["code"])
        existing_codes.add(it["code"])

    # Recompute theme_coverage
    coverage = Counter()
    for it in manifest["items"]:
        for t in it.get("themes") or []:
            coverage[t] += 1
    manifest["theme_coverage"] = dict(coverage)
    manifest["selected"] = len(manifest["items"])
    manifest["merged_at"] = now_iso()
    manifest["merge_added"] = len(added)

    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[merge] added={len(added)} total_items={len(manifest['items'])}", flush=True)
    print(f"[merge] theme_coverage: {dict(coverage)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
