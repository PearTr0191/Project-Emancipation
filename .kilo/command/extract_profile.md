---
description: "Process any Instagram profile (rakhimoff_amir, ivy_roadmap, etc.) by reading digest/transcripts, classifying themes, and writing profile synthesis."
agent: code
subtask: false
---

# /extract_profile [profile-name]

Process any profile (e.g., `rakhimoff_amir`, `ivy_roadmap`) by reading available digest/transcripts, applying the same 9-theme classification rubric, and producing profile-level synthesis.

## Steps

1. Read `mentor/distill_digest_refresh.txt` for profile-tagged entries (`### <code> [profile]`).
2. Read any transcript `.md` files in `mentor/transcripts/` that contain `[profile]` references or profile-name references.
3. Apply theme classification (`essays`, `activities`, `timeline`, `school_list`, `interviews`, `testing`, `recommendations`, `myths_mindset`, `study_skills`).
4. Write `knowledge/<profile>_profile.md` (or update `uilg-voice-profile.md` with a profile comparison section).
5. Update `manifest.json` with profile entries (optional).

## Profiles available

- `rakhimoff_amir`: scholarship/admissions advice profile (digest + transcripts available, no `posts_index.json`).
- `ivy_roadmap`: Ivy League roadmap / mentor profile (digest + transcripts available, no full `posts_index.json`).
- `ultimateivyleagueguide`: full pipeline completed (`posts_index.json` with 1044 records, 907 manifest items).
