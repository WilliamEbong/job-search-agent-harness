#!/usr/bin/env python3
"""ATS check: what a parser reads from the CV, and which posting keywords it finds.

`/apply` Step 5d used to be prose the model executed by hand: run pdftotext,
eyeball the text, hand-build a keyword table. Skippable, slow and expensive in
tokens. This does the mechanical part deterministically. The model keeps the
one judgment a script cannot make: whether a `missing` keyword is something the
candidate truly has (add it, truthfully) or a genuine gap (leave it - never
stuff keywords).

    python harness/ats_check.py --cv cv/main_acme_analyst.pdf \\
        --posting documents/applications/Acme_Analyst/job_posting.md \\
        --tex cv/main_acme_analyst.tex --keywords cv/main_acme_analyst.keywords.txt

Text comes from `pdftotext -layout` when it is on PATH, else pypdf. A `.tex` CV
goes through tex_to_md's moderncv converter and `.md`/`.txt` are read as is;
only a PDF is checked for parseability, because only a PDF has a text layer.
`harness/apply_package.py` runs this for every package and writes the result to
`ats_report.md`.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HARNESS_DIR))
import tex_to_md  # noqa: E402

MAX_KEYWORDS = 30
# Fewer letters and digits than this is no text layer at all: an image-only
# scan, or text converted to outlines. A one-page CV carries thousands.
MIN_TEXT = 50
WEIGHT = {"required": 2, "preferred": 1}
CREDIT = {"covered": 1.0, "synonym-only": 0.5, "missing": 0.0}

EPILOG = r"""keywords file, one per line ('#' starts a comment):
  required: spreadsheet | Excel    the posting's exact term; synonyms after '|'
  preferred: Power BI
  GIS                              a bare line is required
Without --keywords the keywords are extracted heuristically from the posting.

parseability (PDF only): a text layer exists; no (cid:NN) markers or U+FFFD;
the \email and \phone from --tex appear as text (phone compared on digits);
every \cventry year is present. Warnings, not failures: section headings out
of source order, en-dash date ranges.

