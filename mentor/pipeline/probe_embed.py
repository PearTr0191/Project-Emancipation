"""Probe the public embed endpoint for media URLs (no login required)."""

from __future__ import annotations

import re

import requests

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def probe(code: str) -> None:
    url = f"https://www.instagram.com/p/{code}/embed/captioned/"
    r = requests.get(url, headers=UA, timeout=30)
    print(f"=== {code} status={r.status_code} bytes={len(r.text)} ===")
    text = r.text
    video_urls = re.findall(r'"video_url":"([^"]+)"', text) or re.findall(r'property="og:video" content="([^"]+)"', text)
    img_urls = re.findall(r'class="EmbeddedMediaImage"[^>]+src="([^"]+)"', text) or re.findall(r'property="og:image" content="([^"]+)"', text)
    cap = re.search(r'class="Caption".*?</div>', text, re.S)
    print("video_urls:", [u[:100] for u in video_urls[:2]])
    print("img_urls:", [u[:100] for u in img_urls[:2]])
    print("caption block found:", bool(cap))
    if "videoUrl" in text:
        m = re.findall(r'"videoUrl":"([^"]+)"', text)
        print("videoUrl keys:", [u[:100] for u in m[:2]])


if __name__ == "__main__":
    probe("C8kWueLvk20")   # carousel
    probe("C_dSOkiuOqi")   # reel
