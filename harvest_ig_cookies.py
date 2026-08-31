"""Launch Chrome with the user's existing profile (inherits IG login),
navigate to instagram.com, and save cookies to the JSON shape that
SEO/pipeline/refresh_session.py expects.

The output file path and Chrome profile are configurable. Default Chrome
profile on Windows: LOCALAPPDATA/Google/Chrome/User Data/Default
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except (AttributeError, OSError):
    pass

from playwright.sync_api import sync_playwright


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--user-data-dir",
        default=r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data",
        help="Chrome user data dir (parent of Default/)",
    )
    p.add_argument(
        "--profile",
        default="Default",
        help="Chrome profile subdir (e.g. Default, Profile 1)",
    )
    p.add_argument(
        "--out",
        default=r"D:\Project Emancipation\cookies.json",
        help="Output cookies.json path",
    )
    p.add_argument(
        "--ig-handle",
        default=None,
        help="Optional IG handle to navigate to first (confirms login state)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    user_data_dir = args.user_data_dir
    profile_dir = user_data_dir
    if not profile_dir.endswith(args.profile):
        profile_dir = str(Path(user_data_dir) / args.profile)

    if not Path(profile_dir).exists():
        print(f"[error] profile dir not found: {profile_dir}", flush=True)
        return 2

    cookies_out: list[dict] = []
    ig_state: dict = {}

    with sync_playwright() as p:
        # persistent_context reuses the user's Chrome profile = inherited session
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=True,
            channel="chrome",
            args=[
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-blink-features=AutomationControlled",
            ],
            viewport={"width": 1280, "height": 800},
            ignore_https_errors=True,
        )
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            target = f"https://www.instagram.com/{args.ig_handle}/" if args.ig_handle else "https://www.instagram.com/"
            print(f"[navigate] {target}", flush=True)
            page.goto(target, wait_until="domcontentloaded", timeout=45000)
            time.sleep(2.0)

            # Detect login state: look for the profile avatar / nav
            logged_in = page.evaluate(
                """() => {
                    const sels = [
                        'nav svg[aria-label]',
                        'a[href*="/direct/inbox"]',
                        'img[alt*="profile picture" i]',
                        'span[aria-label*="profile" i]',
                    ];
                    for (const s of sels) if (document.querySelector(s)) return true;
                    return location.pathname.includes('/accounts/login') === false && !document.title.toLowerCase().includes('log in');
                }"""
            )
            final_url = page.url
            title = page.title()
            print(f"[state] logged_in={logged_in} url={final_url} title={title!r}", flush=True)
            ig_state = {"logged_in": bool(logged_in), "url": final_url, "title": title}

            for c in ctx.cookies():
                if "instagram.com" in (c.get("domain") or ""):
                    cookies_out.append({
                        "name": c["name"],
                        "value": c["value"],
                        "domain": c["domain"],
                        "path": c.get("path", "/"),
                    })
            print(f"[cookies] {len(cookies_out)} instagram.com cookies captured", flush=True)
        finally:
            ctx.close()

    if not cookies_out:
        print("[error] no instagram.com cookies captured — are you logged in?", flush=True)
        return 3

    payload = {
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ig_state": ig_state,
        "cookies": cookies_out,
    }
    out_path.write_text(json.dumps(cookies_out, indent=2, ensure_ascii=False), encoding="utf-8")
    out_path.with_suffix(".meta.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[saved] {len(cookies_out)} cookies -> {out_path}", flush=True)
    print(f"[saved] metadata -> {out_path.with_suffix('.meta.json')}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
