"""ivybrothers_pipeline.py — IG extraction pipeline for @ivybrothersofficial.

Mirrors the UILG treatment (2026-08-31) with one upgrade: this account's
content is text-on-image carousels, so Phase B extracts every carousel slide
image (full-res) in addition to captions. Headless Chrome + injected cookie
session (same pattern as harvest_ig_cookies.py / pipeline_loop.py).

Phases:
  --phase index    scroll-crawl profile grid + reels tab -> posts_index_ivybrothers.json
  --phase extract  per-post DOM extraction + slide downloads -> transcripts + assets
  --phase all      index then extract

Resumable: checkpoints after every item. No video download / STT —
headless Chrome cannot reach IG's authenticated video blob URLs (proven 2026-08-31).

Login walls: detected per post; the loop aborts immediately and reports, per
the UILG plan §5 (surface to user, never retry blindly).
"""
from __future__ import annotations

import json
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except (AttributeError, OSError):
    pass

ROOT = Path(r"D:\Project Emancipation")
TRANSCRIPTS_DIR = ROOT / "mentor" / "transcripts"
ASSETS_DIR = ROOT / "ivybrothers_assets"
STATE_PATH = ROOT / "ib_state.json"
INDEX_PATH = ROOT / "posts_index_ivybrothers.json"
COOKIES_PATH = ROOT / "cookies.json"

HANDLE = "ivybrothersofficial"

CHROME_PROFILE = Path(
    __import__("os").environ.get(
        "IB_CHROME_PROFILE",
        str(Path(__import__("tempfile").gettempdir()) / "ib_chrome_profile"),
    )
)

NAV_TIMEOUT_MS = 45_000
MAX_SCROLL_ITER = 400
STAGNANT_LIMIT = 10
MIN_SCROLL_ITER = 30
MAX_ATTEMPTS = 3
ABORT_CONSECUTIVE = 25
PROGRESS_EVERY = 5

# Rate-limit pacing. 440 post-views at ~4-6s cadence triggered IG's per-session
# 429 block on 2026-09-21 (~14 views/min for 30 min straight). Remaining posts
# run with randomized pauses + a periodic burst cooldown. Env-overridable.
PAUSE_MIN = float(__import__("os").environ.get("IB_PAUSE_MIN", "3.0"))
PAUSE_MAX = float(__import__("os").environ.get("IB_PAUSE_MAX", "6.0"))
BURST_EVERY = int(__import__("os").environ.get("IB_BURST_EVERY", "30"))
BURST_PAUSE = float(__import__("os").environ.get("IB_BURST_PAUSE", "45"))

# Rate-limit ride mode: IB_BLOCK_MODE=ride waits out the 429 window (backing
# off 60s->300s, retrying the same code after each backoff) instead of
# aborting, capped at IB_BLOCK_RIDE_CAP seconds of total ride time. Default
# abort matches the UILG plan §5; ride is for a known-active block with the
# PC going down soon.
BLOCK_MODE = __import__("os").environ.get("IB_BLOCK_MODE", "abort")
BLOCK_RIDE_CAP = float(__import__("os").environ.get("IB_BLOCK_RIDE_CAP", "3600"))

TRANSIENT_TOKENS = (
    "TimeoutError", "ERR_NETWORK", "ERR_CONNECTION", "ERR_ABORTED",
    "429", "502", "503", "504", "rate limit", "checkpoint", "Please wait",
)
LOGIN_WALL_TOKENS = ("login wall", "accounts/login", "Log in to Instagram")

TS_RE = re.compile(
    r"^(?:[A-Z][a-z]+ \d{1,2}, \d{4}"
    r"|\d+\s?(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?)(?: ago)?"
    r"|Edited)$"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"done_codes": [], "failed_codes": {}, "last_processed_at": None, "login_wall_hit": False}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def already_transcribed(code: str) -> bool:
    p = TRANSCRIPTS_DIR / f"{code}.md"
    if not p.exists():
        return False
    head = p.read_text(encoding="utf-8", errors="replace")[:600]
    return "code:" in head and ("## Caption" in head or "## Transcript" in head)


# ---------- Phase A: index crawl ----------

