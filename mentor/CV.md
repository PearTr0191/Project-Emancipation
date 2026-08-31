# CV — [Name]
**Class of 2027 | Vietnam | International Applicant**
SAT 1540 · IELTS 9.0 · G10 9.5/10 · G11 ~9.6–9.7/10
**Intended major:** Data Science / Applied ML

---

## Projects (Tier 1 — the spike)

### ViDrive — Car TCO Web App · 2026 · *Shipped*
Self-taught Python and Agentic AI workflows to build a car total-cost-of-ownership web app that cuts new-car research from 4+ days to under 2 and saves buyers up to 30M VND per decision. On track for 750 monthly active users within two months of launch.

**150-char version:** Built ViDrive, a car TCO web app, cutting new-car research from 4+ days to under 2 and saving buyers up to 30M VND. Targeting 750 monthly active users.

### Rescue Assist System — Emergency Response AI · 2026 · *Submitted*
AI system utilizing data for emergency response coordination. Ideated and submitted to the **Intel AI Global Impact Festival Vietnam** (elimination round evaluated).

**150-char version:** AI rescue assist system for emergency response coordination. Submitted to the Intel AI Global Impact Festival Vietnam.

### Digital Museum — Cultural Data Preservation · 2026 · *Finished, demo live*
Preserving cultural data through a digital museum; deployed as a demo website.

**150-char version:** Digital museum preserving cultural data, deployed as a live demo website. Makes cultural heritage accessible online.

**Through-line:** All three are data-utility tools for public good — decisions (cars), emergencies (rescue), memory (museum).

---

## Leadership & Operations (Tier 2)

### Head of Human Resources — Julience Science Festival · 2026
Reclaimed 9 of 15 weekly HR man-hours and boosted working attendance by 10 of 80 members by introducing a semi-automated performance tracking system for 40 members across three departments.

**150-char version:** Reclaimed 9 of 15 weekly HR hours and raised attendance 10 of 80 via a tracking system for 40 members across three departments.

### Orientation Group Leader — Foreign Language Specialized School · Aug 2025 – Sep 2026
Directed and onboarded a cohort of 23 freshmen across a multi-day orientation program; facilitated group integration and resolved participant conflicts within 15 minutes of escalation, applying active conflict resolution under tight event constraints.

**150-char version:** Onboarded 23 freshmen through multi-day orientation. Resolved conflicts within 15 minutes of escalation using active conflict resolution.

---

## Open-Source Contributions (Tier 2)

