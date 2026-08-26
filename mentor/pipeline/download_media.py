"""Download media for manifest posts using harvested CDN URLs."""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
INBOX = ROOT / "mentor" / "inbox"
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.instagram.com/",
}


def load_media() -> dict[str, dict]:
    raw = (ROOT / "media_urls.json").read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
        if isinstance(data, str):
            data = json.loads(data)
    except json.JSONDecodeError:
        data = json.loads(json.loads(raw))
    return data["media"]


def fetch(url: str, dest: Path, max_bytes: int = 200 * 1024 * 1024) -> bool:
    try:
        with requests.get(url, headers=UA, timeout=60, stream=True) as r:
            if r.status_code != 200:
                return False
            size = 0
            tmp = dest.with_suffix(dest.suffix + ".part")
            with open(tmp, "wb") as fh:
                for chunk in r.iter_content(1 << 16):
                    size += len(chunk)
                    if size > max_bytes:
                        tmp.unlink(missing_ok=True)
                        return False
                    fh.write(chunk)
            tmp.rename(dest)
            return True
    except requests.RequestException:
        return False


def main() -> None:
    media = load_media()
    print(f"posts in harvest: {len(media)}")
    stats = {"videos": 0, "images": 0, "video_fail": 0}
    for code, m in sorted(media.items()):
        pdir = INBOX / code
        pdir.mkdir(parents=True, exist_ok=True)
        if not (pdir / "video.mp4").exists() and m["mp4"]:
            ok = False
            for u in m["mp4"][:3]:
                if fetch(u, pdir / "video.mp4"):
                    ok = True
                    break
            stats["videos" if ok else "video_fail"] += 1
            time.sleep(0.8)
        n_img = 0
        seen_base: set[str] = set()
        for iu in list(dict.fromkeys([m.get("ogImage") or "", *m["imgs"]])):
            if not iu or n_img >= 12:
                break
            base = iu.split("?")[0].rsplit("/", 1)[-1][:40]
            key = base.split("_")[0] if base else iu[:60]
            if key in seen_base:
                continue
            seen_base.add(key)
            dest = pdir / f"img_{n_img:02d}.jpg"
            if dest.exists():
                n_img += 1
                continue
            if fetch(iu, dest):
                n_img += 1
                stats["images"] += 1
            time.sleep(0.5)
    print(f"downloaded videos={stats['videos']} failed_videos={stats['video_fail']} images={stats['images']}")


if __name__ == "__main__":
    main()