status: covered | synonym-only | missing. Score: required weigh 2, preferred 1;
covered counts 1, synonym-only 0.5.
exit: 0 parse OK (any coverage), 1 parse failure, 2 usage or input error.
Coverage never fails the run - a low score can be an honest gap."""


class InputError(Exception):
    """A missing or unusable input: exit 2, never a parse failure."""


# --- text ------------------------------------------------------------------

def decode(raw: bytes) -> str:
    """pdftotext's UTF-8 output as text.

    MiKTeX ships xpdf's pdftotext, which writes characters outside the Basic
    Multilingual Plane - moderncv's contact and bullet icons - as CESU-8
    surrogate halves. Strict UTF-8 rejects them and errors="replace" turns them
    into U+FFFD: a false parse failure on a clean stock CV. Decode the halves,
    then pair them.
    """
    try:
        text = raw.decode("utf-8", "surrogatepass")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", "replace")
    return text.encode("utf-16", "surrogatepass").decode("utf-16", "replace")


def pdf_text(path: Path) -> tuple[str, str]:
    """(text layer, extractor name). pdftotext -layout first, pypdf second."""
    exe = shutil.which("pdftotext")
    if exe:
        done = subprocess.run([exe, "-layout", "-enc", "UTF-8", str(path), "-"],
                              capture_output=True)
        if done.returncode == 0:
            return decode(done.stdout).replace("\r\n", "\n"), "pdftotext -layout"
    try:
        from pypdf import PdfReader
    except ImportError:
        raise InputError("pdftotext is not on PATH and pypdf is not installed "
                         "(pip install -r requirements.txt)") from None
    name = "pypdf (pdftotext could not read it)" if exe else "pypdf"
    try:
        return "\n".join(page.extract_text() or ""
                         for page in PdfReader(str(path)).pages), name
    except Exception as exc:  # an unreadable PDF has no text layer; report it
        return "", f"{name}: unreadable ({exc})"


def tex_text(path: Path) -> str:
    """CV body text via tex_to_md's moderncv converter.

    Not tex_to_md.convert(): that prepends contact details from the evidence
    register and exits when there is none. Neither belongs in a keyword match
    against this one CV.
    """
    tex = tex_to_md.strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    body = re.search(r"\\begin\{document\}(.*?)\\end\{document\}", tex, flags=re.S)
    body_text = (body.group(1) if body else tex).split("\\makecvtitle", 1)[-1]
    return "\n".join(tex_to_md.convert_cv(body_text))


def tex_facts(path: Path) -> dict:
    """What the CV source says the text layer must contain."""
    tex = tex_to_md.strip_comments(path.read_text(encoding="utf-8", errors="replace"))

    def args(pattern: str) -> list[str]:
        return [value for value in (tex_to_md.inline(arg) for arg in re.findall(pattern, tex))
                if value]

    dates = " ".join(re.findall(r"\\cventry\{([^{}]*)\}", tex))
    return {
        "emails": args(r"\\email\{([^{}]*)\}"),
        "phones": args(r"\\phone(?:\[[^\]]*\])?\{([^{}]*)\}"),
        "years": sorted(set(re.findall(r"\b(?:19|20)\d{2}\b", dates))),
        "sections": args(r"\\section\*?\{([^{}]*)\}"),
    }


# --- parseability ------------------------------------------------------------

YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
EN_DASH_RANGE = re.compile(
    r"\b(?:19|20)\d{2}\s*[\u2013\u2014]\s*(?:(?:19|20)\d{2}|present|now|current)", re.I)


def parse_check(text: str, facts: dict | None) -> dict:
    """Failures make the CV unpresentable; warnings and notes do not."""
    failures: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []
    if len(re.findall(r"\w", text)) < MIN_TEXT:
        failures.append("no text layer")
    if "(cid:" in text:
        failures.append("(cid:) markers")
    if "\ufffd" in text:
        failures.append("U+FFFD characters")
    flat = " ".join(text.split()).casefold()

    if facts is None:
        notes.append("no --tex: email, phone, per-entry years and section order not checked")
        if not YEAR.search(text):
            failures.append("no years in the text layer")
    else:
        if not facts["emails"]:
            notes.append("no \\email in --tex: email not checked")
        if any(email.casefold() not in flat for email in facts["emails"]):
            failures.append("email not in the text layer")
        # Per line, digits only: "+1 555-0142" and "+1 (555) 0142" are the
        # same number, and a whole-document digit string would find any number
        # somewhere by accident.
        line_digits = [re.sub(r"\D", "", line) for line in text.splitlines()]
        phones = [re.sub(r"\D", "", phone) for phone in facts["phones"]]
        if not any(phones):
            notes.append("no phone number in --tex: phone not checked")
        if any(p and not any(p in line for line in line_digits) for p in phones):
            failures.append("phone not in the text layer")
        if not facts["years"]:
            notes.append("no years in the \\cventry dates of --tex: dates not checked")
        missing = [year for year in facts["years"] if not re.search(rf"\b{year}\b", text)]
        if missing:
            failures.append("years missing: " + ", ".join(missing))
        # Reading order, mechanically: the source's section headings must come
        # out of the text layer in the same order. A multi-column template that
        # interleaves its columns fails this; the stock banking style passes.
        at = 0
        for heading in facts["sections"]:
            key = " ".join(heading.split()).casefold()
            found = flat.find(key, at)
            if found >= 0:
                at = found + len(key)
            else:
                state = "out of source order" if key in flat else "not found"
                warnings.append(f"section heading '{heading}' {state} in the text layer")
    if EN_DASH_RANGE.search(text):
        warnings.append("en-dash date range: write \\cventry dates with an ASCII "
                        "hyphen - some ATS imports drop the end date")
    return {"checked": True, "failures": failures, "warnings": warnings, "notes": notes}


# --- matching ------------------------------------------------------------------

# A word (keeping C++, C#, R&D and driver's whole) or a single punctuation mark.
# Hyphens and dashes separate, so chain-of-custody matches "chain of custody";
# `.` and `/` stay tokens, so Node.js, .NET and CI/CD match only as written.
TOKEN = re.compile(r"\w+(?:['\u2019&]\w+)*[+#]*|[^\w\s'\u2019\-\u2010\u2011\u2013\u2014]")


def stem(word: str) -> str:
    """Fold a simple plural so `dashboard` and `dashboards` match both ways."""
    # ponytail: plural s/es/ies only - analysis/analyses and -ing/-ed forms do
    # not fold. A synonym after `|` in the keywords file covers them.
    if len(word) <= 3 or not word.isalpha():
        return word
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith(("sses", "xes", "zes", "ches", "shes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def tokens(text: str) -> list[tuple[str, int, int]]:
    """(folded token, start, end) for every token in `text`."""
    return [(stem(m.group().casefold().replace("'", "").replace("\u2019", "")),
             m.start(), m.end()) for m in TOKEN.finditer(text)]


def stems(text: str) -> list[str]:
    return [token for token, _, _ in tokens(text)]


def find_all(hay: list[str], needle: list[str]) -> list[int]:
    """Every index where the token run `needle` starts in `hay`."""
    size = len(needle)
    if not size:
        return []
    return [i for i in range(len(hay) - size + 1) if hay[i:i + size] == needle]


def snippet(text: str, start: int, end: int, room: int = 30) -> str:
    left, right = max(0, start - room), min(len(text), end + room)
    core = " ".join(text[left:right].split())
    return ("..." if left else "") + core + ("..." if right < len(text) else "")


def match(text: str, keywords: list[dict]) -> list[dict]:
    """One row per keyword: covered, synonym-only (a synonym hit) or missing."""
    found = tokens(text)
    hay = [token for token, _, _ in found]
    rows = []
    for keyword in keywords:
        row = {"keyword": keyword["keyword"], "priority": keyword["priority"],
               "status": "missing", "matched": "", "where": ""}
        for n, term in enumerate([keyword["keyword"], *keyword.get("synonyms", [])]):
            needle = stems(term)
            hits = find_all(hay, needle)
            if hits:
                first, last = hits[0], hits[0] + len(needle) - 1
                more = f" (+{len(hits) - 1} more)" if len(hits) > 1 else ""
                row.update(status="covered" if n == 0 else "synonym-only", matched=term,
                           where=snippet(text, found[first][1], found[last][2]) + more)
                break
        rows.append(row)
    return rows


# --- keywords ------------------------------------------------------------------

def load_keywords(path: Path) -> list[dict]:
    """The drafter's list: `required: term | synonym`, `preferred: term`, bare = required."""
    keywords, seen = [], set()
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = re.sub(r"(?:^|\s)#.*", "", raw).strip()  # C# survives: no space before #
        priority = "required"
        label = re.match(r"(required|preferred)\s*:\s*(.*)", line, re.I)
        if label:
            priority, line = label.group(1).lower(), label.group(2)
        terms = [term.strip() for term in line.split("|") if term.strip()]
        key = " ".join(stems(terms[0])) if terms else ""
        if key and key not in seen:
            seen.add(key)
            keywords.append({"keyword": terms[0], "priority": priority,
                             "synonyms": terms[1:]})
    return keywords


