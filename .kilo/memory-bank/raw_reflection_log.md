# Raw Reflection Log

***
Date: 2026-09-29
TaskRef: "Repair word-level OCR corruption in chunks/chunk_08_viii_experiences.md -> FIXED_chunk_08_viii_experiences.md"

Learnings:
- PowerShell's comma operator binds TIGHTER than `+` in array subexpressions. `@('a' + $x, 'b' + $y)` yields a 1-element array, not a 2-element array, and silently concatenates. Must wrap each element: `@(('a' + $x), ('b' + $y))`. Use a `Add-Pair` function to avoid the trap entirely.
- A safe recipe for surgical text repair of a long UTF-8 file: read with `ReadAllText(path, UTF8Encoding($false))`, assert each search literal occurs EXACTLY once with `[regex]::Matches(..., [regex]::Escape($old)).Count -ne 1`, apply `.Replace()`, write back with the same encoding. The "exactly once" assertion caught the parsing bug above before it could silently skip a fix.
- Scripts with non-ASCII search literals are fragile in PS 5.1 (a .ps1 without a BOM is read as ANSI). Build them from `[char]0x2014` (em dash), `[char]0x2019` (right quote), `[char]0x201C` (left double quote), `[char]0x00BB` (guillemet) so the script file stays pure ASCII.
- Byte-delta arithmetic is a cheap integrity check: predicted output byte delta (+4) matched exactly, confirming no unintended characters were added or stripped.
- Cross-referencing a mangled line against the reviewer's summary of the same essay proves the repair: "East-forward seven years" -> "Fast-forward seven years" was confirmed by the reviewer quoting “Fast-forward seven years,” in the same chunk.
- The reviewer of the same essay in-chunk is a ground-truth oracle for the student's own text (same for the Lisa Wang / Leslie Ojeaburu / Isaac Alter reviews).

Difficulties:
- Ran the repair script twice due to the comma-precedence parse error; first run threw on an unexpected pattern count, which is exactly the guardrail working. No partial writes occurred because the throw happened before the single WriteAllText at the end.
- Several spots were genuinely ambiguous and deliberately left: fill-in-the-blank underscores, spaced ellipses (`.. .`, `. ..`), a doubled em dash, a mid-sentence capital ("Constant"), a lowercase paragraph-initial "but", a semicolon before a capital letter, and "disservice done by humans". Each would require guessing author intent.

