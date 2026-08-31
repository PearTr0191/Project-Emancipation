"""pipeline_loop.py — Resumable caption-first distillation loop for UILG.

UILG content is text-on-screen-first. The caption + og:description + slide
text are the primary signal. This loop navigates each pending post, captures
all available text, and writes mentor/transcripts/<code>.md. No video download,
no STT — headless Chrome cannot reach IG's authenticated video blob URLs.

Resumable: writes pipeline_state.json after every item.
"""
from __future__ import annotations

import json
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
STATE_PATH = ROOT / "pipeline_state.json"
PENDING_PATH = ROOT / "pending_codes.json"

# Chrome persistent context for Playwright. Default: system temp, so we
# never drop a junction inside the workspace (which would expose the user's
# Chrome profile to the project tree / git). Override with UILG_CHROME_PROFILE.
CHROME_PROFILE = Path(
    __import__("os").environ.get(
        "UILG_CHROME_PROFILE",
        str(Path(__import__("tempfile").gettempdir()) / "uilg_chrome_profile"),
    )
)

PROGRESS_EVERY = int(__import__("os").environ.get("UILG_PROGRESS_EVERY", "10"))
NAV_TIMEOUT_MS = 45_000

TRANSIENT_TOKENS = (
    "TimeoutError", "ERR_NETWORK", "ERR_CONNECTION", "ERR_ABORTED",
    "429", "502", "503", "504", "rate limit", "checkpoint", "Please wait",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"done_codes": [], "failed_codes": {}, "last_processed_at": None}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def load_pending() -> list[str]:
    if not PENDING_PATH.exists():
        sys.exit(f"missing {PENDING_PATH}")
    return json.loads(PENDING_PATH.read_text(encoding="utf-8"))["pending_codes"]


def already_transcribed(code: str) -> bool:
    p = TRANSCRIPTS_DIR / f"{code}.md"
    if not p.exists():
        return False
    head = p.read_text(encoding="utf-8", errors="replace")[:600]
    return "code:" in head and ("## Caption" in head or "## Transcript" in head)


# ---------- Extraction ----------

EXTRACT_JS = r"""() => {
    const meta = (prop) => {
        const el = document.querySelector(`meta[property="${prop}"]`) ||
                    document.querySelector(`meta[name="${prop}"]`);
        return el ? el.getAttribute('content') : null;
    };
    // Collect visible text inside the article main column as a fallback caption
    const main = document.querySelector('article, main, [role="main"]');
    const visibleText = main ? main.innerText.slice(0, 8000) : '';
    // Try to grab JSON-LD description
    let jsonld = null;
    try {
        for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
            const j = JSON.parse(s.textContent);
            if (j && (j.description || j.articleBody)) {
                jsonld = j.description || j.articleBody;
                break;
            }
        }
    } catch {}
    return {
        ogTitle: meta('og:title'),
        ogDesc: meta('og:description'),
        ogImage: meta('og:image'),
        twitterTitle: meta('twitter:title'),
        twitterDesc: meta('twitter:description'),
        desc: meta('description'),
        jsonld,
        visibleText,
        title: document.title,
    };
}"""


def fetch_post(page, code: str) -> dict:
    """Navigate to /reel/<code>/ (fallback /p/<code>/) and return text signal."""
    for path in ("reel", "p"):
        url = f"https://www.instagram.com/{path}/{code}/"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
            time.sleep(1.5)
            return page.evaluate(EXTRACT_JS)
        except Exception:
            continue
    raise RuntimeError(f"navigation failed for {code}")


def pick_caption(record: dict, info: dict) -> str:
    """Choose the longest available caption source. Prefers posts_index caption
    (it has the full text) and falls back to og:description / visibleText."""
    candidates = [
        record.get("caption") or "",
        info.get("ogDesc") or "",
        info.get("desc") or "",
        info.get("jsonld") or "",
    ]
    return max(candidates, key=len)


# ---------- Markdown writer ----------