PREFERRED_HEADING = re.compile(
    r"nice[- ]to[- ]have|preferred|bonus|\bplus\b|\bassets?\b|desirable|advantageous", re.I)
REQUIRED_HEADING = re.compile(
    r"requirement|qualification|must[- ]?have|skills|experience|about you|who you are"
    r"|you(?:['\u2019]ll| will)? (?:bring|need|have)", re.I)
BULLET = re.compile(r"^\s*(?:[-*\u2022\u00b7\u25aa\u25e6\u2013]|\d+[.)])\s+")
# Inside one requirement: list separators and the words that join two skills.
SPLIT = re.compile(
    r"[,;:()\[\]/]|\.(?:\s|$)|\s[-\u2013\u2014]\s"
    r"|\b(?:and|or|for|with|in|including|such as|like|e\.g\.?|i\.e\.?|etc)\b", re.I)
YEARS = re.compile(
    r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*\+?\s*"
    r"(?:or more\s+|plus\s+)?(?:years?|yrs?)\b['\u2019]?(?:\s+of)?(?:\s+(?:experience|working))?",
    re.I)
LEADING = re.compile(
    r"^(?:a|an|the|to|of|and|or|any|strong|excellent|proven|demonstrated|demonstrable|solid"
    r"|good|great|advanced|basic|valid|hands-on|deep|minimum|relevant|previous|prior"
    r"|professional|modern"
    r"|(?:working )?knowledge of|proficiency(?: in| with)?|familiarity(?: with)?|ability to"
    r"|understanding of|experience|exposure to|expertise(?: in)?|background(?: in)?"
    r"|fluency(?: in)?|fluent(?: in)?|comfortable(?: with)?|track record of)\s+", re.I)
TRAILING = re.compile(
    r"\s+(?:(?:is )?(?:a plus|an asset|desirable|preferred|required)|skills?|tools?"
    r"|software|experience|knowledge|awareness|scripting|programming)$", re.I)
