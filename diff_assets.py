"""diff_assets.py — One-shot diff to compute the pending set.

Reads:
  D:\Project Emancipation\posts_index.json    (full pool, 1044 records)
  D:\Project Emancipation\manifest.json        (already-distilled 72 selected)
  D:\Project Emancipation\new_candidates.json  (already-tagged 121 candidates)
  D:\Project Emancipation\mentor\transcripts\  (existing transcripts on disk)

Writes:
  D:\Project Emancipation\pending_codes.json  (list of codes we still owe)

Exits 0 on success, 1 if any input file is missing.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Project Emancipation")
TRANSCRIPTS_DIR = ROOT / "mentor" / "transcripts"


def load_json(path: Path) -> object:
    if not path.exists():
        print(f"[error] missing: {path}", flush=True)
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def parse_transcript_codes(transcripts_dir: Path) -> set[str]:
    """Extract `code: <value>` from YAML front-matter of every transcript md."""
    code_re = re.compile(r"^code:\s*(\S+)\s*$", re.MULTILINE)
    codes: set[str] = set()
    if not transcripts_dir.exists():
        return codes
    for p in transcripts_dir.glob("*.md"):
        m = code_re.search(p.read_text(encoding="utf-8", errors="replace"))
        if m:
            codes.add(m.group(1))
    return codes


def main() -> int:
    posts_index = load_json(ROOT / "posts_index.json")
    manifest = load_json(ROOT / "manifest.json")
    new_candidates = load_json(ROOT / "new_candidates.json")

    pool = {r["code"]: r for r in posts_index["records"]}
    selected = {item["code"] for item in manifest["items"]}
    candidates = {item["code"] for item in new_candidates["items"]}
    transcribed = parse_transcript_codes(TRANSCRIPTS_DIR)

    # Already-covered = in manifest OR in new_candidates OR has a transcript on disk
    covered = selected | candidates | transcribed
    pending_codes = [c for c in pool.keys() if c not in covered]

    # Partition by product_type
    by_type: Counter[str] = Counter()
    for code in pending_codes:
        pt = pool[code].get("product_type") or "unknown"
        by_type[pt] += 1

    # Reorder pending by taken_at desc (newest first) so the most signal-rich
    # items are processed first in case the run is interrupted.
    pending_codes.sort(key=lambda c: pool[c].get("taken_at", 0), reverse=True)

    out = {
        "username": posts_index.get("username"),
        "computed_at": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pool_size": len(pool),
        "manifest_selected": len(selected),
        "new_candidates": len(candidates),
        "transcripts_on_disk": len(transcribed),
        "covered_total": len(covered),
        "pending_count": len(pending_codes),
        "pending_by_product_type": dict(by_type),
        "pending_codes": pending_codes,
    }
    out_path = ROOT / "pending_codes.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[diff] pool={len(pool)} manifest={len(selected)} candidates={len(candidates)} transcripts={len(transcribed)}")
    print(f"[diff] covered={len(covered)} pending={len(pending_codes)}")
    print(f"[diff] by_product_type: {dict(by_type)}")
    print(f"[saved] {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
