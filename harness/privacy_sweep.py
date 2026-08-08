#!/usr/bin/env python3
"""Content scan for personal data before the repository is made public.

Companion to `tools/harness_guards.py`, which checks *structure* (are the
ignore rules present, is anything personal tracked?). This checks *content*:
does any file that would ship contain something that looks like a real person's
details?

    python harness/privacy_sweep.py            # scan tracked files
    python harness/privacy_sweep.py --all      # scan the whole working tree
    python harness/privacy_sweep.py --explain  # also list what was allowed, and why

Exit code = number of hits. Zero is the release gate.

**The demo candidate is expected and allowed.** Riley Chen, `example.com`
addresses and the reserved `555-01xx` phone range are the fictional content this
project ships on purpose. Everything else that matches a personal-data shape is
reported.

The bias is deliberate: this reports too much rather than too little. A false
positive costs someone thirty seconds; a false negative publishes a phone
number. Add an allow entry with a reason rather than loosening a pattern.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Fictional values that ship on purpose.
ALLOWED_LITERALS = {
    "riley chen",
    "riley.chen@example.com",
    "+1 555-0142",
    "example-rileychen",
    "example-riley-chen",
    # The stock cover-letter template's placeholder LinkedIn URL, beside
    # `[YOUR NAME]` and `your.email@example.com`. It was previously excused by
    # a line-level placeholder rule that also excused real addresses sharing a
    # line with a placeholder; that rule is now scoped away from contact
    # labels, so this one names itself here instead of loosening a pattern.
    "www.linkedin.com/in/yourprofile",
    "linkedin.com/in/yourprofile",
}
ALLOWED_DOMAINS = ("example.com", "example.org", "example.net", "example.ca",
                   "example-", "localhost")

# Reserved-for-fiction phone ranges (NANP 555-01xx).
FICTIONAL_PHONE = re.compile(r"555-01\d{2}")

# Blocking: a hit here is personal data that must not ship. Zero of these is
# the release gate.
BLOCKING_PATTERNS = [
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("phone", re.compile(
        r"(?<![\w.])(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?![\w.])")),
    ("linkedin profile", re.compile(r"linkedin\.com/in/[\w-]+", re.I)),
    ("postal code (CA)", re.compile(r"\b[A-Z]\d[A-Z][ -]?\d[A-Z]\d\b")),
    ("street address", re.compile(
        r"\b\d{1,5}\s+\w+(?:\s+\w+)?\s+"
        r"(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Drive|Dr\.?|Boulevard|Blvd\.?)\b",
        re.I)),
    ("api key or token", re.compile(
        r"\b(?:sk-[A-Za-z0-9]{16,}|fc-[A-Za-z0-9]{16,}|gh[pousr]_[A-Za-z0-9]{16,}"
        r"|AKIA[0-9A-Z]{12,}|xox[baprs]-[A-Za-z0-9-]{10,})")),
]

# Advisory: reported for the owner to eyeball at the release gate, but not
# blocking.
#
# GitHub URLs were blocking in the first version of this script and produced 71
# hits, essentially all of them **required licence attribution** — the upstream
# author in CONTRIBUTING.md and CHANGELOG.md, the vendored humanizer's author,
# the portal CLI authors. That content must ship; NOTICE.md and README exist
# specifically to carry it. A check that fails the build on correct, mandatory
# content is a wrong check, and a gate that has to be waived every run stops
# being a gate.
#
# The category is kept rather than deleted, because a GitHub handle *is*
# identifying and the owner should see the list before flipping the repo
# public. `--strict` promotes these back to blocking.
ADVISORY_PATTERNS = [
    ("github url", re.compile(r"github\.com/[\w-]+(?:/[\w.-]+)?", re.I)),
]

# Files whose whole job is to describe these patterns.
SELF_REFERENTIAL = {
    "harness/privacy_sweep.py",
    "tests_harness/test_privacy.py",
}

SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".xlsx",
                 ".docx", ".ttf", ".otf", ".woff", ".woff2", ".ico", ".lock"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache", "build",
             "OpenFonts", "assets"}


# Categories where a documentation marker elsewhere on the line is NOT enough.
# These can identify or contact a real person, so only the match itself (or an
# explicit placeholder token) may excuse them. This split is the fix for the
# old rule, which let any line containing "test" or "example" ship a real email.
CONTACT_LABELS = {"email", "phone", "linkedin profile", "api key or token"}


def is_allowed(match: str, line: str, label: str = "") -> bool:
    lowered = match.lower()
    if lowered in ALLOWED_LITERALS:
        return True
    if any(domain in lowered for domain in ALLOWED_DOMAINS):
        return True
    if FICTIONAL_PHONE.search(match):
        return True
    # A placeholder rather than a value.
    #
    # This check is deliberately narrow, and it used to be far too wide: it
    # allowed EVERY match on any line containing the word "example" or "test".
    # A CHANGELOG entry reading "tested with jane.doe@realcompany.com" shipped
    # clean. For a gate whose stated bias is "report too much rather than too
    # little", that was the one rule pointing the other way.
    #
    # Now only explicit placeholder tokens excuse a line, and the documentation
    # vocabulary ("Example Company", "123 Hiring Street") must appear in the
    # MATCH ITSELF rather than merely somewhere on the line.
    # A placeholder token inside the MATCH itself always excuses it.
    if re.search(r"\[YOUR_|@@|<your|your[.\-_]|placeholder", lowered, re.I):
        return True
    # A documentation marker inside the MATCH itself always excuses it.
    if re.search(r"\b(example|test|sample|acme)\b", lowered):
        return True
    # A marker merely elsewhere on the LINE excuses only the shape-based
    # categories — a street-address or postal-code regex firing on
    # "123 Hiring Street\\Example City" in a template snippet. It never
    # excuses an email, phone number, profile URL or key: those are exactly
    # what a real leak looks like, and "test" appears near real data all the
    # time.
    #
    # The placeholder half of this used to run above the label split, which
    # quietly reopened the hole the split was written to close: one `your-`
    # anywhere on a line excused a real address on the same line.
    if label and label not in CONTACT_LABELS:
        if re.search(r"\[YOUR_|@@|<your|your[.\-_]|placeholder", line, re.I):
            return True
        if re.search(r"\b(example|test|sample|placeholder|template)\b", line, re.I):
            return True
    return False


def candidate_files(scan_all: bool) -> list[Path]:
    if scan_all:
        files = [p for p in ROOT.rglob("*") if p.is_file()]
    else:
        try:
            out = subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                                 cwd=str(ROOT), check=True).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            sys.exit(f"privacy_sweep: could not list tracked files: {exc}")
        files = [ROOT / line.strip() for line in out.splitlines() if line.strip()]
    keep = []
    for path in files:
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        keep.append(path)
    return sorted(keep)


def scan(scan_all: bool = False,
         strict: bool = False) -> tuple[list, list]:
    """Return (blocking_hits, advisory_hits), each (path, line, label, value)."""
    blocking: list[tuple[str, int, str, str]] = []
    advisory: list[tuple[str, int, str, str]] = []
    patterns = [(label, pattern, True) for label, pattern in BLOCKING_PATTERNS]
    patterns += [(label, pattern, strict) for label, pattern in ADVISORY_PATTERNS]

    for path in candidate_files(scan_all):
        relative = path.relative_to(ROOT).as_posix()
        if relative in SELF_REFERENTIAL:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            for label, pattern, blocks in patterns:
                for match in pattern.finditer(line):
                    value = match.group(0)
                    if is_allowed(value, line, label):
                        continue
                    (blocking if blocks else advisory).append(
                        (relative, number, label, value)
                    )
    return blocking, advisory


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan for personal data before publishing."
    )
    parser.add_argument("--all", action="store_true",
                        help="scan the whole working tree, not just tracked files")
    parser.add_argument("--explain", action="store_true",
                        help="also print what is deliberately allowed")
    parser.add_argument("--strict", action="store_true",
                        help="treat advisory categories (GitHub URLs) as blocking too")
    args = parser.parse_args(argv)

    hits, advisory = scan(scan_all=args.all, strict=args.strict)
    scope = "working tree" if args.all else "tracked files"

    if args.explain:
        print("Deliberately allowed (the fictional demo candidate):")
        for literal in sorted(ALLOWED_LITERALS):
            print(f"  - {literal}")
        print(f"  - any address on: {', '.join(ALLOWED_DOMAINS)}")
        print("  - phone numbers in the reserved 555-01xx fiction range")
        print("  - placeholder tokens ([YOUR_*], @@KEY@@, <your...>)\n")

    if advisory:
        # Grouped, not listed line by line: these are overwhelmingly repeated
        # attribution links, and 70 near-identical lines would bury the
        # blocking section that actually matters.
        by_value: dict[str, int] = {}
        for _, _, _, value in advisory:
            by_value[value] = by_value.get(value, 0) + 1
        print(f"Advisory - {len(advisory)} GitHub URL(s) across "
              f"{len(by_value)} distinct account(s)/repo(s).")
        print("Mostly required licence attribution. Worth an eyeball before going "
              "public; not blocking.")
        for value, count in sorted(by_value.items(), key=lambda kv: -kv[1]):
            print(f"    {count:>3}x  {value}")
        print()

    if not hits:
        print(f"privacy_sweep: OK - no personal data found in {scope}"
              f"{' (strict)' if args.strict else ''}.")
        return 0

    print(f"privacy_sweep: {len(hits)} blocking personal-data hit(s) in {scope}.")
    print("Each one is either real data that must not ship, or a false positive that "
          "deserves an allow entry with a reason - never a loosened pattern.\n")
    for relative, number, label, value in hits:
        print(f"  {relative}:{number}  [{label}]  {value}")
    # Capped, as fact_check.py already does. An uncapped count is an exit-status
    # wraparound waiting to happen: exactly 256 hits would have exited 0 and the
    # release gate would have reported a catastrophically dirty tree as clean.
    return min(len(hits), 100)


if __name__ == "__main__":
    sys.exit(main())
