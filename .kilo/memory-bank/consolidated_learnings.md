# Consolidated Learnings

*Curated from raw reflection logs. Organized for retrieval and reuse.*

---

## Windows PowerShell 5.1 Scripting

### Comma operator binds tighter than `+` inside `@()`
**Symptom**: `@('a' + $x, 'b' + $y)` produces a **1-element** array whose value is `a<x>b<y>` (values concatenated), not a 2-element array.

**Cause**: In the PowerShell precedence table, `,` ranks above the arithmetic/comparison operators, so the expression parses as a flat comma list before `+` is applied.

**Fix**: Parenthesize each element, or better, use a helper:

```powershell
$pairs = New-Object System.Collections.ArrayList
function Add-Pair([string]$old, [string]$new) { $script:pairs.Add(@($old, $new)) | Out-Null }
```

**Guardrail**: assert `$p.Count -eq 2` inside the loop.

### Single-quote escaping
PowerShell single-quoted strings escape `'` by **doubling** it; backslash is NOT an escape character.
- Correct: `'would ha\''e significantly'`  ->  `would ha\'e significantly`
- Wrong: `'would ha\'e significantly'`    ->  parse error

### Non-ASCII literals in .ps1 files
PS 5.1 reads a BOM-less `.ps1` using the ANSI code page, mangling smart quotes and em dashes. Either save the script as UTF-8 **with BOM**, or build literals from code points:

```powershell
$em   = [string][char]0x2014   # em dash
$apos = [string][char]0x2019   # right single quote
$ldq  = [string][char]0x201C   # left double quote
$raq  = [string][char]0x00BB   # right guillemet
```

### Safe surgical text repair recipe
```powershell
$text = [System.IO.File]::ReadAllText($src, (New-Object System.Text.UTF8Encoding($false)))
foreach ($p in $pairs) {
    if (([regex]::Matches($text, [regex]::Escape($p[0]))).Count -ne 1) { throw "not unique: $($p[0])" }
    $text = $text.Replace($p[0], $p[1])
}
[System.IO.File]::WriteAllText($dst, $text, (New-Object System.Text.UTF8Encoding($false)))
```
- The "occurs exactly once" assertion is the single most valuable guardrail: it catches both missed fixes and ambiguous over-matching before anything is written.
- Keep all writes to one `WriteAllText` at the very end, after every assertion passes, so a throw leaves no partial output.
- Verify with a **predicted byte delta** per edit (e.g. `^` -> `U+201C` = +2 bytes, `\e` -> `e` = -1) and check the arithmetic matches reality. Catches silent character loss.

---

## OCR / Text-Corruption Repair

### Character-code auditing before editing
When a line "looks" damaged, dump the actual code points before deciding:
```powershell
($line.ToCharArray() | ForEach-Object { 'U+{0:X4}' -f [int]$_ }) -join ' '
```
This distinguishes a genuine OCR defect (an ASCII `^`, `\`, or `»` where none belongs) from legitimate typography (a doubled em dash is a valid convention). Prevents "fixing" non-defects.

### Chunk-internal ground truth
A chunk containing both a student's essay and its published review is self-verifying: the review frequently **quotes or paraphrases the essay verbatim**. Corroborate a repair against it.
- "East-forward seven years" -> "Fast-forward seven years" was proved by the reviewer citing "Fast-forward seven years,".
- In-chunk reviewer attributions (`*— Juliet Nelson*`) also serve as repeated-name consistency checks across essays.

### Ambiguity policy
Prefer a missed fix over a wrong one. Categories to leave alone unless provable:
- Fill-in-the-blank underscores (`"From___ I learned ___"`) — the underscore may BE the original blank, not corruption.
- Spaced ellipses (`.. .`, `. ..`) when tight `...` is used elsewhere — cannot tell author style from OCR.
- Doubled em dashes, deliberate lowercase paragraph initials, mid-sentence emphasis capitals.
- Semicolon/colon before a capitalised word (may be authorial, not a degraded period).
- Real digits even when surrounded by letters-as-pronouns: `(1, 5, and 9)`, `11:53`, `2009`, `Op. 16`.

### Verification checklist for a repaired chunk
1. File exists, byte count differs only by the predicted delta.
2. Line count identical before/after (paragraph count = blank-line count; compare both).
3. Every `##` / `###` heading present; every `**Review**` present.
4. Diff line numbers listed explicitly and each one re-read in the output.
5. Encoding (BOM presence) and line endings (CRLF vs LF) preserved.

---

*Last updated: 2026-09-29 | Source: Project Emancipation chunk_08_viii_experiences OCR repair*
