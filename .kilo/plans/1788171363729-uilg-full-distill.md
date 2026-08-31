# Plan: Full distillation of @ultimateivyleagueguide Instagram profile

**Date:** 2026-08-31
**Owner:** Implementation agent (Kilo, non-plan mode)
**Goal:** Distill the *entire* profile (1044 posts in pool, ~851 currently unprocessed) into the existing 9-theme knowledge base so no insight from the source account is left on the floor for the student's PS, supplements, and recommender strategy.

---

## 1. Current state (what already exists)

| Asset | Count / Size | Status |
|---|---|---|
| `posts_index.json` | 1044 records (full pool, captions + meta) | Already scraped 2026-08-25 |
| `manifest.json` | 72 selected posts (high-score / thematic) | Already distilled |
| `new_candidates.json` | 121 candidate posts (recent-cycle) | Awaiting deeper distillation |
| `mentor/transcripts/` | ~80 transcripts already on disk | Mix of `ultimateivyleagueguide` (UILG) and `ivy_roadmap` |
| `mentor/knowledge/` | 9-theme KB (essays, timeline, activities, school_list, interviews, testing, recommendations, myths_mindset, study_skills) | Built from the 193 already-processed items |
| Pipeline scripts | `harvest_ig_cookies.py`, `debug_scroll*.py`, `debug_reel_video.py`, `probe_range.py` | Working from prior sessions |
| **Delta to extract** | ~851 reels/posts (1044 − 72 − 121) | **The work** |

Theme-coverage gap today (from `manifest.json`): essays 55, timeline 39, activities 32, school_list **3**, interviews 11, testing 67, recommendations **2**, myths_mindset 41, study_skills 51. The two thin themes (school_list, recommendations) are the obvious distillation targets once the full profile is processed.

---

## 2. Scope decisions

- **In scope:** scrape + transcribe + distill all UILG posts/reels in `posts_index.json` that are not already in `mentor/transcripts/` or `manifest.json`.
- **Out of scope:**
  - Re-scraping the already-transcribed reels (no value in re-running OCR/STT).
  - The `ivy_roadmap` channel — only UILG is in scope here.
  - Resolving the PS theme ("The 5% Gap" already locked). This plan only feeds the KB; the PS drafting week stays Sep 1–7.
  - Building new scraper infra — we extend existing scripts.

---

## 3. Approach (one continuous pipeline)

```
posts_index.json (1044)
   └─ filter: code ∉ transcripts/ ∉ manifest.selected
   └─ partition by product_type:
        clips/reel        → video URL → ffmpeg/STT → transcript md
        carousel/image    → caption + OCR (slide text via existing debug_reel_video heuristics adapted for carousels)
   └─ per item: write mentor/transcripts/<code>.md (existing schema)
   └─ per item: append scoring/themes entry to a NEW manifest_delta.json
   └─ batch-distill all newly-transcribed items into the 9-theme knowledge files
   └─ re-merge manifest.json + manifest_delta.json → single source of truth
```

### 3.1 Pre-flight (do first, once)

1. **Diff existing assets.** Write a one-shot script `diff_assets.py` that:
   - Loads `posts_index.json`, `manifest.json`, lists every `code` in `mentor/transcripts/*.md` (parse first heading).
   - Emits `pending_codes.json` — the ~851 codes we still owe.
   - Splits pending set by `product_type`: `clips` vs `carousel_container` vs others. Reports counts.
   - **Exit criterion:** pending set is concrete and saved before any scraping begins.

2. **Cookie sanity check.** Run `harvest_ig_cookies.py` and confirm `cookies.json` + `cookies.meta.json` show `logged_in=true`. If stale, run the helper to refresh.

### 3.2 Scrape loop (the bulk work)