COLLECT_HREFS_JS = r"""() => {
    const out = [];
    const seen = new Set();
    // Scope to the profile's own tiles: hrefs are username-prefixed
    // (/ivybrothersofficial/p/<code>/, /ivybrothersofficial/reel/<code>/).
    // Bare /p/ and /reel/ links belong to right-rail suggested content
    // from OTHER accounts — those contaminated the first crawl (325 junk reels).
    for (const a of document.querySelectorAll('a[href]')) {
        const href = a.getAttribute('href') || '';
        const m = href.match(/\/ivybrothersofficial\/(?:p|reel)\/([A-Za-z0-9_-]{5,})\/?/);
        if (!m) continue;
        const code = m[1];
        if (seen.has(code)) continue;
        seen.add(code);
        const kind = href.includes('/reel/') ? 'reel' : 'p';
        const img = a.querySelector('img');
        const alt = img ? (img.alt || '') : '';
        const isCarousel = /carousel/i.test(alt) ||
            !!a.querySelector('[aria-label*="Carousel" i]');
        out.push({ code: code, kind: kind, alt: alt.slice(0, 300), carousel_badge: isCarousel });
    }
    return out;
}"""

PROFILE_META_JS = r"""() => {
    const txt = document.body ? document.body.innerText.slice(0, 4000) : '';
    return { bio: txt, title: document.title };
}"""


def save_index(records: dict, profile_meta: dict | None) -> None:
    out = {
        "username": HANDLE,
        "scraped_at": now_iso(),
        "pool_size": len(records),
        "profile_meta": profile_meta or {},
        "records": list(records.values()),
    }
    INDEX_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")


def crawl_surface(page, url: str, label: str, seen: dict, profile_meta: dict | None) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
    time.sleep(2.0)
    if label == "grid":
        try:
            profile_meta.update(page.evaluate(PROFILE_META_JS) or {})
        except Exception:
            pass
    stagnant = 0
    for i in range(MAX_SCROLL_ITER):
        found = page.evaluate(COLLECT_HREFS_JS)
        new = 0
        for rec in found:
            if rec["code"] not in seen:
                seen[rec["code"]] = rec
                new += 1
        stagnant = 0 if new else stagnant + 1
        if i % 20 == 0:
            save_index(seen, profile_meta)
            print(f"[{label}] iter={i} codes={len(seen)}", flush=True)
        if stagnant >= STAGNANT_LIMIT and i >= MIN_SCROLL_ITER:
            break
        page.evaluate("() => window.scrollBy(0, window.innerHeight * 3)")
        time.sleep(0.7)
    save_index(seen, profile_meta)
    print(f"[{label}] finished codes={len(seen)}", flush=True)


def phase_index(page) -> dict:
    seen: dict = {}
    profile_meta: dict = {}
    crawl_surface(page, f"https://www.instagram.com/{HANDLE}/", "grid", seen, profile_meta)
    crawl_surface(page, f"https://www.instagram.com/{HANDLE}/reels/", "reels", seen, profile_meta)
    save_index(seen, profile_meta)
    by_kind: dict = {}
    for rec in seen.values():
        by_kind[rec.get("kind") or "p"] = by_kind.get(rec.get("kind") or "p", 0) + 1
    print(f"[index] done pool={len(seen)} by_kind={by_kind}", flush=True)
    return {"pool": len(seen), "by_kind": by_kind}


# ---------- Phase B: per-post extraction ----------

CAPTION_JS = r"""() => {
    const meta = (prop) => {
        const el = document.querySelector(`meta[property="${prop}"]`) ||
                    document.querySelector(`meta[name="${prop}"]`);
        return el ? el.getAttribute('content') : null;
    };
    let jsonld = null;
    try {
        for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
            const j = JSON.parse(s.textContent);
            if (j && (j.description || j.articleBody)) { jsonld = j.description || j.articleBody; break; }
        }
    } catch {}
    const article = document.querySelector('article') || document.querySelector('main');
    const inner = article ? article.innerText.slice(0, 12000) : '';
    const moreBtn = article ? Array.from(article.querySelectorAll('button, span, div[role="button"]'))
        .find(el => /^(more|…\s*more)$/i.test((el.textContent || '').trim())) : null;
    if (moreBtn) { try { moreBtn.click(); } catch {} }
    return { ogTitle: meta('og:title'), ogDesc: meta('og:description'), jsonld: jsonld, inner: inner };
}"""

INNER_JS = r"""() => {
    const article = document.querySelector('article') || document.querySelector('main');
    return { inner: article ? article.innerText.slice(0, 12000) : '' };
}"""

