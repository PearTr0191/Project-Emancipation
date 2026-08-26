"""Metadata-only discovery pass over a public Instagram profile.

Writes records incrementally to posts_index.jsonl (checkpoint/resume),
then consolidates to posts_index.json on success.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import instaloader
from instaloader import (
    ConnectionException,
    LoginRequiredException,
    Profile,
    QueryReturnedBadRequestException,
    QueryReturnedForbiddenException,
)

TARGET = "ultimateivyleagueguide"
ROOT = Path(__file__).resolve().parents[2]
OUT_JSONL = ROOT / "posts_index.jsonl"
OUT_JSON = ROOT / "posts_index.json"


def build_loader() -> instaloader.Instaloader:
    loader = instaloader.Instaloader(
        download_comments=False,
        download_geotags=False,
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        save_metadata=False,
        compress_json=False,
        post_metadata_txt_pattern="",
        quiet=True,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
    )
    try:
        loader.load_session_from_file(TARGET)
        print("[session] loaded stored session", flush=True)
    except FileNotFoundError:
        print("[session] no stored session, proceeding anonymously", flush=True)
    except Exception as exc:  # noqa: BLE001 - session issues must not kill discovery
        print(f"[session] could not load session ({exc}); going anonymous", flush=True)
    return loader


def load_seen() -> set[str]:
    if not OUT_JSONL.exists():
        return set()
    seen: set[str] = set()
    for line in OUT_JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            seen.add(json.loads(line)["shortcode"])
        except (json.JSONDecodeError, KeyError):
            continue
    return seen


def record_of(post: instaloader.Post) -> dict[str, object]:
    return {
        "shortcode": post.shortcode,
        "date_utc": post.date_utc.isoformat(),
        "typename": getattr(post, "typename", ""),
        "is_video": bool(post.is_video),
        "mediacount": int(post.mediacount),
        "likes": int(post.likes),
        "comments": int(post.comments),
        "caption": post.caption or "",
    }


def consolidate() -> None:
    records: list[dict[str, object]] = []
    for line in OUT_JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    dedup: dict[str, dict[str, object]] = {r["shortcode"]: r for r in records}
    ordered = sorted(dedup.values(), key=lambda r: str(r["date_utc"]), reverse=True)
    OUT_JSON.write_text(json.dumps(ordered, indent=2), encoding="utf-8")
    print(f"[done] consolidated {len(ordered)} unique posts -> {OUT_JSON.name}", flush=True)


def main() -> int:
    seen = load_seen()
    mode = "resuming" if seen else "starting fresh"
    print(f"[discovery] {mode}; {len(seen)} shortcodes already indexed", flush=True)

    loader = build_loader()
    try:
        profile = Profile.from_username(loader.context, TARGET)
    except LoginRequiredException:
        print("[error] profile access requires login.", flush=True)
        print("Seed a session once with:  instaloader --login YOUR_USERNAME", flush=True)
        print("then re-run this script.", flush=True)
        return 3
    except (ConnectionException, QueryReturnedForbiddenException, QueryReturnedBadRequestException) as exc:
        print(f"[error] cannot access profile right now: {exc}", flush=True)
        return 2

    total_est = profile.mediacount
    print(f"[discovery] @{TARGET} has ~{total_est} posts", flush=True)

    out_fh = OUT_JSONL.open("a", encoding="utf-8")
    fetched = 0
    started = time.time()
    try:
        for post in profile.get_posts():
            if post.shortcode in seen:
                continue
            rec = record_of(post)
            out_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out_fh.flush()
            seen.add(rec["shortcode"])
            fetched += 1
            if fetched % 25 == 0:
                elapsed = time.time() - started
                print(f"[progress] {len(seen)} indexed (+{fetched} this run, {elapsed:.0f}s)", flush=True)
            time.sleep(1.5)
    except KeyboardInterrupt:
        print("\n[interrupt] partial progress kept; re-run to resume", flush=True)
        return 130
    except LoginRequiredException:
        print(f"\n[partial] login wall after {len(seen)} posts.", flush=True)
        print("Run:  instaloader --login YOUR_USERNAME   then re-run to resume.", flush=True)
        return 3
    except (ConnectionException, QueryReturnedForbiddenException, QueryReturnedBadRequestException) as exc:
        print(f"\n[partial] rate-limited or blocked after {len(seen)} posts: {exc}", flush=True)
        print("Wait ~15 minutes, then re-run to resume.", flush=True)
        return 2
    finally:
        out_fh.close()

    print(f"[discovery] complete: {len(seen)} posts indexed", flush=True)
    consolidate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