3. **Reel/video scraping.** For each `clips` code in `pending_codes.json`:
   - Use the existing Playwright persistent-context pattern from `debug_reel_video.py` to navigate `https://www.instagram.com/reel/<code>/`.
   - Capture `og:video` URL (`page.evaluate` block already in `debug_reel_video.py`).
   - Download with a streaming HTTP client, `Range: bytes=0-` (proven via `probe_range.py`) to handle >2 GB reels.
   - Save to `D:\Project Emancipation\<code>\` (mirror existing `<Db3rLZcO96f>\` layout).
   - Verify file integrity (size > 0; `ffprobe` if moov atom missing).
   - Extract audio → `whisper` (or existing faster-whisper pipeline if present in repo, else fall back to `ffmpeg` + `whisper` CLI).
   - Write `mentor/transcripts/<code>.md` matching the existing schema (code + handle header, `[SPEECH]` / `[SLIDES]` / `[CAPTION]` blocks — see `distill_digest_refresh.txt`).

4. **Carousel scraping.** For each `carousel_container` code:
   - Same persistent context, navigate `https://www.instagram.com/p/<code>/`.
   - Pull the caption from `posts_index.json` (already on disk — no need to re-pull).
   - Slide text extraction: render via Playwright, capture each `<img>`/`<video>` in the carousel, OCR with `tesseract` or copy any visible text nodes. Existing UILG carousel transcripts in `distill_digest_refresh.txt` show slide text is mostly short labels + numbers — OCR quality must be verified on 5 samples before full run.
   - For image-only posts (no video, no carousel): caption from `posts_index.json` is sufficient. Write a transcript containing the caption + media_type + product_type and tag `[CAPTION-ONLY]`.

5. **Failure / rate-limit handling.**
   - Per the always-active self-healing-agents rule: any transient failure (timeout, `429`, empty DOM) → exponential backoff (2^n seconds, max 3 retries on the same reel).
   - On persistent failure for a code, write `mentor/transcripts/<code>.FAILED.json` with the error and the last known state. Move on. Report at the end.
   - If Instagram returns a checkpoint / login wall mid-run: stop the loop, surface to the user with the offending URL, restart from checkpoint.

6. **Checkpointing.** Every 50 codes, append progress to `pipeline_state.json` (`{done_codes: [], failed_codes: [], last_processed_at: ISO}`). The loop must be resumable — if killed, next run picks up where it left off. **No full re-runs on resume.**

### 3.3 Distillation

7. **Per-item triage.** For each newly-written transcript, run the same scoring rubric already encoded in `manifest.json` (likes, themes, promo_hits, ed_hits). Score = weighted sum. Output → `manifest_delta.json` with the same schema as `manifest.json`. Threshold for "promoted" matches the existing floor.