SLIDE_IMGS_JS = r"""() => {
    const out = [];
    const seen = new Set();
    for (const img of document.querySelectorAll('article img, main img')) {
        const w = img.naturalWidth || 0;
        if (w < 400) continue;
        const alt = img.alt || '';
        if (/profile picture/i.test(alt)) continue;
        if (alt && !alt.startsWith('Photo by')) continue;
        let best = img.currentSrc || img.src || '';
        try {
            const parts = (img.srcset || '').split(',').map(s => s.trim()).filter(Boolean)
                .map(s => { const kv = s.split(/\s+/); return { u: kv[0], w: kv[1] && kv[1].endsWith('w') ? parseInt(kv[1]) : 0 }; });
            if (parts.length) best = parts.reduce((a, b) => (b.w > a.w ? b : a)).u;
        } catch {}
        if (!best || seen.has(best)) continue;
        seen.add(best);
        out.push({ url: best, alt: alt.slice(0, 300), w: w, h: img.naturalHeight || 0 });
    }
    return out;
}"""

HAS_NEXT_JS = r"""() => {
    const btns = Array.from(document.querySelectorAll('button[aria-label], [role="button"]'));
    return btns.some(x => /^(next|go forward)$/i.test(x.getAttribute('aria-label') || ''));
}"""

CLICK_NEXT_JS = r"""() => {
    const btns = Array.from(document.querySelectorAll('button[aria-label], [role="button"]'));
    const b = btns.find(x => /^(next|go forward)$/i.test(x.getAttribute('aria-label') || ''));
    if (b) { b.click(); return true; }
    return false;
}"""


def harvest_slides(page, slides: dict) -> int:
    found = page.evaluate(SLIDE_IMGS_JS)
    new = 0
    for rec in found:
        if rec["url"] not in slides:
            slides[rec["url"]] = rec
            new += 1
    return new


def collect_slides(page) -> list:
    slides: dict = {}
    harvest_slides(page, slides)
    for _ in range(30):
        if not page.evaluate(HAS_NEXT_JS):
            break
        page.evaluate(CLICK_NEXT_JS)
        time.sleep(0.35)
        if harvest_slides(page, slides) == 0:
            time.sleep(0.35)
            if harvest_slides(page, slides) == 0:
                break
    return list(slides.values())


def parse_caption_block(inner: str, handle: str) -> str:
    lines = [ln.strip() for ln in inner.splitlines()]
    start = None
    for i, ln in enumerate(lines):
        if ln == handle:
            start = i
            break
    if start is None:
        return ""
    end = None
    for i in range(start + 1, len(lines)):
        ln = lines[i]
        if TS_RE.match(ln):
            end = i
            break
        if ln in ("Add a comment", "Follow", "Message", "View all comments"):
            end = i
            break
    if end is None:
        end = min(len(lines), start + 40)
    block = [ln for ln in lines[start + 1:end]]
    while block and not block[-1]:
        block.pop()
    return "\n".join(block).strip()


def pick_caption(info: dict, inner2: str, handle: str) -> str:
    candidates = [
        info.get("jsonld") or "",
        parse_caption_block(inner2 or "", handle),
        parse_caption_block(info.get("inner") or "", handle),
        info.get("ogDesc") or "",
    ]
    return max(candidates, key=len)


def download_slide(page, url: str, path: Path) -> bool:
    try:
        resp = page.context.request.get(url, timeout=30_000, headers={"referer": "https://www.instagram.com/"})
        if resp.status == 200:
            body = resp.body()
            if body and len(body) > 1024:
                path.write_bytes(body)
                return True
    except Exception:
        pass
    try:
        b64 = page.evaluate(
            r"""async (u) => {
                const r = await fetch(u, {credentials: 'include'});
                if (!r.ok) return null;
                const buf = await r.arrayBuffer();
                const bytes = new Uint8Array(buf);
                let binary = '';
                const chunk = 0x8000;
                for (let i = 0; i < bytes.length; i += chunk) {
                    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
                }
                return btoa(binary);
            }""",
            url,
        )
        if b64:
            import base64
            raw = base64.b64decode(b64)
            if len(raw) > 1024:
                path.write_bytes(raw)
                return True
    except Exception:
        pass
    return False