TECH = re.compile(
    r"(?<![\w.])(?:[A-Za-z]+\+\+|[A-Za-z]#|\.NET|[A-Za-z]+\.js|[A-Z]{1,4}/[A-Z]{1,4}"
    r"|ISO ?\d{3,5}|[A-Z][a-z]+[A-Z][A-Za-z]*|[A-Z][A-Z0-9]{1,5})(?![\w+#])")
NOT_TECH = {"AND", "OR", "THE", "NOT", "WE", "YOU", "OUR", "HR", "EEO", "FTE", "USA",
            "UK", "EU", "US", "ID", "OK", "AM", "PM", "CAD", "USD", "EUR", "GBP",
            "DKK", "NOK", "SEK", "CHF", "AUD"}
STOPWORDS = set("""
a an the and or of to in for with on at by from as is are be been will would can could
should may must our we you your us this that these those it its their they who what which
when where how all any some more most other others such into about across through per via
not no if than then also etc have has had do does able ability experience knowledge skill
skills degree field similar equivalent related relevant strong excellent good great proven
demonstrated solid advanced basic year years plus minimum preferred required requirement
requirements qualification qualifications familiarity proficiency understanding exposure
expertise background fluent fluency work working role team job position candidate
including using use well new within level high professional
""".split())


def heading_of(line: str) -> str | None:
    """The heading text when `line` is a heading, else None."""
    stripped = line.strip()
    if not stripped or BULLET.match(stripped):
        return None
    marked = re.match(r"#{1,6}\s+(.*)", stripped)
    if marked:
        return marked.group(1).strip("*_ :")
    bare = stripped.strip("*_ ").rstrip(":").strip("*_ ")
    words = len(bare.split())
    if words <= 8 and (stripped.endswith(":")
                       or (stripped[:2] in ("**", "__") and stripped.rstrip(":")[-2:] in ("**", "__"))):
        return bare
    # A plain short line like "Requirements" or "Nice to have" - but not a
    # bullet-less item like "Experience with GIS".
    if (words <= 4 and re.match(r"(?:\w+\s+)?(?:" + PREFERRED_HEADING.pattern + "|"
                                + REQUIRED_HEADING.pattern + ")", bare, re.I)
            and not re.search(r"\b(?:with|in|of|for)\b|[.,;]", bare, re.I)):
        return bare
    return None


def section_items(posting: str) -> list[tuple[str, str]]:
    """(priority, item text) for every item under a required/preferred heading."""
    items: list[list[str]] = []
    section, current, bulleted = None, None, False
    for line in posting.splitlines():
        head, stripped = heading_of(line), line.strip()
        if (head is None and section and current is None and bulleted and stripped
                and not BULLET.match(line) and len(stripped.split()) <= 5
                and not stripped.endswith((".", ",", ";"))):
            head = stripped  # a plain heading ("Benefits") after a bulleted list
        if head is not None:
            section = ("preferred" if PREFERRED_HEADING.search(head)
                       else "required" if REQUIRED_HEADING.search(head) else None)
            current, bulleted = None, False
        elif not stripped:
            current = None
        elif section:
            body = BULLET.sub("", line).strip()
            if BULLET.match(line) or current is None:
                current = [section, body]
                items.append(current)
                bulleted = bulleted or bool(BULLET.match(line))
            else:  # a wrapped bullet's continuation line
                current[1] += " " + body
    return [(priority, text) for priority, text in items]


def chunks(item: str) -> list[str]:
    """1-4-word skill phrases from one requirement line."""
    item = YEARS.sub(" ", item.replace("**", "").replace("__", "").replace("`", ""))
    item = re.sub(r"\b([A-Z]{1,4})/([A-Z]{1,4})\b", "\\1\x00\\2", item)  # keep QA/QC whole
    out = []
    for part in SPLIT.split(item):
        # Trailing periods only: a leading one is .NET's.
        part = part.replace("\x00", "/").strip(" -*_'\"\u2019\u2013\u2014").rstrip(" .")
        while True:
            shorter = LEADING.sub("", part).strip()
            if shorter == part:
                break
            part = shorter
        part = TRAILING.sub("", part).rstrip(" .")
        words = part.split()
        if (1 <= len(words) <= 4 and re.search(r"[A-Za-z]", part)
                and not re.search(r"[%$\u20ac\u00a3]", part)
                and not all(word.casefold() in STOPWORDS for word in words)):
            out.append(part)
    return out


