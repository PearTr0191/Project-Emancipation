# Common App CV — [Name]
**Class of 2027 | Vietnam | International Applicant**
SAT 1540 · IELTS 9.0 · G10 9.5/10 · G11 9.6/10
**Intended major:** Data Science / Applied ML

> **The through-line (name it in every entry):** one field — making data useful and trustworthy for real decisions: car buying (ViDrive), emergency response (rescue), cultural memory (museum), college funding (GlowBal). This file is the master content for the Common App Activities and Honors sections. Competitions timing lives in `CV.md`. The VinUni 1-page version is `CV-vinuni.md`.

---

## Projects (Tier 1 — the spike)

### ViDrive — Car TCO Web App · 2026 · *Shipped*
Built a car total-cost-of-ownership web app that prices a new-car decision from real fuel prices and running-cost data, cutting new-car research from 4+ days to under 2. One buyer took the model's recommendation over the car he came in wanting, a CR-V L at 1.1B VND against a VF6 Plus at 770M, and saved 330M VND. Self-taught Python and agentic-AI workflows; on track for 750 monthly active users within two months of launch.

**150-char version:** Built ViDrive, a car TCO web app: research cut from 4+ days to under 2; one buyer saved 330M VND on the purchase. 750 MAU target.

*Measured 2026-10-01 — the "projected" qualifier is retired. One verified buyer, and the figure is his own: a CR-V L at 1.1B VND MSRP against a VF6 Plus at 770M, on the car he actually bought — 330M VND saved. The strength rests on the receipt, not the number: keep the message thread and the purchase record on file for the VinUni interview, because "he bought the cheaper car the model named" is the data-science claim and 330M is only its arithmetic.*

### Rescue Assist System — Emergency Response AI · 2026 · *Self-initiated — description pending*
**Not a competition entry any more.** Built for the Intel AI Global Impact Festival Vietnam and submitted to its elimination round; **did not advance to the finalist round** (student-confirmed 2026-10-02).

> **Open, and blocking:** this entry now stands or falls on one sentence that does not exist yet — what the system actually does. Concretely: what data it takes in, what dispatch or routing decision it produces, and who would be reading the output. The old line ("AI system utilizing data for emergency response coordination") named a *category*, not a system, and the competition name was carrying the credibility. **Test:** write it in 150 characters using only true specifics. If that is impossible without inventing anything, cut the entry — do not pad it. Nothing else in the file depends on it.

**150-char version:** *pending the same test.*

### Digital Museum — Heritage Data, Live · 2026 · *Live at vietheritage.pages.dev*
Built a fully interactive virtual museum where heritage survives as verified data: a strict cleaning-and-verification gate admits only artisan-proven information, 3D models and images carry each heritage item, and a self-trained ONNX model scores vocal similarity to the originals.

**150-char version:** Interactive virtual museum at vietheritage.pages.dev: verified heritage data, 3D artifact models, self-trained ONNX vocal-similarity model.

**The thread (name it in every version of this CV):** One field — making data useful and trustworthy for real decisions: car buying (ViDrive), emergency response (rescue), cultural memory (museum), college funding (GlowBal). Lead with it; do not bury it at the bottom of a section.

---

## Technical Review & Advisory (Tier 2 — argues for Tier 1)

### Beta Tester & Technical Advisor — GlowBal · Aug–Sep 2026 · *Advisory*
Ran the review program for a scholarship and admissions platform built for students who can't afford to do the research themselves. Two passes, both evidence-backed: a full end-to-end user session on a fresh account (Aug 30, 16 logged frictions), then a five-persona sweep across 17 routes covering UX, security, systems, and first-time-user failure modes (Sep 12). Every finding written up in a fixed format — symptom, technical consequence, fix proposal, severity — with a screenshot attached.

The two P0 findings were the same defect from different ends. The flagship AI report engine didn't generate: intake answers submitted, then discarded, and the Create button stayed disabled. And university search couldn't filter by need-blind status, full-need funding, co-op, or admission odds. For a student budgeting $20k total, that filter is the only question the product exists to answer, and it couldn't return one. Also flagged analytics firing after "Essential Only" consent, a privacy policy with no Vietnamese data-handling section under NĐ-CP 13/2023, and the same achievement, GPA, and subject fields stored in two to four places without syncing.