8. **Batch-distill into the 9-theme KB.** Read all new transcripts and append to the appropriate file in `mentor/knowledge/`:
   - `essays.md`, `timeline.md`, `activities.md`, `school_list.md` ← **underweight (3 items)** — give this theme extra attention; nearly every UILG carousel about school list (how to pick, ranking, fit) belongs here.
   - `interviews.md`, `testing.md`, `recommendations.md` ← **recommendations underweight (2 items)** — there is likely a UILG post series on LORs/teacher outreach in the unprocessed set.
   - `myths_mindset.md`, `study_skills.md`.
   - Cross-reference the existing UILG rubric in `knowledge/` so new entries slot in alongside the existing 193 (don't duplicate).

9. **Build a single source of truth.** Append `manifest_delta.json` records to `manifest.json`. Update `theme_coverage` counts. Update `mentor/context.md` "Log" with the date and totals.

10. **Voice / style profile synthesis.** One new file `mentor/knowledge/uilg-voice-profile.md` capturing:
    - recurring frameworks (PPF, three tiers, door taxonomy, etc. — already noted in PS-theme-outline.md evidence base)
    - vocabulary patterns, hook formulas (e.g., "How to X 📝" carousel opener, "7 things…" list)
    - structural templates for carousels vs reels vs captions
    - what UILG sells / promotes (mentor program, eBook, course) so the student can write **against** the UILG formula without copying it (per the 2026-08-26 voice rule in `PS-theme-outline.md`).

### 3.4 Validation / sign-off

11. **Coverage check.** After merge, re-run a diff:
    - `len(pending_codes.json) == 0` OR only contains explicit `.FAILED.json` entries.
    - Every transcript in `mentor/transcripts/` has a `code:` line that exists in `posts_index.json`.
    - `manifest.json.theme_coverage` sums match `len(manifest.items)`.

12. **Spot-audit.** Read 5 randomly chosen newly-added transcripts. Confirm format matches `distill_digest_refresh.txt` schema and that distillation entries in `knowledge/` are not duplicates of existing ones.

13. **Update `mentor/context.md` "Log"** with: date, posts processed, theme deltas, any FAILED.json codes, and the new `uilg-voice-profile.md` reference.

---

## 4. Files to create / modify

**New files:**
- `pending_codes.json` — diff output (one-shot, can be deleted after merge)
- `pipeline_state.json` — resumable loop state
- `manifest_delta.json` — staging area for new manifest entries
- `diff_assets.py` — one-shot asset diff helper
- `pipeline_loop.py` — resumable scraping loop (the workhorse)
- `distill_loop.py` — batches new transcripts into knowledge files
- `mentor/knowledge/uilg-voice-profile.md` — synthesis
- `mentor/transcripts/<code>.md` — one per newly-processed post (the bulk of new files)
- `mentor/transcripts/<code>.FAILED.json` — for items that failed after retries

**Modified files:**
- `manifest.json` — merged with `manifest_delta.json`, theme_coverage recalculated
- `mentor/knowledge/<theme>.md` — appended with new distillations
- `mentor/context.md` — "Log" entry appended

**Untouched:** PS drafting files (`PS-theme-outline.md`, `mentor/transcripts/` schema reference).

---

## 5. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Instagram rate-limit / checkpoint during long run | Checkpoint every 50 codes; resume from state file; surface login walls to user immediately rather than retrying blindly. |
| 851 reels × minutes each = multi-hour run | Allow the loop to run in background; surface progress every 50 codes; user can stop and resume. |
| OCR quality on carousels may be poor | Verify on 5 samples before committing to the full carousel batch; if tesseract is unreliable, fall back to caption-only `[CAPTION-ONLY]` for carousels and document the gap. |
| Some reels are huge (>2 GB) | Use `Range` requests (proven via `probe_range.py`); `ffprobe` to verify moov atom before STT. |
| Duplicates / near-duplicates flooding the KB | Before appending to a `knowledge/<theme>.md`, hash the new entry's content and skip if a >85% match exists in the existing file. |
| Voice profile becomes a copy-paste template for the student | The 2026-08-26 voice rule says "raw material must stay human-authored"; uilg-voice-profile.md exists to help the student *avoid* the UILG formula, not adopt it. Flag this explicitly in the file's preamble. |
| Run partially completes then user changes mind | `pipeline_state.json` + `manifest_delta.json` make rollback trivial: delete state + delta and the system returns to the pre-run state with manifest untouched. |

---

## 6. Order of operations (executable as-is)

1. Write `diff_assets.py` → run it → produce `pending_codes.json`. **Stop here, confirm count looks right (~851).**
2. Refresh cookies via `harvest_ig_cookies.py` if needed; confirm `logged_in=true`.
3. Write `pipeline_loop.py` (resumable scraping). Run against `pending_codes.json`. Reels first (higher signal), carousels second, image posts third. Save transcripts as they complete.
4. After loop completes (or on user stop), write `distill_loop.py` and run it against the newly-added transcripts to populate `manifest_delta.json` and append to `knowledge/<theme>.md`.
5. Run voice-profile synthesis → `mentor/knowledge/uilg-voice-profile.md`.
6. Merge `manifest_delta.json` into `manifest.json`; recompute `theme_coverage`.
7. Run the validation diff from §3.4 #11.
8. Spot-audit 5 transcripts (read + format check).
9. Update `mentor/context.md` Log with the date, totals, deltas, and any failed codes.

---

## 7. Open question (one)

**Run mode for the scraping loop.** Does the user want:

(A) the loop to run **in the foreground, synchronously**, surfacing progress as it goes — simplest, blocks the session;
(B) the loop to run **in the background** (PowerShell `Start-Process` or detached task), polling `pipeline_state.json` for progress — does not block, requires the implementation agent to come back and check;
(C) the loop to be **driven manually** in chunks of N codes (e.g., 100 at a time) so the user can sanity-check transcripts between batches — slowest, highest oversight.

Default recommendation: **(B)** with progress logged to `pipeline_state.json` every 50 codes, the user notified when the run completes or hits a checkpoint wall. Switch to (C) if the user wants to review output mid-run.

Plan saved at `D:\Project Emancipation\.kilo\plans\1788171363729-uilg-full-distill.md`.