### Maintainer-Reviewed PRs — NoLlama (Intel NPU / OpenVINO LLM server) · Aug 2026 · *Merged upstream*
Three PRs merged into [`aweussom/NoLlama`](https://github.com/aweussom/NoLlama) by the same contributor, each after multi-round maintainer review. All shipped behind regression tests or node harnesses on `main`.

**PR #23 — `feat: Added Markdown syntax support; fixed sticky-scrolling`** (merged Aug 13; upstream base for #35)
The Web UI renderer pipeline (`mdEscapeAndRender`, `mdInline`, `escapeAttr`, `safeUrl`). Four real bugs found under maintainer review: (1) XSS via unquoted attribute injection (`![x" onerror="alert(1)](y)` executed on render) — fixed by an `escapeAttr` quote-escaper + a `safeUrl` allowlist (http/https/mailto/relative — `javascript:`, `data:` render as plain text); (2) `mdInline` ran twice (whole text then per line), breaking underscores inside `href` URLs; (3) emphasis regexes crossed newlines, destroying star-bullet lists; (4) blockquote matched raw `>` before escaping turned it into `&gt;`. Plus the sticky-scroll architecture (`streamState`, `updateStreamBubble`, pinned/freed model on expanded thinking blocks) that keeps user scroll intact during streaming. All 8 failure cases + 7 regression cases verified with a node harness.

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

## Competitions

| Competition | When | Results | On Nov 1 app? |
|---|---|---|---|
| Intel AI Global Impact Festival Vietnam | Aug 2026 | Aug 2026 | If advanced past elimination |
| North Vietnam Startup Competition | Sep 2026 | By Oct 2026 | ✅ Yes — if placed |
| NextGen Innovator | Sep 2026 | By Oct 2026 | ✅ Yes — if placed |
| ~~HiMCM~~ | Nov 2026 | **Jan 24, 2027** | ❌ Dropped — Jan 24 is after REA (Nov 1) and after most RD deadlines. No-go for this cycle. |

**Key correction:** Startup + Innovator results land by October, so they are **not** invisible to the Nov 1 REA app — they can be included if you place. HiMCM is the only genuine no-go, and specifically because Jan 24 falls after both the REA deadline and most Regular Decision deadlines.

**Implication:** the two September competitions are real REA assets, not just RD updates. Submit them, and if you place, update the application before Nov 1 with the result. The products are already built, so this is submission logistics, not build time — but protect the essay blocks anyway, since September is the essay window.

---

## Activities List — What Goes Where (Common App)

**Activities section (8 slots max, use ~5–6):**
1. ViDrive — Passion Project
2. Rescue Assist System — Independent Project for Competition Submission
3. NoLlama OSS Contributions (#23 renderer/XSS; #34 NPU pin; #35 tables + banner) — Independent Project
4. Digital Museum — Independent Project for Competition Submission
5. Julience Science Festival — Leadership
6. Orientation Group Leader — Leadership
7. SAT Tutoring — Volunteer

**Order by impact, not chronology.** ViDrive first. Cluster the three personal projects; NoLlama lands right after Digital Museum — same "ship a real fix on a real codebase" theme, reviewer-validated. Leadership and tutoring follow.

**Achievements section (Top Achievements):** Only the four real ones — ViDrive, Rescue Assist (Intel), Digital Museum, Julience HR. **No TBD placeholders.** NoLlama is not an "achievement" in the same sense (it's a contribution, not a placement); it belongs in Activities, not Achievements.

---

## Essays — The Five Types (draft all five)

1. **Personal statement** — core value: clarity through data. Arc: frustration → build → impact. Material: ViDrive.
2. **Why this major** — the moment you got hooked on data/ML. Never open with "I love science."
3. **Extracurricular essay** — what changed in you because of ViDrive (not what you did).
4. **Community essay** — SAT tutoring, orientation leadership, or the rescue work.
5. **Challenge essay** — specificity beats size. What you learned → what you do differently now.

---

## School List (draft — confirm before writing supplements)

**Long-term goal lens: stay in the US → employment → green card → naturalization.**
Schools ranked on three things beyond admit odds: (1) co-op / work-integrated learning, (2) location near H-1B-sponsoring employers, (3) cost & aid (you fund years of limited student-income before a green card).

**Reach (REA):**
- Stanford — REA, Nov 1. Bay Area, top employer pipeline, meets full need.
- Dartmouth — small Ivy, strong CS, generous aid. Hanover is rural; NYC/Boston recruiting still strong.
- +1: Cornell / Rice / Vanderbilt / Duke / Notre Dame

**Targets:**
- **Northeastern** — Boston, **co-op program is the strongest structured work pipeline in the country**. Directly serves the employment→H-1B→green card path. Generous aid.
- **NYU** — NYC, Tandon. Massive employer access, need-blind admission. **Meets 100% of demonstrated financial need for first-year undergraduates on the NYC campus, explicitly including international applicants** (The NYU Promise, expanded 2024-25). Loans are not part of the need-meeting package; internationals file CSS Profile only (no FAFSA, so no federal dollars — the Promise is funded from NYU's own budget). NYU charges the same tuition regardless of residency. 2026-27 COA ~$96,988. **This is the only school on the list with a published equivalent policy — the single most budget-relevant fact in the comparison.** Verify 2026-27 figures with NYU's Office of Financial Aid before treating as decisive (costs were not yet officially approved at the time of the check).
- **Georgia Tech** — Atlanta, top-5 CS, co-op available, significantly cheaper than peers, strong Southeast employer base.
- **USC** — LA, Viterbi, generous aid, West Coast internship pipeline.
- **Michigan** — Ann Arbor, top CS/DS, strong Midwest employer recruiting, EA Nov 1.
- **CMU** — added; verify need-aware vs need-blind + 100% need met for internationals before committing. Pittsburgh is low-cost with a growing tech employer base.

**Safeties:**
- **Purdue** — strong CS, genuinely affordable, solid employer relationships. Real safety.
- **Maryland** — near DC/tech corridor, strong CS, good aid.
- +1: UT Austin / SUNY Stony Brook / Arizona State

**Non-US (secondary):**
- NUS
- VinUni (pivot — deadline ~2 months later)

### CDS weighting at a glance (2025–26 cycle)

What each school rates **Very Important** — the factors that actually move a decision. Full C7 grid + C9–C12 + C8 + aid findings: `mentor/knowledge/cds-comparison-9schools.md`.

| School | Very Important factors | Test policy | Where your 1540 lands |
|---|---|---|---|
| Stanford | rigor, GPA, class rank, scores, essay, recs, **extracurriculars**, talent, character | Required | Below median composite; **at 75th on Math** |
| Dartmouth | rigor, GPA, class rank, scores, essay, recs, **extracurriculars**, character (talent = Important only) | Required | Above median; well above Math 75th |
| NYU | rigor, GPA, **essay**, **recs**, **character** (demoted class rank, scores, interview) | Test-optional | Above median; at Math 75th |
| Georgia Tech | rigor, GPA, **character**, **state residency** (scores = Considered) | Required | Well above median; far above Math 75th |
| Michigan | **rigor + GPA only** (everything else Important/Considered) | Test-optional | Well above median; far above Math 75th |
| USC | rigor, GPA, **scores**, **essay**, **recs** (extracurriculars = Important) | Test-optional | Above median; at Math 75th |
| Northeastern | rigor, GPA, **scores**, **recs** (extracurriculars = Important) | Test-optional | Above median; far above Math 75th |
| Purdue | rigor, GPA, **essay** (talent = Not Considered, no interview) | **Required** | Far above median; way above Math 75th |
| Maryland | rigor, GPA (extracurriculars/talent/character = Important) | Test-optional | Well above median; far above Math 75th |

**What this means for ViDrive (your Tier 1):**
- Only **Stanford** and **Dartmouth** rate extracurriculars Very Important — there, ViDrive is a primary differentiator. At every other school it is supporting, and your transcript + score do more of the work (which is fine — your score is genuinely strong relative to them).
- **NYU's grid is the best match for a builder profile** — it rewards what you write and what teachers say, and it is the only school confirmed to meet 100% of demonstrated need for internationals.
- **Michigan is the most readable grid** (only rigor + GPA matter) — your upward trend and rigorous schedule are exactly what it asks for.
- **Purdue is the strongest safety on score** — your 1540 is far above its 75th percentile, and its essay is genuinely weighted.

**Your 800 Math is at or above every school's 75th percentile except Stanford** (where it equals the 75th). Your composite is below-median only at Stanford — true of every applicant at a 4% school, and the CDS does not tell you whether that specific gap is disqualifying.

---

## Portal Setup — do this first (one evening)

**Key fact: you need ~2–3 accounts, not 12.** One Common App account covers most schools. The exceptions are Stanford and Georgia Tech, which use their own systems. If you only set up Common App, you will silently miss Stanford — the school you're applying to early.

### Accounts to create (in this order)

| # | Portal | Covers these schools |
|---|---|---|
| 1 | **Common App** (commonapp.org) | Dartmouth, NYU, USC, Michigan, Northeastern, CMU, Purdue, Maryland, + Cornell/Rice/Vanderbilt/Duke/Notre Dame if added |
| 2 | **Stanford Quest** (stanford.edu/apply) | Stanford — REA, Nov 1. NOT on Common App. |
| 3 | **Georgia Tech** portal (apply.gatech.edu) | Georgia Tech — uses its own system. Verify. |

**Verify before relying on it:** Georgia Tech's portal system. Confirm at apply.gatech.edu.

### Info to have ready before you start
- One consistent email address across all portals (don't mix accounts)
- Full name, address, birthdate, citizenship/passport details
- SAT (1540) + IELTS (9.0) — decide whether to send; verify each school's test policy (Stanford's may be test-required)
- Activities list — **use the cleaned version** (4 real entries, no TBDs)
- Essays — **not yet drafting**, but theme session DONE (2026-08-26). Theme locked ~80%: see `mentor/PS-theme-outline.md`. Fill-in movements + 10-moments list due before Sep 1; draft week Sep 1–7.

### Don't do yet
- Don't write the personal statement or supplements until the theme session. Accounts can sit empty.
- Don't send test scores until you've confirmed each school's policy.

---

## Timeline

| Date | Item |
|---|---|
| Aug 25 | Portal cleanup: remove 4 TBDs, add rescue + museum, submit real entries |
| Aug 28 | SAT registration closes — **do not register** (1540 is sufficient) |
| Sep 1–7 | Personal statement draft |
| Sep 8–14 | Stanford + Dartmouth supplements; ask recommenders (one-pager protocol) |
| Sep 15–21 | NYU, Michigan, Georgia Tech supplements |
| Sep 22–28 | Revise all; feedback |
| Sep 29 – Oct 5 | Submit Stanford REA + Dartmouth EA |
| Oct 1 | FAFSA opens — **not applicable** (international); use CSS Profile where required |
| Oct | Startup + Innovator competition results |
| Nov 1 | Stanford REA + Michigan EA due |
| Jan | Regular Decision deadlines |

---

## Open Items

- [x] Confirm school list — confirmed
- [x] Set up Common App — done (Stanford + all targets on Common App; GT redirect verified by user)
- [ ] **Remove 4 TBD achievements; add rescue assist + digital museum** — verify this got done with the portal setup
- [x] Rewrite all 6 experience descriptions to ≤150 chars (drafts ready in CV)
- [ ] Identify recommenders: 1 academic + 1 personal who truly know you
- [ ] Build recommender one-pager (academic interests, personal challenges, 3 moments to weave in)
- [x] Verify each school's international aid policy: need-blind? 100% need met? — **NYU confirmed: meets 100% of demonstrated need for internationals (NYU Promise, 2024-25 expansion).** Full CDS C7/C9-C12/C8 comparison + aid findings in `mentor/knowledge/cds-comparison-9schools.md`. Remaining gap: **CMU** (need-aware vs need-blind + 100% need met for internationals still unverified) and **Cornell/Rice/Vanderbilt/Duke/Notre Dame** (the +1 reaches, not yet CDS-checked).
- [x] Theme session DONE (2026-08-26) — theme + structure locked ~80%, all decisions and fill-in prompts in `mentor/PS-theme-outline.md`. Remaining: fill movements + 10-moments list before Sep 1; PS draft week Sep 1–7.