def build_transcript_md(code: str, taken_at: int, caption: str,
                        product_type: str, info: dict) -> str:
    date = datetime.fromtimestamp(taken_at, tz=timezone.utc).strftime("%Y-%m-%d")
    cap = caption.strip() or "(no caption captured)"
    front = f"---\ncode: {code}\ndate: {date}\nthemes: \n---\n\n"
    cap_block = f"## Caption\n\n{cap}\n\n"
    meta_lines = []
    if info.get("ogTitle"):
        meta_lines.append(f"- og:title: {info['ogTitle'][:200]}")
    if info.get("twitterTitle"):
        meta_lines.append(f"- twitter:title: {info['twitterTitle'][:200]}")
    meta_block = "## Page meta\n\n" + ("\n".join(meta_lines) if meta_lines else "(none)") + "\n\n"
    source = (f"*Source: ultimateivyleagueguide {product_type} {code}, posted {date}. "
              f"Caption-first extraction (headless browser).*\n")
    return front + cap_block + meta_block + source


# ---------- Per-code worker ----------

def process_code(page, code: str, record: dict, state: dict) -> str:
    if already_transcribed(code):
        state["done_codes"].append(code)
        return "skipped"
    if code in state["failed_codes"] and state["failed_codes"][code].get("attempts", 0) >= 3:
        return "skipped"

    attempts = state["failed_codes"].get(code, {}).get("attempts", 0)
    product_type = record.get("product_type") or "feed"
    taken_at = record.get("taken_at") or int(time.time())
    md_path = TRANSCRIPTS_DIR / f"{code}.md"

    try:
        info = fetch_post(page, code)
        caption = pick_caption(record, info)
        md = build_transcript_md(code, taken_at, caption, product_type, info)
        md_path.write_text(md, encoding="utf-8")
        state["done_codes"].append(code)
        state["failed_codes"].pop(code, None)
        return "done"
    except Exception as exc:
        attempts += 1
        state["failed_codes"][code] = {
            "error": f"{type(exc).__name__}: {exc}"[:500],
            "attempts": attempts,
            "last_try": now_iso(),
        }
        msg = f"{type(exc).__name__}: {exc}"
        if any(tok in msg for tok in TRANSIENT_TOKENS) and attempts < 3:
            time.sleep(min(2 ** attempts, 30))
        return "failed"


# ---------- Main loop ----------

def main() -> int:
    state = load_state()
    pending = load_pending()
    pool = {r["code"]: r for r in json.loads((ROOT / "posts_index.json").read_text(encoding="utf-8"))["records"]}
    remaining = [c for c in pending if c not in set(state["done_codes"])]
    print(f"[start] pending={len(pending)} already_done={len(state['done_codes'])} remaining={len(remaining)}", flush=True)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        CHROME_PROFILE.mkdir(parents=True, exist_ok=True)
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(CHROME_PROFILE),
            headless=True,
            channel="chrome",
            args=["--no-first-run", "--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 800},
        )
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto("https://www.instagram.com/ultimateivyleagueguide/", wait_until="domcontentloaded", timeout=45000)
            time.sleep(2)
            print(f"[login-check] url={page.url} title={page.title()[:60]!r}", flush=True)

            consecutive_failures = 0
            for i, code in enumerate(remaining, 1):
                record = pool.get(code, {"code": code, "product_type": "unknown", "caption": ""})
                result = process_code(page, code, record, state)
                if i % PROGRESS_EVERY == 0 or result == "failed":
                    state["last_processed_at"] = now_iso()
                    save_state(state)
                    print(f"[{i}/{len(remaining)}] {code} -> {result} | done={len(state['done_codes'])} failed={len(state['failed_codes'])}", flush=True)
                if result == "done":
                    consecutive_failures = 0
                    time.sleep(0.4)
                elif result == "failed":
                    consecutive_failures += 1
                    if consecutive_failures >= 25:
                        print(f"[abort] {consecutive_failures} consecutive failures — likely rate-limited or session expired", flush=True)
                        break
        finally:
            ctx.close()

    save_state(state)
    print(f"[done] total_done={len(state['done_codes'])} total_failed={len(state['failed_codes'])}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
