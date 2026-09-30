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