Successes:
- Character-code auditing (dumping U+XXXX for every non-ASCII char on a suspect line) distinguished a real OCR defect (ASCII `^` and `\` and `»` artifacts) from legitimate typography (doubled em dash), avoiding a wrong "fix" on line 19.
- 23 targeted repairs across 19 lines, zero blank-line changes (134 blank lines before and after), 8/8 headings and 7/7 `**Review**` markers preserved.
- Kept all real digits: "(1, 5, and 9)", "11:53", "2009", "Top 40", "40+ teens" counts.
***
Date: 2026-09-30
TaskRef: "Install jpeggdev/humanize-writing globally for Kilo and Cline, merged over the existing no-slop skill"

Learnings:
- A "verbatim" claim is only worth what a diff proves. I wrote `references/ai-tells.md` by retyping what `webfetch` returned, and the markdown-to-text render had silently altered one word ("these cluster" -> "this cluster"). The file was labelled verbatim in its own header while being wrong. Raw bytes plus a line diff are the only acceptable evidence for vendored content.
- Authoritative cross-check for a vendored file: the GitHub Contents API blob (`sha` + `size` + `content`). It settled a contradiction that the raw download and the web render disagreed on. Repo HEAD was unchanged (last commit 2026-03-14, "refine AI-detection guidelines to reduce false positives"), which proved the web render was the corrupt source rather than a fresh upstream edit.
- Chained surgical edits on a long line compound errors. A truncated `newString` first dropped two clauses; the repair edit then re-appended the tail and duplicated it. Two edits produced three wrong states. Rebuilding the file programmatically from the downloaded bytes (assert the anchor line, splice the header, write) collapsed it to correct in one pass. For vendored text, regenerate rather than patch.
- The Edit tool reports "applied successfully" on edits that damage the file. Every edit to a vendored file needs a read-back plus a hash or diff, in the same session.
- `python -c` one-liners break on nested quotes under PowerShell 5.1 (an escaped inner string terminated the literal). Write the script to `C:\Users\Admin\AppData\Local\Temp\kilo\*.py` and run it instead.
- Kilo snapshots skill bodies when the session prompt is built. The `skill` tool served the pre-edit SKILL.md all session while the file on disk was already correct; the directory listing it returned did include the new files. Verify by reading the file, not by loading the skill.
- Kilo's `config_validation` "Failed to parse frontmatter: No context found for instance" on `agent/general.md` is not caused by editing the body. `kilo.jsonc` holds empty stubs, `"agent": { "general": {}, "design": {} }`, so the validator has no instance context to resolve. Pre-existing config drift.
- Harness skills are discovered from a fixed path per harness, not symlinked: Kilo reads `~/.config/kilo/skills/`, Cline reads `~/.agents/skills/`. Two real copies need a hash comparison after every write to keep them honest.

Difficulties:
- Trusted the user's pasted text as the reference and initially "restored" the wrong word, because both the user's paste and my first fetch came from the same rendered pipeline. Had to fall back to the API blob and a byte download to find ground truth.
- Ran the hash comparison twice with wrong substring offsets, producing a false MISMATCH on identical files. Compare on a stable key (`$_.Name` + `$_.Directory.Name`), never a hand-counted character offset.

Successes:
- Final state: `references/ai-tells.md` body is byte-identical to upstream in both installs, with a two-line provenance header as the only delta. Both files hash to e5a6f0466b0b571c.
- Resolved four genuine conflicts between the two rule sets (em dashes, fragments, adverbs, rule of three) in one documented table rather than leaving both rule sets live, and deleted the two now-superseded reference files so no stale rule survives.
- Broadened the three `no-slop` trigger lines from app/web-and-docs-only to every prose artifact, and confirmed all three edited rule files are still valid UTF-8 without a BOM.

Security note (pre-existing, not introduced):
- `C:\Users\Admin\.config\kilo\kilo.jsonc` stores the OpenRouter, NVIDIA, and Groq API keys, the GitHub PAT, and the Firecrawl key in plaintext. Reading that file places every one of them into the session transcript. Rotate them and move to env vars if these transcripts are ever shared or uploaded.
***
Date: 2026-10-01
TaskRef: "Project Emancipation — propagate the verified ViDrive saving (30M → 300M VND, MSRP 1.1B vs 770M) across all eight application files"

Learnings:
- A fact correction in a claims workspace is never a find-and-replace. The number appeared in eight files under four different framings: a CV entry, a 150-char variant, an interview-prep line, a PS sentence with a dollar conversion, an outline thesis line, a trim-hierarchy instruction, a verified-fact checklist, and a profile summary. Replacing the digit in each one without reading its surrounding claim would have produced eight locally-correct, globally-contradictory statements.
- The 30M and the 300M were never the same measurement. 30M came off the running-cost model (km/100 x consumption x price x years); 300M is the MSRP gap on the purchase the user actually made. A tenfold "correction" that looks like a typo is usually a category error, and the category change is the story: model output versus transaction record. The transaction is the stronger artifact for a data-science application because it survives "how was this measured" without a projection caveat.
- A "projected" qualifier is conditional language with an exit clause attached. The VinUni specialist review had written one in with the explicit condition "revert if measured receipts exist." Finding that clause turned this from a judgment call into a mechanical edit, and it closed open item (4) from the same day's log. Search the workspace for the condition before re-litigating a claim.
- Arithmetic on a user's own numbers is a review obligation, not a nitpick. 1.1B - 770M = 330M, and the figure being propagated is 300M. An interviewer who does that subtraction in their head will land on it, and the student would have no answer ready. Flagged rather than silently corrected: the round number may be deliberate (net of fees, a trim delta) and only the student knows which.
- A number stated inside a quotation inherits the quotation's truth conditions. "He wrote back that I had saved him 30M dong" was a self-report; 300M is the student's own subtraction of two MSRP figures. Swapping the digit in place quietly makes a real person say something he did not say. The honest fix is to move the figure out of his mouth and let the two prices carry it. Recorded as an open item instead of rewritten, because the workspace's guardrail 7 requires the PS sentences to be the student's own.
- Guardrail 7 ("raw material must stay his; AI-written prose actively hurts") changes what a correction is allowed to touch. Digit fixes are fine. Rewriting the sentence that carries the digit is not. Splitting the edit into "correct the fact" and "flag the voice problem for the author" kept both constraints intact.
- `ripgrep` is not installed on this machine. `rg` fails with CommandNotFoundException; the `grep` tool is the working path for content search and accepts a per-file `path` argument, which is also how to scope a workspace-wide sweep to eight specific files and avoid false hits in ~2,000 third-party transcript files.
- Third-party corpora in the same tree poison numeric greps. `$30M app startup` and "30 million dollar company" appear throughout `mentor/transcripts/` and `manifest*.json` (scraped Instagram captions). A bare `30M` sweep returns dozens of unrelated hits; `30M VND` and `thirty million` are the discriminating patterns for this claim.
- Historical log entries in this workspace are an audit trail and must not be edited. `mentor/context.md` deliberately preserves superseded entries (see the 2026-08-26 NYU correction and the 2026-09-01 record reversals). The correct move is a new dated entry that supersedes, plus edits only to live claim sites.

Difficulties:
- The first context.md log append failed on a typo in the anchor string ("ViClause" for "ViDrive"). Retrying against a short unique tail sentence instead of the whole paragraph fixed it. Long anchors on minified single-line log entries are the failure mode; anchor on the last sentence.
- Inserting the three-item open-questions list into the PS outline split the original seam block, leaving its "Reader function" line stranded after the list. Caught on read-back and re-ordered so the block reads description, function, then open items.
- Initial file listing via `Get-ChildItem -Recurse` was truncated to a temp file because `mentor/transcripts/` holds roughly 2,000 files. The numeric greps that actually mattered were answerable from targeted file reads instead; the listing was wasted work.

Successes:
- Eight files updated coherently, verified by re-reading every changed line. The only surviving "30M" strings are intentional supersession markers ("the old 30M figure... is now retired") and the preserved 2026-10-01 audit entry.
- The 150-char Common App variant was rewritten rather than patched and lands at 129 characters, verified by hand count, leaving headroom if the sentence needs the MSRP pair inline.
- The update surfaced two soft numbers nobody had flagged: the 750 MAU target is a goal rather than a count, and the 4+ days -> under 2 research cut has no sample behind it. Both written into the DS-specific rule in `CV-commonapp.md` so they get measured or reframed before submission.
- The dollar conversion was moved at the rate the draft already used (25,000 VND/USD, from 30M = $1,200) rather than a fresh rate, so the essay stays internally consistent.
- Left the working tree uncommitted. Prior sessions already had uncommitted work in `mentor/CV.md` and `.kilo/`, and the user asked for an update, not a commit.

Addendum (same session, ~15 min later — the three flagged items were answered in a single line):
- Naming the open questions precisely paid off. "Figure is 330M, trims are VF6 Plus and CR-V L, attribution's good" answered all three in nine words. A vague "is this number right?" would have produced a vague reply and a second round of edits. When a fact is propagating, ask the narrowest question that pins it.
- Do the arithmetic check *before* propagating a figure, not after. 1.1B − 770M = 330M; I carried 300M through eight files first and only then flagged the gap. The 330M was the user's number all along and 300M was a lossy version that had been sitting in the workspace. In a first-person application document, a wrong digit is a credibility event rather than a typo, and the cost of one confirming question is eight edits. Sequence matters more here than anywhere else I write.
- This workspace is under concurrent edit. Between two reads of `mentor/CV-commonapp.md` the file grew from 95 to 126 lines, gained a GlowBal entry and a talent-show provenance note, and the DS-rule sentence I had already edited was rewritten underneath me — my next edit failed with "oldString not found" because the line had changed. Any edit against a long single-line paragraph in this repo can race. Mitigation: re-read the target line immediately before editing it, anchor on the shortest unique substring, and treat an anchor failure as evidence the file moved rather than as a typo in the search.
- Counted-number slips are worth fixing when the sentence is already open. That DS-rule read "Three ViDrive numbers still cannot answer it" and then named two. One word, same sentence I was editing, no scope creep.
***

