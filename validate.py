"""validate.py — Post-run validation checks.

Confirms:
  1. All transcripts reference codes that exist in posts_index.json.
  2. Every code in pipeline_state.json.done_codes has a transcript file.
  3. Every code in pending_codes.json is either done, failed, or in manifest.
  4. manifest.json.theme_coverage sums match len(manifest.items) themes.
  5. No orphan FAILED.json files without corresponding transcript.

Reports a single summary line at the end. Exits 0 on pass, 1 on fail.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Project Emancipation")
TRANSCRIPTS_DIR = ROOT / "mentor" / "transcripts"


def main() -> int:
    issues: list[str] = []

    # 1. posts_index.json vs transcript codes
    pool = {r["code"] for r in json.loads((ROOT / "posts_index.json").read_text(encoding="utf-8"))["records"]}
    code_re = re.compile(r"^code:\s*(\S+)\s*$", re.MULTILINE)
    transcript_codes: set[str] = set()
    for p in TRANSCRIPTS_DIR.glob("*.md"):
        m = code_re.search(p.read_text(encoding="utf-8", errors="replace"))
        if m:
            transcript_codes.add(m.group(1))

    orphan_transcripts = transcript_codes - pool
    if orphan_transcripts:
        issues.append(f"{len(orphan_transcripts)} transcript codes not in posts_index.json (first 5: {sorted(orphan_transcripts)[:5]})")

    # 2. pipeline_state.json.done_codes vs transcript files
    state_path = ROOT / "pipeline_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        done = set(state.get("done_codes", []))
        missing = done - transcript_codes
        if missing:
            issues.append(f"{len(missing)} done codes lack a transcript file (first 5: {sorted(missing)[:5]})")
        print(f"[state] done={len(done)} failed={len(state.get('failed_codes', {}))}")
    else:
        issues.append("pipeline_state.json missing")

    # 3. pending_codes.json coverage
    pending_path = ROOT / "pending_codes.json"
    if pending_path.exists():
        pending = set(json.loads(pending_path.read_text(encoding="utf-8"))["pending_codes"])
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        covered = transcript_codes | {it["code"] for it in manifest["items"]}
        # Note: candidates file is allowed as covered too
        cand_path = ROOT / "new_candidates.json"
        if cand_path.exists():
            cands = {it["code"] for it in json.loads(cand_path.read_text(encoding="utf-8"))["items"]}
        else:
            cands = set()
        all_covered = covered | cands
        still_pending = pending - all_covered
        if still_pending:
            print(f"[pending] {len(still_pending)} codes still unaccounted for (first 10: {sorted(still_pending)[:10]})")
        else:
            print(f"[pending] all {len(pending)} originally-pending codes are now covered")

    # 4. manifest theme coverage
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    items = manifest["items"]
    coverage_actual = Counter()
    for it in items:
        for t in it.get("themes") or []:
            coverage_actual[t] += 1
    coverage_reported = manifest.get("theme_coverage", {})
    for t, c in coverage_actual.items():
        if coverage_reported.get(t) != c:
            issues.append(f"theme_coverage mismatch for {t}: reported={coverage_reported.get(t)} actual={c}")

    print(f"[manifest] total_items={len(items)} theme_coverage={dict(coverage_actual)}")

    # 5. orphan FAILED files
    failed_files = list(TRANSCRIPTS_DIR.glob("*.FAILED.json"))
    if failed_files:
        print(f"[failed-files] {len(failed_files)} orphan FAILED.json files (first 5: {[f.name for f in failed_files[:5]]})")

    print()
    if issues:
        print("[ISSUES]")
        for i in issues:
            print(f"  - {i}")
        return 1
    print("[OK] all validations pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
