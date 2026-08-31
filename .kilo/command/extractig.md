---
description: "Full Instagram profile distillation pipeline: diff asset pool, scrape all pending codes via Playwright, transcribe (caption-first), classify per-theme, merge into manifest, and produce profile-level synthesis / voice profile."
agent: code
subtask: false
---

# /extractig [instagram-handle]

Consolidates the full extraction pipeline (`diff_assets.py` → `pipeline_loop.py` → `distill_loop.py` → `merge_manifest.py`) into a single callable command, then writes a profile-level synthesis at `knowledge/uilg-voice-profile.md` with an updated manifest.

## Inputs

- `$1` — Instagram handle (e.g., `ultimateivyleagueguide`). Must match a username entry in `posts_index.json`. If the handle is different, adjust the `username` field first or provide the updated index path.
- `$2` (optional) — output theme file override (`knowledge/<override>.md`). Default: updates all 9 theme files.

## Steps (automatic — no user interaction needed beyond initial call)

1. **Compute delta.** `python diff_assets.py` compares `posts_index.json` against `mentor/transcripts/` and `manifest.json`, writes `pending_codes.json`. Reports pool size, covered, pending count by `product_type`.

2. **Refresh cookies.** `python harvest_ig_cookies.py --ig-handle $1` captures current login state into `cookies.json` + `.meta.json`. If `logged_in` is false, exits with clear instruction: the user must open a headful Chrome session and log in manually first.

3. **Launch resumable scrape loop.** `python pipeline_loop.py` reads `pending_codes.json`. Per item:
   - Navigates `https://www.instagram.com/reel/<code>/` (falls back to `/p/<code>/`).
   - Captures `og:description`, visible caption, page meta (`og:title`, `twitter:title`).
   - Writes `mentor/transcripts/<code>.md` (YAML frontmatter: `code`, `date`, `themes`; sections `## Caption`, `## Page meta`).
   - Resumes from `pipeline_state.json` (skips `done_codes`, skips `failed_codes` with >=3 attempts). Reports `[i/N] code -> done | done=N failed=0` every 10 items.

4. **Batch-distill.** `python distill_loop.py` reads pipeline state, classifies each new transcript against the 9-theme keyword rubric (`essays`, `activities`, `timeline`, `school_list`, `interviews`, `testing`, `recommendations`, `myths_mindset`, `study_skills`, `cross_cutting`), writes `manifest_delta.json`, and appends synthesized entries to the 9 KB files in `mentor/knowledge/`. Deduplicates via `already_in_kb()` hash check.

5. **Profile synthesis.** The loop also writes `knowledge/uilg-voice-profile.md` (only updated, not overwritten) summarizing: recurring frameworks (PPF, Three Tiers, Six-step PS build, ED three-step), hook formulas (ALL-CAPS `How to X 📝`, `7 X` list, `Comment [KEYWORD]` close), credibility loops (zero rejections / Harvard / Forbes / millions guided), and anti-pattern blacklist (`"my passion"`, `"since I was a child"`, `"looking back"`, `"make a difference"`, `"follow your dreams"`, `"if I could go back"`). References `PS-theme-outline.md` for the locked theme (`The 5% Gap`) and notes how UILG's templates must be actively avoided when drafting.

6. **Merge manifest.** `python merge_manifest.py` merges `manifest_delta.json` into `manifest.json` (with `manifest.json.bak`), updates `theme_coverage`, `selected`, `merged_at`, `merge_added`. Reports final counts.

7. **Validate.** `python validate.py` checks: transcript codes exist in `posts_index.json`, done codes have `.md` files, pending codes are covered, theme_coverage sums match, and no orphan `.FAILED.json` files without transcripts.

8. **Clean up.** After successful run: `__pycache__/` removed, `cookies.json`/`.meta.json` kept (useful for the next run, not a risk), `pending_codes.json` and `pipeline_state.json` removed (regeneratable), `manifest_delta.json` removed (merged). `.gitignore` already covers `/pipeline_state.json`, `/pending_codes.json`, `/manifest_delta.json`, `/cookies.json`, `/cookies.meta.json`, `/chrome_profile`, `__pycache__/`, `.playwright-mcp/`, `.kilo/node_modules/`, per-code download dirs (`/[A-Za-z][A-Za-z0-9_-]{8,16}/` with `!/mentor/` exclusion).

## Exit codes

- `0` — full success. `pipeline_state.json` reports `done=N failed=0`, `validate.py` reports `[OK]`, manifest at `907` items (or whatever sum), and `knowledge/uilg-voice-profile.md` + updated KB files exist.
- `2` — cookie/login failure. The user must open a persistent Chrome session at `https://www.instagram.com/$1/` and confirm `cookies.meta.json` shows `logged_in=true`.
- `1` — structural failure (missing input files, corrupt manifest, or persistent error rate >10% of codes — which indicates upstream IG rate-limiting or a session wall).

## Files the user should keep

- `mentor/transcripts/*.md` (1043 items) — searchable index of the profile.
- `mentor/knowledge/*.md` (9 curated KB files + `uilg-voice-profile.md`) — signal only.
- `manifest.json` (merged, 907 items) — index.
- `.gitignore` (expanded to cover all noise sources) — prevents accidental commits.

Files the user can safely delete between runs: `pending_codes.json`, `pipeline_state.json`, `manifest_delta.json`, `__pycache__/`, `.kilo/node_modules/` (covered by `.kilo/.gitignore`), any leftover per-code video dirs (covered by `.gitignore` pattern), `chrome_profile` (security-sensitive junction, must never be recreated inside workspace — `pipeline_loop.py` uses `%TEMP%/uilg_chrome_profile` by default).
