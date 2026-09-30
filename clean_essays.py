"""
Phase 1 structural cleaner for winning-essays.md (OCR'd book text).

Deterministic transformations:
  * drop front matter (CONTENTS page + ACKNOWLEDGMENTS)
  * drop running headers and page numbers
  * drop decorative OCR garbage blocks
  * repair soft-hyphen (U+00AC) line-wrap splits
  * unwrap hard-wrapped lines back into paragraphs
  * re-emit as structured Markdown (sections / essays / reviews / epigraphs)

Structural facts this relies on:
  - A page number is always followed by that page's running header. An essay's
    display heading and its running header are the same string, so the FIRST
    sighting in the body is the real heading; later sightings are dropped.
  - "REVIEW" opens a review; the em-dash line that closes one is the reviewer.
  - An em-dash line NOT inside a review is a prompt/epigraph attribution that
    belongs to the essay preceding it.
  - The book's own table of contents is the authoritative list of essay names,
    which makes heading detection exact instead of heuristic.

Word-level OCR errors (1->I, ;->j, ^->") are NOT handled here.
"""
from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "winning-essays.md"
OUT = ROOT / "winning-essays.phase1.md"

SOFT_HYPHEN = "\u00ac"
EM_DASH = "\u2014"
PAGEBREAK = "\x00PAGEBREAK\x00"

PAGE_NUM = re.compile(r"^\d{1,3}$|^[ivxlcdm]{1,7}$|^[IVXLCDM]{1,7}$")

RUNNING_HEADERS = {
    "50 Successful Harvard Application Essays",
    "Contents",
    "CONTENTS",
    "ACKNOWLEDGMENTS",
    "Acknowledgments",
    "Introduction",
    "Identity",
    "Introspection",
    "Overcoming Obstacles",
    "Foreign Life",
    "Passion",
    "Inspiration",
    "Experiences",
}

GARBAGE = re.compile(r"^[I1%/)\]<>|*_`\u2013\u2014\s]{1,3}$")

SECTIONS = [
    ("I", "Introduction", "The Admissions Essay"),
    ("II", "Identity", None),
    ("III", "Introspection", None),
    ("IV", "Overcoming Obstacles", None),
    ("V", "Foreign Life", None),
    ("VI", "Passion", None),
    ("VII", "Inspiration", None),
    ("VIII", "Experiences", None),
]

# The table of contents misprints two names; the body of the book confirms
# these spellings, so they win.
TOC_OVERRIDES = {
    "Chaffee Duckets": "Chaffee Duckers",
    "Harniah Umanski-Castro": "Hannah Umanski-Castro",
}

SECTION_RE = re.compile(
    r"^(I|II|III|IV|V|VI|VII|VIII)\.\s*([A-Za-z][A-Za-z ]*?)\s*$"
)
TERMINAL = re.compile(r"[.!?][\"'\u2019\u201d\u201c\u2014]*$")
WRAP = 72
SUBTITLE_MAX = 46


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


# A line can break after one of these; the next word follows it directly.
NO_SPACE_AFTER = "\u2014\u2013(\u201c\u2018\"'/"


def join_text(parts: list[str]) -> str:
    out = ""
    for part in parts:
        if not out:
            out = part
        elif out[-1] in NO_SPACE_AFTER:
            out += part
        else:
            out += " " + part
    return out



# ---------------------------------------------------------------- pass 0
def extract_toc_names(lines: list[str]) -> list[str]:
    """The 50 essay names, straight out of the book's table of contents."""
    end = next(i for i, l in enumerate(lines) if l.strip() == "ACKNOWLEDGMENTS")
    names: list[str] = []
    for raw in lines[:end]:
        text = raw.replace(SOFT_HYPHEN, "").strip()
        if not text or PAGE_NUM.match(text) or text in RUNNING_HEADERS:
            continue
        # "I. Introduction: The Admissions Essay" is a section, not an essay.
        if re.match(r"^(I|II|III|IV|V|VI|VII|VIII)\.", text):
            continue
        names.append(TOC_OVERRIDES.get(text, text))
    return names


# ---------------------------------------------------------------- pass 1
def drop_front_matter(lines: list[str]) -> list[str]:
    for i, raw in enumerate(lines):
        if raw.strip() == "I. INTRODUCTION":
            return lines[i:]
    raise SystemExit("could not locate start of body ('I. INTRODUCTION')")


def _looks_like_name(text: str) -> bool:
    if not text or len(text) > 34 or text.endswith("."):
        return False
    if TERMINAL.search(text):
        return False
    words = text.split()
    if not (1 <= len(words) <= 5):
        return False
    return all(
        (core := w.strip(".,'-")) and core[0].isupper() and len(core) <= 14
        for w in words
    )


