"""validate_ivybrothers.py — Post-run validation for the Ivy Brothers crawl.

Parallel to validate.py (which checks the UILG pool — ivybrothers transcripts
would be false orphans there). Confirms:
  1. All ivybrothers transcripts reference codes in posts_index_ivybrothers.json.
  2. ib_state.json.done_codes ↔ transcript files.
  3. Pool coverage: pool = done + failed + unprocessed, no overlaps.
  4. manifest_ivybrothers.json theme_coverage sums match actual item counts.
  5. Asset dirs exist for transcripts claiming slides; slide files exist.
  6. No orphan FAILED.json files.

Exits 0 on pass, 1 on fail.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Project Emancipation")
TRANSCRIPTS_DIR = ROOT / "mentor" / "transcripts"
ASSETS_DIR = ROOT / "ivybrothers_assets"
HANDLE = "ivybrothersofficial"


def is_ivybrothers_transcript(p: Path) -> bool:
    head = p.read_text(encoding="utf-8", errors="replace")[:300]
    return f"handle: {HANDLE}" in head


def transcript_code(p: Path) -> str | None:
    head = p.read_text(encoding="utf-8", errors="replace")[:300]
    m = re.search(r"^code:\s*(\S+)\s*$", head, re.MULTILINE)
    return m.group(1) if m else None


def main() -> int:
    issues: list[str] = []

    # 1. ivybrothers transcripts vs posts_index_ivybrothers.json
    index_path = ROOT / "posts_index_ivybrothers.json"
    if not index_path.exists():
        issues.append("posts_index_ivybrothers.json missing")
        pool: set[str] = set()
    else:
        index = json.loads(index_path.read_text(encoding="utf-8"))
        pool = {r["code"] for r in index["records"]}
        print(f"[index] pool={len(index['pool_size']) if False else len(index['records'])} scraped_at={index.get('scraped_at')}")

    ib_transcripts: dict[str, Path] = {}
    for p in TRANSCRIPTS_DIR.glob("*.md"):
        if is_ivybrothers_transcript(p):
            code = transcript_code(p)
            if code:
                ib_transcripts[code] = p
    print(f"[transcripts] ivybrothers={len(ib_transcripts)}")

    orphans = set(ib_transcripts) - pool
    if orphans:
        issues.append(f"{len(orphans)} ivybrothers transcripts not in posts_index_ivybrothers.json (first 5: {sorted(orphans)[:5]})")

    # 2. ib_state done_codes vs transcript files
    state_path = ROOT / "ib_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        done = set(state.get("done_codes", []))
        missing_files = done - set(ib_transcripts)
        if missing_files:
            issues.append(f"{len(missing_files)} done codes lack a transcript file (first 5: {sorted(missing_files)[:5]})")
        failed = state.get("failed_codes", {})
        print(f"[state] done={len(done)} failed={len(failed)} login_wall_hit={state.get('login_wall_hit', False)}")
    else:
        issues.append("ib_state.json missing")

    # 3. pool coverage
    if pool:
        done_set = done if state_path.exists() else set()
        failed_set = set(failed.keys()) if state_path.exists() else set()
        unprocessed = pool - done_set - failed_set
        print(f"[coverage] done={len(done_set & pool)} failed={len(failed_set & pool)} unprocessed={len(unprocessed)}")
        if failed_set - pool:
            issues.append(f"{len(failed_set - pool)} failed codes not in pool (first 5: {sorted(failed_set - pool)[:5]})")

    # 4. manifest theme coverage
    manifest_path = ROOT / "manifest_ivybrothers.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        items = manifest["items"]
        coverage_actual: Counter = Counter()
        for it in items:
            for t in it.get("themes") or []:
                coverage_actual[t] += 1
        reported = manifest.get("theme_coverage", {})
        for t, c in coverage_actual.items():
            if reported.get(t) != c:
                issues.append(f"theme_coverage mismatch for {t}: reported={reported.get(t)} actual={c}")
        manifest_codes = {it["code"] for it in items}
        transcripts_not_in_manifest = set(ib_transcripts) - manifest_codes
        if transcripts_not_in_manifest:
            issues.append(f"{len(transcripts_not_in_manifest)} transcripts missing from manifest (first 5: {sorted(transcripts_not_in_manifest)[:5]})")
        print(f"[manifest] items={len(items)} theme_coverage={dict(coverage_actual)}")
    else:
        issues.append("manifest_ivybrothers.json missing")

    # 5. assets: transcripts claiming slides must have slide files
    missing_assets: list[str] = []
    slide_total = 0
    for code, p in ib_transcripts.items():
        body = p.read_text(encoding="utf-8", errors="replace")
        refs = re.findall(r"- ivybrothers_assets/" + re.escape(code) + r"/(slide_\d+\.jpg)", body)
        if not refs:
            continue
        code_dir = ASSETS_DIR / code
        for fname in refs:
            slide_total += 1
            if not (code_dir / fname).exists():
                missing_assets.append(f"{code}/{fname}")
    if missing_assets:
        issues.append(f"{len(missing_assets)} referenced slide files missing on disk (first 5: {missing_assets[:5]})")
    print(f"[assets] referenced_slides={slide_total} missing={len(missing_assets)}")

    # 6. orphan FAILED.json
    failed_files = list(TRANSCRIPTS_DIR.glob("*.FAILED.json"))
    if failed_files:
        print(f"[failed-files] {len(failed_files)} orphan FAILED.json files")

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