def extract_keywords(posting: str) -> list[dict]:
    """Required/preferred keywords from the posting itself - the fallback path."""
    # ponytail: English section headings, filler words and stopwords only, and
    # no synonyms. The drafter's keywords file is the primary path, and it is
    # how other languages (or a Danish posting against an English CV) work.
    posting = re.sub(r"<!--.*?-->", " ", posting, flags=re.S)  # hidden text is not the ad
    found: list[dict] = []
    seen: set[str] = set()

    def add(term: str, priority: str) -> None:
        key = " ".join(stems(term))
        if key and key not in seen:
            seen.add(key)
            found.append({"keyword": term, "priority": priority, "synonyms": []})

    items = section_items(posting)
    for priority, text in items:
        for part in chunks(text):
            add(part, priority)
    # Tech-shaped tokens a long clause would otherwise hide (C++, CI/CD, GIS),
    # unless a phrase already holds them ("Power BI" covers "BI").
    sources = items or [("required", posting)]
    phrases = [stems(k["keyword"]) for k in found]
    for priority, text in sources:
        for term in TECH.findall(text):
            if term not in NOT_TECH and not any(find_all(p, stems(term)) for p in phrases):
                add(term, priority)
    if not items:
        # No recognisable sections: two-word phrases the posting repeats.
        toks = tokens(posting)
        pairs: Counter = Counter()
        surface: dict = {}
        for (a, start, _), (b, _, end) in zip(toks, toks[1:]):
            if all(t.isalpha() and len(t) > 2 and t not in STOPWORDS for t in (a, b)):
                pairs[(a, b)] += 1
                surface.setdefault((a, b), " ".join(posting[start:end].split()))
        for pair, count in pairs.items():
            if count >= 2:
                add(surface[pair], "required")
    ordered = ([k for k in found if k["priority"] == "required"]
               + [k for k in found if k["priority"] == "preferred"])
    return ordered[:MAX_KEYWORDS]


# --- the check -------------------------------------------------------------------

def check(cv: Path, posting: Path, keywords: Path | None = None,
          tex: Path | None = None) -> dict:
    """Run every check. The result is what --json prints."""
    for path, flag in ((cv, "--cv"), (posting, "--posting"), (keywords, "--keywords"),
                       (tex, "--tex")):
        if path is not None and not path.is_file():
            raise InputError(f"{flag} {path}: no such file")
    kind = cv.suffix.lower()
    if kind == ".pdf":
        text, extractor = pdf_text(cv)
        if tex is None and cv.with_suffix(".tex").is_file():
            tex = cv.with_suffix(".tex")  # /apply compiles beside the source
        parse = parse_check(text, tex_facts(tex) if tex else None)
    elif kind in (".tex", ".md", ".txt"):
        if kind == ".tex":
            text, extractor = tex_text(cv), "tex_to_md"
        else:
            text, extractor = cv.read_text(encoding="utf-8", errors="replace"), "as is"
        parse = {"checked": False, "failures": [], "warnings": [],
                 "notes": [f"{kind} input: parseability needs the compiled PDF"]}
    else:
        raise InputError(f"--cv must be .pdf, .tex, .md or .txt, not {cv.name}")

    posting_text = posting.read_text(encoding="utf-8", errors="replace")
    if keywords:
        wanted = load_keywords(keywords)
        source = f"drafter's list ({keywords.name})"
    else:
        wanted = extract_keywords(posting_text)
        source = "extracted from the posting (no keywords file)"
    if not wanted:
        parse["notes"].append("no keywords found - write a keywords file")
    rows = match(text, wanted)

    counts = {p: {"covered": sum(1 for r in rows if r["priority"] == p and r["status"] == "covered"),
                  "total": sum(1 for r in rows if r["priority"] == p)} for p in WEIGHT}
    total = sum(WEIGHT[r["priority"]] for r in rows)
    score = (round(100 * sum(WEIGHT[r["priority"]] * CREDIT[r["status"]] for r in rows) / total)
             if total else None)
    result = {"cv": str(cv), "posting": str(posting), "tex": str(tex) if tex else None,
              "extractor": extractor, "keywords_source": source, "parse": parse,
              "required": counts["required"], "preferred": counts["preferred"],
              "score": score, "keywords": rows}
    result["summary"] = summary(result)
    return result