def drop_headers_and_pagenums(lines: list[str]) -> tuple[list[str], list[str]]:
    """Blank out page numbers; strip running headers, keeping real headings."""
    out: list[str] = []
    seen: set[str] = set()
    removed: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        text = lines[i].replace(SOFT_HYPHEN, "").strip()
        if not PAGE_NUM.match(text):
            out.append(lines[i])
            i += 1
            continue

        out.append(PAGEBREAK)
        nxt = lines[i + 1].replace(SOFT_HYPHEN, "").strip() if i + 1 < n else ""

        if nxt in RUNNING_HEADERS:
            removed.append(f"header  {nxt!r}")
            i += 2          # skip the number *and* the header
            continue
        if _looks_like_name(nxt):
            if nxt in seen:
                removed.append(f"header  {nxt!r}")
                i += 2          # repeat sighting = running header
                continue
            seen.add(nxt)       # first sighting = the essay's real heading
        i += 1
    return out, removed


def drop_garbage(lines: list[str]) -> tuple[list[str], list[str]]:
    out: list[str] = []
    removed: list[str] = []
    for raw in lines:
        text = raw.replace(SOFT_HYPHEN, "").strip()
        if text and GARBAGE.match(text) and not PAGE_NUM.match(text):
            removed.append(f"garbage {text!r}")
            continue
        out.append(raw)
    return out, removed