def build_transcript_md(code: str, taken_at: int, caption: str, kind: str,
                        slides: list, info: dict, failed_downloads: int) -> str:
    date = datetime.fromtimestamp(taken_at, tz=timezone.utc).strftime("%Y-%m-%d")
    cap = caption.strip() or "(no caption captured)"
    front = f"---\ncode: {code}\ndate: {date}\nhandle: {HANDLE}\nthemes: \n---\n\n"
    cap_block = f"## Caption\n\n{cap}\n\n"
    slide_lines = []
    for i, s in enumerate(sorted(slides, key=lambda x: -(x.get("w") or 0)), 1):
        rel = f"ivybrothers_assets/{code}/slide_{i:02d}.jpg"
        dims = f"{s.get('w') or '?'}x{s.get('h') or '?'}"
        alt = f" | alt: {s['alt']}" if s.get("alt") else ""
        slide_lines.append(f"- {rel} ({dims}){alt}")
    slides_block = "## Slides\n\n" + ("\n".join(slide_lines) if slide_lines else "(none captured)") + "\n\n"
    if failed_downloads:
        slides_block += f"*Note: {failed_downloads} slide URL(s) collected but download failed.*\n\n"
    meta_lines = []
    if info.get("ogTitle"):
        meta_lines.append(f"- og:title: {info['ogTitle'][:200]}")
    if info.get("ogDesc"):
        meta_lines.append(f"- og:description: {info['ogDesc'][:400]}")
    meta_block = "## Page meta\n\n" + ("\n".join(meta_lines) if meta_lines else "(none)") + "\n\n"
    source = (f"*Source: {HANDLE} {kind} {code}, posted {date}. "
              f"DOM extraction (headless browser, cookie session). No video/STT.*\n")
    return front + cap_block + slides_block + meta_block + source


def process_code(page, code: str, record: dict, state: dict) -> str:
    if already_transcribed(code):
        state["done_codes"].append(code)
        return "skipped"
    attempts = state["failed_codes"].get(code, {}).get("attempts", 0)
    if attempts >= MAX_ATTEMPTS:
        return "skipped"

    kind = record.get("kind") or "p"
    alt = record.get("alt") or ""
    for path in ("p", "reel"):
        url = f"https://www.instagram.com/{path}/{code}/"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
            time.sleep(1.4)
            if "/accounts/login" in page.url or "log in" in page.title().lower():
                raise RuntimeError(f"login wall at {url}")
            break
        except RuntimeError as exc:
            if "login wall" in str(exc):
                raise
            continue
        except Exception:
            # Playwright raises its own Error type for navigation failures
            # (net::ERR_HTTP_RESPONSE_CODE_FAILURE, timeouts, etc.) — try the
            # fallback path instead of crashing the loop (crashed at 440/668
            # on 2026-09-21 before this fix).
            continue
    else:
        raise RuntimeError(f"navigation failed for {code}")

    try:
        info = page.evaluate(CAPTION_JS) or {}
        time.sleep(0.35)
        inner2 = (page.evaluate(INNER_JS) or {}).get("inner") or ""
        caption = pick_caption(info, inner2, HANDLE)
        slides = collect_slides(page)
        code_dir = ASSETS_DIR / code
        code_dir.mkdir(parents=True, exist_ok=True)
        failed_downloads = 0
        for i, s in enumerate(sorted(slides, key=lambda x: -(x.get("w") or 0)), 1):
            if not download_slide(page, s["url"], code_dir / f"slide_{i:02d}.jpg"):
                failed_downloads += 1
        taken_at = int(time.time())
        ts_match = re.search(r"[A-Z][a-z]+ \d{1,2}, \d{4}", inner2 or "") or re.search(r"[A-Z][a-z]+ \d{1,2}, \d{4}", info.get("ogDesc") or "")
        if ts_match:
            try:
                taken_at = int(datetime.strptime(ts_match.group(0), "%B %d, %Y").replace(tzinfo=timezone.utc).timestamp())
            except ValueError:
                pass
        md = build_transcript_md(code, taken_at, caption, kind, slides, info, failed_downloads)
        (TRANSCRIPTS_DIR / f"{code}.md").write_text(md, encoding="utf-8")
        state["done_codes"].append(code)
        state["failed_codes"].pop(code, None)
        return "done"
    except RuntimeError as exc:
        if "login wall" in str(exc):
            raise
        attempts += 1
        state["failed_codes"][code] = {"error": f"{type(exc).__name__}: {exc}"[:500], "attempts": attempts, "last_try": now_iso()}
        return "failed"
    except Exception as exc:
        attempts += 1
        state["failed_codes"][code] = {"error": f"{type(exc).__name__}: {exc}"[:500], "attempts": attempts, "last_try": now_iso()}
        msg = f"{type(exc).__name__}: {exc}"
        if any(tok in msg for tok in TRANSIENT_TOKENS) and attempts < MAX_ATTEMPTS:
            time.sleep(min(2 ** attempts, 30))
        return "failed"


def ride_gate(consecutive_failures: int, ride_start: float | None) -> tuple[float | None, bool, float]:
    """Rate-limit ride decision: returns (updated_ride_start, should_abort, backoff_seconds)."""
    if ride_start is None:
        ride_start = time.time()
    elapsed = time.time() - ride_start
    if elapsed >= BLOCK_RIDE_CAP:
        return ride_start, True, 0.0
    return ride_start, False, min(60 * (consecutive_failures - ABORT_CONSECUTIVE + 1), 300)


