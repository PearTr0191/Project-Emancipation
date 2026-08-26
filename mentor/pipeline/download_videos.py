"""Download manifest videos from harvested progressive-mp4 URLs (multiple sources merged)."""

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


def load(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    d = json.loads(raw)
    if isinstance(d, str):
        d = json.loads(d)
    return {k: v for k, v in d.get("videos", {}).items() if isinstance(v, str) and v.startswith("http")}


def fetch(url: str, dest: Path) -> bool:
    try:
        with requests.get(url, headers=UA, timeout=120, stream=True) as r:
            if r.status_code != 200:
                return False
            tmp = dest.with_suffix(".part")
            with open(tmp, "wb") as fh:
                for chunk in r.iter_content(1 << 16):
                    fh.write(chunk)
            head = open(tmp, "rb").read(12)
            if b"ftyp" not in head:
                tmp.unlink(missing_ok=True)
                return False
            tmp.replace(dest)
            return True
    except requests.RequestException:
        return False


def main() -> None:
    merged: dict[str, str] = {}
    merged.update(load(ROOT / "video_urls.json"))
    merged.update(load(ROOT / "video_urls_2.json"))
    merged.update(load(ROOT / "video_urls_3.json"))
    man = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    codes = [it["code"] for it in man["items"]]
    have = [c for c in codes if c in merged]
    print(f"manifest={len(codes)} urls_available={len(have)}")
    ok = 0
    for code in have:
        pdir = INBOX / code
        dest = pdir / "video.mp4"
        if dest.exists():
            head = open(dest, "rb").read(12)
            if b"ftyp" in head:
                continue
        pdir.mkdir(parents=True, exist_ok=True)
        if fetch(merged[code], dest):
            ok += 1
            print(f"  {code} ok", flush=True)
        else:
            print(f"  {code} FAILED", flush=True)
        time.sleep(1.2)
    still_missing = [c for c in codes if not (INBOX / c / "video.mp4").exists()]
    (ROOT / "videos_missing.json").write_text(json.dumps(still_missing), encoding="utf-8")
    print(f"downloaded={ok} missing_now={len(still_missing)}")


if __name__ == "__main__":
    main()