**150-char version:** Ran GlowBal's review program: full user session plus a five-persona sweep of 17 routes; P0 findings on a broken report engine and missing need-blind filters.

*Why this is strong for the DS profile, stated plainly: it is the only entry where a third party — a product team — read his work and acted on it, and the defect he led with is a data-quality failure, not a visual one. A platform whose whole claim is trustworthy admissions data could not filter by the one criterion its users decide on. That is the thread of this CV arriving somewhere he did not build it himself.*

*Source material: `D:/Projects/GlowBal/GlowBal B1PR.md`, `GlowBal W2 Multi-Persona Review.md`, `[GlowBal PIA] Pear - W1.md`, `W2-evidence/`.*

---

## Leadership & Operations (Tier 2)

### Head of Human Resources — Julience Science Festival · 2026
Reclaimed 9 of 15 weekly HR man-hours and boosted working attendance by 10 of 80 members by introducing a semi-automated performance tracking system for 40 members across three departments.

**150-char version:** Reclaimed 9 of 15 weekly HR hours and raised attendance 10 of 80 via a tracking system for 40 members across three departments.

### Orientation Group Leader — Foreign Language Specialized School · Aug 2025 – Sep 2026
Directed and onboarded a cohort of 23 freshmen across a multi-day orientation program; facilitated group integration and resolved participant conflicts within 15 minutes of escalation, applying active conflict resolution under tight event constraints.

**150-char version:** Onboarded 23 freshmen through multi-day orientation. Resolved conflicts within 15 minutes of escalation using active conflict resolution.

### Co-Orchestrator & Technical Lead — "Dear Across The Blue" (SMCNN 2026) · Mar 2026
Co-orchestrated "Dear Across The Blue," a talent show put on by two classes, 11A2 and 11A9. The official roster is 70 students, 35 per class, split across six departments: performance, content, design, logistics, sound, and visual effects. My assigned post was technical lead and coordinator for content, SFX and VFX — three of the six departments.

Built the effects and wrote the cue-call script that fired them live, then ran the VFX and SFX bench on show night. Cue calling is the part that does not forgive mistakes: the script either matches what the room is doing or the room knows nothing is happening.

**150-char version:** Technical lead and coordinator for content, SFX and VFX on "Dear Across The Blue," a 70-student, six-department school talent show.

*Provenance (resolved 2026-10-01):* `Post-Op Assessment - A2xA9 SMCNN.md` — the show's own work-and-member assessment table. Headcount, department structure, and the exact role title are quoted from it, not estimated. Four corrections to what was previously written here: the headcount is **70, not "80+"**; the show has a name and it is "Dear Across The Blue," not a generic talent show; the post was broader than VFX/SFX — it covered technical plus content coordination as well, which is why the title reads technical lead rather than head of VFX/SFX; and **the 100% figure has been cut.**

**On the 100% — the column is `ĐGHT`, Đánh giá hoàn thành: a completion rating, not a grade or an award.** Sixty-one of the seventy members scored 100%; six scored 80% and two scored 90%. Quoting it would have read as a distinction he earned when it is the modal outcome — it records that he finished his assigned duties, which is the baseline expectation for a committee member. If a reader asked "how many others got 100%?" the honest answer is nearly everyone, so it does not survive the measurement rule this file runs on. It stays here as a fact about the source document and out of the entry.

**Still unverified:** the number of acts. The assessment table records per-member department assignments, not programme contents. If a programme, poster or video turns up, it is the one remaining figure worth adding; if not, the entry does not need it — 70 students across six departments is already the load-bearing claim.

---

## Open-Source Contributions (Tier 2)