def phase_extract(page) -> int:
    state = load_state()
    if not INDEX_PATH.exists():
        sys.exit(f"missing {INDEX_PATH} — run --phase index first")
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    records = {r["code"]: r for r in index["records"]}
    remaining = [c for c in records if c not in set(state["done_codes"])]
    total = len(remaining)
    print(f"[extract] pool={len(records)} already_done={len(state['done_codes'])} remaining={total}", flush=True)

    consecutive_failures = 0
    ride_start: float | None = None
    i = 0
    while i < total:
        code = remaining[i]
        try:
            result = process_code(page, code, records[code], state)
        except RuntimeError as exc:
            if "login wall" in str(exc):
                state["login_wall_hit"] = True
                print(f"[abort] login wall detected at {code} — stopping loop, surface to user", flush=True)
                break
            result = "failed"
        except Exception:
            result = "failed"

        if result == "skipped":
            i += 1
            save_state(state)
            continue

        if result == "done":
            consecutive_failures = 0
            i += 1
            save_state(state)
            print(f"[{i}/{total}] {code} -> done | total_done={len(state['done_codes'])}", flush=True)
            if i % BURST_EVERY == 0:
                print(f"[burst] cooldown {BURST_PAUSE}s after {i} items", flush=True)
                time.sleep(BURST_PAUSE)
            else:
                time.sleep(random.uniform(PAUSE_MIN, PAUSE_MAX))
            continue

        consecutive_failures += 1
        state["last_processed_at"] = now_iso()
        save_state(state)
        print(f"[{i}/{total}] {code} -> failed ({consecutive_failures} consecutive)", flush=True)
        if consecutive_failures >= ABORT_CONSECUTIVE and BLOCK_MODE == "ride":
            ride_start, should_abort, backoff = ride_gate(consecutive_failures, ride_start)
            if should_abort:
                print(f"[abort] block ride cap {BLOCK_RIDE_CAP:.0f}s exceeded — stopping", flush=True)
                break
            print(f"[ride] 429 block active — backing off {backoff:.0f}s (elapsed {time.time() - ride_start:.0f}/{BLOCK_RIDE_CAP:.0f}s)", flush=True)
            time.sleep(backoff)
            try:
                result = process_code(page, code, records[code], state)
            except RuntimeError as exc:
                if "login wall" in str(exc):
                    state["login_wall_hit"] = True
                    print(f"[abort] login wall detected at {code} — stopping loop", flush=True)
                    break
                result = "failed"
            except Exception:
                result = "failed"
            if result == "done":
                consecutive_failures = 0
                i += 1
                save_state(state)
                print(f"[{i}/{total}] {code} -> done (after ride)", flush=True)
                continue
        elif consecutive_failures >= ABORT_CONSECUTIVE:
            print(f"[abort] {consecutive_failures} consecutive failures — likely rate-limited or session expired", flush=True)
            break
        i += 1

    save_state(state)
    print(f"[extract] finished total_done={len(state['done_codes'])} total_failed={len(state['failed_codes'])}", flush=True)
    return 0


def launch_browser(p):
    CHROME_PROFILE.mkdir(parents=True, exist_ok=True)
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(CHROME_PROFILE),
        headless=True,
        channel="chrome",
        args=["--no-first-run", "--no-default-browser-check", "--disable-blink-features=AutomationControlled"],
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True,
    )
    if COOKIES_PATH.exists():
        cookies = json.loads(COOKIES_PATH.read_text(encoding="utf-8"))
        for c in cookies:
            c.setdefault("sameSite", "Lax")
        ctx.add_cookies(cookies)
        print(f"[cookies] injected {len(cookies)} cookies", flush=True)
    else:
        print("[cookies] WARNING: cookies.json missing — running logged-out", flush=True)
    return ctx


def main() -> int:
    phase = sys.argv[sys.argv.index("--phase") + 1] if "--phase" in sys.argv else "all"
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        ctx = launch_browser(p)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            if phase in ("index", "all"):
                summary = phase_index(page)
                if phase == "index":
                    print(f"[stop] index-only run complete: {summary}", flush=True)
                    return 0
            if phase in ("extract", "all"):
                return phase_extract(page)
            sys.exit(f"unknown phase: {phase}")
        finally:
            ctx.close()


if __name__ == "__main__":
    sys.exit(main())