def merge_split_headings(lines: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(lines):
        cur = lines[i].replace(SOFT_HYPHEN, "").strip()
        nxt = lines[i + 1].replace(SOFT_HYPHEN, "").strip() if i + 1 < len(lines) else ""
        if cur == "IV. OVERCOMING" and nxt == "OBSTACLES":
            out.append("IV. OVERCOMING OBSTACLES")
            i += 2
            continue
        out.append(lines[i])
        i += 1
    return out


def dehyphenate(lines: list[str]) -> list[tuple[str, int]]:
    """Undo line-break splits.

    Returns (text, effective_length) per line. The effective length is the
    width of the *last* physical segment folded into the line, because that is
    what the typesetter actually measured when deciding to end a paragraph.
    A run of consecutive split words must be chained, not consumed one at a
    time, or only the first link of the run is repaired.
    """
    out: list[tuple[str, int]] = []
    n = len(lines)
    i = 0
    while i < n:
        text = lines[i].rstrip()
        eff = len(text)
        while text.endswith(SOFT_HYPHEN):
            j = i + 1
            while j < n and (not lines[j].strip() or lines[j].strip() == PAGEBREAK):
                j += 1
            if j >= n:
                text = text[:-1]
                break
            nxt = lines[j].rstrip()
            # Split fragments are pieces of ONE word: never insert a space.
            text = text[:-1] + nxt
            eff = len(nxt)
            i = j
        out.append((text.replace(SOFT_HYPHEN, ""), eff))
        i += 1
    return out



# ---------------------------------------------------------------- pass 2
class NameMatcher:
    """Binds body heading lines to canonical names from the table of contents."""

    def __init__(self, names: list[str]) -> None:
        self.remaining = list(names)

    def match(self, text: str) -> str | None:
        key = norm(text)
        if not key:
            return None
        for name in self.remaining:
            if norm(name) == key:
                self.remaining.remove(name)
                return name
        close = difflib.get_close_matches(
            key, [norm(n) for n in self.remaining], n=1, cutoff=0.80
        )
        if close:
            for name in self.remaining:
                if norm(name) == close[0]:
                    self.remaining.remove(name)
                    return name
        return None


def build_blocks(lines: list[str], toc: list[str]) -> list[tuple[str, str]]:
    pairs = dehyphenate(lines) if not isinstance(lines[0], tuple) else lines
    cleaned = [p[0].strip() for p in pairs]
    widths = [p[1] for p in pairs]
    matcher = NameMatcher(toc)
    blocks: list[tuple[str, str]] = []
    buf: list[str] = []
    prev: str | None = None
    in_review = False
    sec_sub = {n: s for n, _, s in SECTIONS}
    await_sub: str | None = None

    def emit_para() -> None:
        nonlocal buf, prev
        if buf:
            blocks.append(("para", join_text(buf)))
            buf.clear()
        prev = "para"

    n = len(cleaned)
    i = 0
    while i < n:
        text = cleaned[i]

        if not text:
            if buf:
                emit_para()
            i += 1
            continue

        if text == PAGEBREAK:
            # A page break mid-sentence must not split the paragraph.
            if buf and TERMINAL.search(buf[-1]):
                emit_para()
            elif buf:
                prev = "para"
            else:
                prev = None
            i += 1
            continue

        m = SECTION_RE.match(text)
        if m and len(text) <= 28:
            if buf:
                emit_para()
            await_sub = sec_sub.get(m.group(1))
            in_review = False
            blocks.append(("section", text))
            prev = "section"
            i += 1
            continue

        # The emitter prints the section's subtitle itself; drop the source line.
        if await_sub and norm(text) == norm(await_sub):
            await_sub = None
            i += 1
            continue

        if text == "REVIEW":
            if buf:
                emit_para()
            in_review = True
            blocks.append(("review", "REVIEW"))
            prev = "review"
            i += 1
            continue

        if text.startswith(EM_DASH) and len(text) <= 45:
            if buf:
                emit_para()
            attr = text.lstrip(EM_DASH + "^\u00ac\u2018' ").strip().rstrip(",")
            # Absorb a trailing source line ("... Feynman," / "Caltech 1974").
            nxt = cleaned[i + 1] if i + 1 < n else ""
            if (
                not in_review
                and nxt
                and nxt != PAGEBREAK
                and len(nxt) <= SUBTITLE_MAX
                and not TERMINAL.search(nxt)
            ):
                attr = f"{attr}, {nxt}"
                i += 1
            blocks.append(("byline" if in_review else "attrib", attr))
            in_review = False
            prev = "byline"
            i += 1
            continue

        name = matcher.match(text) if len(text) <= 40 else None
        if name is not None:
            if buf:
                emit_para()
            if await_sub and norm(await_sub) == norm(name):
                await_sub = None
                i += 1
                continue
            blocks.append(("label", name))
            in_review = False
            prev = "label"
            i += 1
            continue

        # Subtitle: a short unterminated line right under an essay title.
        if (
            prev == "label"
            and len(text) <= SUBTITLE_MAX
            and not TERMINAL.search(text)
            and i + 1 < n
            and cleaned[i + 1] not in ("", PAGEBREAK)
        ):
            if buf:
                emit_para()
            blocks.append(("subtitle", text))
            prev = "subtitle"
            i += 1
            continue

        buf.append(text)
        if TERMINAL.search(text) and widths[i] <= WRAP:
            emit_para()
            prev = None
        i += 1

    if buf:
        blocks.append(("para", " ".join(buf)))
    return blocks


# ---------------------------------------------------------------- emit
def emit(blocks: list[tuple[str, str]]) -> str:
    lookup = {n: (t, s) for n, t, s in SECTIONS}
    out: list[str] = []
    pending: list[str] = []

    def gap() -> None:
        while out and out[-1] == "":
            out.pop()
        if out:
            out.append("")

    def flush_pending() -> None:
        nonlocal pending
        if pending:
            out.extend(pending)
            pending = []

    for kind, text in blocks:
        if kind == "section":
            flush_pending()
            gap()
            m = SECTION_RE.match(text)
            num = m.group(1) if m else ""
            title, sub = lookup.get(num, (text, None))
            out += [f"## {num}. {title}", ""]
            if sub:
                out += [f"*{sub}*", ""]
            continue

        if kind == "review":
            flush_pending()
            gap()
            out += ["**Review**", ""]
            continue

        if kind == "byline":
            pending = [f"*{EM_DASH} {text}*", ""]
            continue

        if kind == "attrib":
            flush_pending()
            out += [f"*{EM_DASH} {text}*", ""]
            continue

        if kind == "label":
            flush_pending()
            gap()
            out += [f"### {text}", ""]
            continue

        if kind == "subtitle":
            flush_pending()
            out += [f"*{text}*", ""]
            continue

        flush_pending()
        out += [text, ""]

    flush_pending()
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------- main
def main() -> int:
    original = SRC.read_text(encoding="utf-8").split("\n")
    toc = extract_toc_names(original)
    print(f"TOC names extracted    : {len(toc)}")

    lines = drop_front_matter(original)
    lines, r1 = drop_headers_and_pagenums(lines)
    lines, r2 = drop_garbage(lines)
    lines = merge_split_headings(lines)
    lines = dehyphenate(lines)
    print(f"running headers removed: {len(r1)}   garbage removed: {len(r2)}")

    blocks = build_blocks(lines, toc)
    counts: dict[str, int] = {}
    for k, _ in blocks:
        counts[k] = counts.get(k, 0) + 1
    print(f"blocks                 : {counts}")

    md = emit(blocks)
    OUT.write_text(md, encoding="utf-8")
    print(f"\nwrote {OUT.name}: {len(md.split())} words, {md.count(chr(10))} lines")

    labels = [t for k, t in blocks if k == "label"]
    print(f"\nessay titles detected: {len(labels)}")
    missing = [n for n in toc if n not in labels]
    print(f"missing from body     : {missing if missing else 'none'}")

    if counts.get("label", 0) != 50 or counts.get("section", 0) != 8:
        print("\nSTRUCTURE CHECK FAILED", file=sys.stderr)
        return 1
    print("\nstructure check passed: 8 sections, 50 essays")
    return 0


if __name__ == "__main__":
    sys.exit(main())