### Maintainer-Reviewed PRs — NoLlama (Intel NPU / OpenVINO LLM server) · Aug 2026 · *Merged upstream*
Three PRs merged into [`aweussom/NoLlama`](https://github.com/aweussom/NoLlama) by the same contributor, each after multi-round maintainer review. All shipped behind regression tests or node harnesses on `main`.

**PR #23 — `feat: Added Markdown syntax support; fixed sticky-scrolling`** (merged Aug 13; upstream base for #35)
The Web UI renderer pipeline (`mdEscapeAndRender`, `mdInline`, `escapeAttr`, `safeUrl`). Four real bugs found under maintainer review: (1) XSS via unquoted attribute injection (`![x" onerror="alert(1)](y)` executed on render) — fixed by an `escapeAttr` quote-escaper + a `safeUrl` allowlist (http/https/mailto/relative — `javascript:`, `data:` render as plain text); (2) `mdInline` ran twice (whole text then per line), breaking underscores inside `href` URLs; (3) emphasis regexes crossed newlines, destroying star-bullet lists; (4) blockquote matched raw `>` before escaping turned it into `>`. Plus the sticky-scroll architecture (`streamState`, `updateStreamBubble`, pinned/freed model on expanded thinking blocks) that keeps user scroll intact during streaming. All 8 failure cases + 7 regression cases verified with a node harness.

**150-char version:** Shipped #23 on `aweussom/NoLlama`: built the markdown renderer (`escapeAttr` XSS guard, `safeUrl` scheme block, single-pass `mdInline`) + pinned scroll during streaming; 15 cases verified.

**PR #34 — `feat: pin NPU_PLATFORM on NPU load (AUTO_DETECT guard)`**
Pinned the `NPU_PLATFORM` constructor kwarg in the NPU load path so the Intel NPU compiler stops defaulting to `AUTO_DETECT` and returning `Unsupported platform: 'AUTO_DETECT'` on Intel Core Ultra hardware. Surface area: a `--npu-platform` flag with auto-resolve from `DEVICE_ARCHITECTURE`, the platform printed in the device banner, and an `AUTO_DETECT`-specific hint in the user-facing error explainer (matched before the generic "Compilation failed" branch, gated on the serving slot being NPU). Regression test `tests/test_npu_pin.py` covers all four orderings — including the GPU-slot gate — so a future reorder breaks a test instead of a user's afternoon.

**150-char version:** Shipped #34 on `aweussom/NoLlama`: pinned `NPU_PLATFORM` so Intel NPU stops failing on `AUTO_DETECT`; added `--npu-platform`, a banner suffix, and a regression test for the error-hint ordering.

**PR #35 — `feat: web UI markdown table pass + NPU-gated history-length banner`** (closes #25, #26)
Two production fixes to the Web UI streaming renderer. **Markdown tables**: pipe-in-cell content no longer splits on `|`, alignment colons (`:--`/`-:`/`:-:`) supported, streaming assembly covered, and `splitTableRow` tracks bracket depth so footnote-style `[1]` and unclosed `[` don't swallow the next cell. **History-length banner**: warns the user when chat history approaches the NPU's prompt-token cap (NPU-only — the UI gates it on `/health` reporting an NPU device, since GPU/CPU have no such limit). CSS uses the existing theme variables. Test harness `scripts/md-render-test.mjs` at 52/52 including XSS-in-cell, code spans in cells, alignment, and footnote edge cases.

**150-char version:** Shipped #35 on `aweussom/NoLlama`: added markdown tables + a NPU-only history-cap banner to the Web UI renderer, with a 52-case test harness behind it.

**Through-line:** Three PRs, same codebase, same reviewer — from the renderer foundation (#23) to an error that lied to the user (#34) and a table the renderer couldn't render (#35). Each one: find the place the system misleads the user, fix it minimally, leave a regression test behind it.

---

## Teaching & Service (Tier 3)

### SAT Tutor — Schoolhouse · Feb – Mar 2026 · Volunteer
Taught two 1-on-1 SAT classes over nearly 20 hours, raising both students from a 1260 baseline to 1450+.

**150-char version:** Taught two 1-on-1 SAT classes over nearly 20 hours, raising both students from a 1260 baseline to 1450+.

---

## Activities List — What Goes Where (Common App)

**Updated 2026-10-01 with GlowBal and the Mar 2026 talent show.** That took the shortlist from 7 to 9 entries against an 8-slot cap. **Resolved 2026-10-02:** the Intel Festival elimination removed Rescue Assist from contention, so the shortlist is back to exactly 8 and the cap problem is gone rather than solved. Nothing needs to come back in.

**Order by impact, not chronology.** ViDrive first. GlowBal second — it earns the slot ahead of NoLlama because a third party acted on his findings, and because it is the cleanest service-to-others story in the file. The two build projects follow. Leadership, then volunteering.

**On Rescue Assist — the honest version (rewritten 2026-10-02).** It was already the weakest standalone entry: an elimination round is not a placement, and the description carried no number that survived the measurement test. The finalist round has now closed without advancing him, which (a) removes the competition name the entry was borrowing credibility from, and (b) kills the earlier plan to demote it into a clause inside the Intel Festival Honors line — there is no Honors line to demote into. **An elimination is not an achievement**, so it is out of Top Achievements and out of REWARDS on the VinUni CV, full stop.

That leaves one honest question, and it is a description question rather than a value question. The project is real built work and it carries the emergency-response arm of the stated through-line (cars → emergencies → heritage → college funding), so cutting it is a real loss. What it no longer has is a third party vouching for it. Write the one line that says what the system *does* — data in, decision out, user identified — in 150 characters, true specifics only. If that line can be written, the entry survives on its own engineering. If it cannot, cut it rather than padding it back with the festival's name. Either answer is defensible; padding is not.

**What did not get weaker.** NoLlama is Intel-adjacent and untouched by this: three PRs merged upstream into an Intel NPU / OpenVINO LLM server after multi-round maintainer review, each shipped behind a regression test. That is a verified artifact with a public record, which is a strictly stronger thing to point an AO at than a festival elimination. The "Intel" thread in this file actually reads cleaner with the competition gone and the repo kept.

**Achievements section (Top Achievements):** Only the three real ones — ViDrive, Digital Museum, Julience HR. **No TBD placeholders.** NoLlama is not an "achievement" in the same sense (it's a contribution, not a placement); it belongs in Activities, not Achievements. GlowBal is advisory service, not an honor — Activities only. **Rescue Assist (Intel) was on this list until 2026-10-02** and was removed when the finalist round closed without advancing him: an elimination round is a submission, not an award, and listing it as an achievement is the kind of inflation both AOs and VinUni reviewers read past.

**Activities section (8 slots max, use ~5–6):**

| # | Entry | Type |
|---|---|---|
| 1 | ViDrive — Passion Project | Independent |
| 2 | GlowBal — Beta Tester & Technical Advisor | Advisory |
| 3 | NoLlama OSS Contributions (#23 renderer/XSS; #34 NPU pin; #35 tables + banner) | Independent |
| 4 | Digital Museum | Independent |
| 5 | Julience Science Festival — Head of HR | Leadership |
| 6 | "Dear Across The Blue" — Co-Orchestrator & Technical Lead | Leadership |
| 7 | Orientation Group Leader | Leadership |
| 8 | SAT Tutoring — Schoolhouse | Volunteer |
| — | Rescue Assist System — *out of Activities and Honors as of 2026-10-02; held under Projects pending the description test above* | Independent |

**DS-specific rule for the entries:** every number must survive the "how was this measured" question. ViDrive's 330M is measured now — the MSRP gap on a real purchase (CR-V L at 1.1B against VF6 Plus at 770M), verified 2026-10-01, and the figure is the user's own rather than the model's (see the note above); Julience's 9/15 and 10/80 are measured baselines; the museum's gate and ONNX model are real systems; GlowBal's 16 frictions, 5 personas and 17 routes are countable from the review files; the show's 70 students and six departments are countable from the assessment table. Two ViDrive numbers still cannot answer it: the 750 MAU target is a goal rather than a count, and the 4+ days → under 2 research cut needs a sample behind it. Measure or reframe both before submitting.

**Provenance status (updated 2026-10-01):** the talent show's figures are now sourced. `Post-Op Assessment - A2xA9 SMCNN.md` is the show's own member assessment — it names "Dear Across The Blue" as the title, gives the roster as 35 students in 11A2 plus 35 in 11A9 (70 total), lists six departments (performance, content, design, logistics, SFX, VFX), and records his post as technical lead and coordinator for content, SFX and VFX at a 100% assessment rating. **The earlier "80+" figure was an estimate and is now retired** — the CV says 70. Only the act count is still unrecorded anywhere in that file.
