"""Download recent-cycle media: videos + covers + full carousel slides (newest first)."""

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
    merged: dict[str, dict] = {}
    for name in ("recent_media.json", "recent_media_2.json"):
        p = ROOT / name
        if not p.exists():
            continue
        raw = p.read_text(encoding="utf-8")
        d = json.loads(raw)
        if isinstance(d, str):
            d = json.loads(d)
        for k, v in d["media"].items():
            merged.setdefault(k, v)
    return merged


def fetch(url: str, dest: Path) -> bool:
    try:
        with requests.get(url, headers=UA, timeout=120, stream=True) as r:
            if r.status_code != 200:
                return False
            tmp = dest.with_suffix(dest.suffix + ".part")
            with open(tmp, "wb") as fh:
                for chunk in r.iter_content(1 << 16):
                    fh.write(chunk)
            head = open(tmp, "rb").read(16)
            ok = b"ftyp" in head or head[:3] == b"\xff\xd8\xff" or b"RIFF" in head
            if not ok:
                tmp.unlink(missing_ok=True)
                return False
            tmp.replace(dest)
            return True
    except requests.RequestException:
        return False


def main() -> None:
    media = load_media()
    cands = json.loads((ROOT / "new_candidates.json").read_text(encoding="utf-8"))
    items = cands["items"]
    print(f"candidates={len(items)} harvested={len(media)}")
    stats = {"videos": 0, "images": 0}
    missing_videos: list[str] = []
    for it in items:
        code = it["code"]
        m = media.get(code, {})
        pdir = INBOX / code
        dest_v = pdir / "video.mp4"
        need_video = it["product_type"] == "clips"
        if need_video and m.get("video") and not (dest_v.exists() and b"ftyp" in dest_v.read_bytes()[:16]):
            pdir.mkdir(parents=True, exist_ok=True)
            if fetch(m["video"], dest_v):
                stats["videos"] += 1
            else:
                missing_videos.append(code)
            time.sleep(1.0)

        n_img = 0
        urls: list[str] = []

        def push(u: str | None) -> None:
            if u:
                urls.append(u)

        for cov in m.get("covers", []):
            push(cov)
        for cm in m.get("carousel", []):
            for iu in cm.get("images", []):
                push(iu)
            if cm.get("video"):
                pass
        seen: set[str] = set()
        for u in urls:
            key = u.split("?")[0][-60:]
            if key in seen:
                continue
            seen.add(key)
            dest = pdir / f"img_{n_img:02d}.jpg"
            if dest.exists():
                n_img += 1
                continue
            pdir.mkdir(parents=True, exist_ok=True)
            if fetch(u, dest):
                n_img += 1
                stats["images"] += 1
            time.sleep(0.6)
    (ROOT / "recent_missing_videos.json").write_text(json.dumps(missing_videos, indent=1), encoding="utf-8")
    print(f"videos={stats['videos']} images={stats['images']} video_failures={len(missing_videos)}")


if __name__ == "__main__":
    main()