def summary(result: dict) -> str:
    parse = result["parse"]
    if not parse["checked"]:
        state = "parse n/a (not a PDF)"
    elif parse["failures"]:
        state = f"parse FAIL ({'; '.join(parse['failures'])})"
    else:
        state = "parse OK"
    req, pref = result["required"], result["preferred"]
    score = "n/a" if result["score"] is None else f"{result['score']}%"
    return (f"ATS: {state} \u00b7 required {req['covered']}/{req['total']} \u00b7 "
            f"preferred {pref['covered']}/{pref['total']} \u00b7 score {score}")


def missing(result: dict, priority: str) -> list[str]:
    return [r["keyword"] for r in result["keywords"]
            if r["priority"] == priority and r["status"] == "missing"]


def render_brief(result: dict) -> str:
    """Summary, then what to act on: synonym hits (an ATS often matches literally, so
    use the posting's term where it is true) and misses."""
    lines = [result["summary"]]
    for priority in WEIGHT:
        near = [f'{r["keyword"]} (as "{r["matched"]}")' for r in result["keywords"]
                if r["priority"] == priority and r["status"] == "synonym-only"]
        if near:
            lines.append(f"synonym-only {priority}: " + "; ".join(near))
        if missing(result, priority):
            lines.append(f"missing {priority}: " + "; ".join(missing(result, priority)))
    if result["parse"]["warnings"]:
        lines.append("warnings: " + "; ".join(result["parse"]["warnings"]))
    return "\n".join(lines)


def render_markdown(result: dict) -> str:
    parse = result["parse"]
    lines = [f"# ATS check - {Path(result['cv']).name}", "", result["summary"], "",
             f"- CV: `{result['cv']}` (text via {result['extractor']})",
             f"- Posting: `{result['posting']}`",
             f"- Keywords: {result['keywords_source']}", "", "## Parseability", ""]
    if parse["checked"] and not parse["failures"]:
        lines.append("- OK: a text layer, no `(cid:)` markers or U+FFFD, and every "
                     "contact detail and year the source names (see notes for skips)")
    lines += [f"- FAIL: {item}" for item in parse["failures"]]
    lines += [f"- WARN: {item}" for item in parse["warnings"]]
    lines += [f"- note: {item}" for item in parse["notes"]]
    if parse["failures"]:
        lines += ["", "Fix it in the CV source, recompile, re-run: print the email and "
                  "phone as text, not only as an icon or a link; `(cid:)` or U+FFFD "
                  "means a font without a Unicode map; no text layer means an "
                  "image-only or outlined PDF."]
    lines += ["", "## Keyword coverage", "",
              "| keyword | priority | status | where |", "|---|---|---|---|"]
    for row in result["keywords"]:
        where = (f'as "{row["matched"]}": ' if row["status"] == "synonym-only" else "") + row["where"]
        cells = [row["keyword"], row["priority"], row["status"], where]
        lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
    for priority in WEIGHT:
        if missing(result, priority):
            lines += ["", f"Missing {priority}: " + "; ".join(missing(result, priority))]
    lines += ["", "Next: mark each missing row **have it** (add it truthfully, preferring "
              "experience bullets; recompile; re-run) or **gap** (leave it - never stuff "
              "keywords). Prefer the posting's exact term over a synonym where it is true.",
              "", "Score: required weigh 2, preferred 1; covered counts 1, synonym-only 0.5."]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        # On a cp1252 pipe the summary's middle dot arrives as mojibake.
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        prog="ats_check.py", description=__doc__.splitlines()[0], epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cv", required=True,
                        help="the CV: a compiled .pdf (parseability + keywords) "
                             "or .tex/.md/.txt (keywords only)")
    parser.add_argument("--posting", required=True, help="the posting text, e.g. job_posting.md")
    parser.add_argument("--keywords", help="the drafter's keyword list (format below)")
    parser.add_argument("--tex", help="the CV source, for the contact, year and section "
                                      "checks (default: the .tex beside a PDF)")
    parser.add_argument("--out", help="also write the markdown report to this file")
    parser.add_argument("--brief", action="store_true",
                        help="print only the summary line and the missing keywords")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args(argv)
    try:
        result = check(Path(args.cv), Path(args.posting),
                       Path(args.keywords) if args.keywords else None,
                       Path(args.tex) if args.tex else None)
        if args.out:
            Path(args.out).write_text(render_markdown(result), encoding="utf-8")
    except (InputError, OSError) as exc:
        print(f"ats_check: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    elif args.brief:
        print(render_brief(result))
    elif args.out:
        print(f"{result['summary']}\nreport: {args.out}")
    else:
        print(render_markdown(result), end="")
    return 1 if result["parse"]["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
