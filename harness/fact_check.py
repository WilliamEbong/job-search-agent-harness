#!/usr/bin/env python3
"""Tier-1 deterministic fact checker for job application documents.

Reads `evidence/register.yaml` and checks CV / cover-letter text against it.
A claim that is not in the register is not claimable.

    python harness/fact_check.py cv/main_acme_analyst.tex cover_letters/cover_acme.tex
    python harness/fact_check.py --posting documents/applications/Acme_Analyst/job_posting.md draft.tex

Exit code = number of red lines (0 = OK).

Two boundaries worth being explicit about:

* **This checker judges facts, never phrasing.** Whether a reframing is
  persuasive, whether "led" is fair where the evidence says "supported" — that
  is the reviewer pass (Tier 2). Paraphrase stays completely free here.
* **Never weaken a check to make a draft pass.** The three legal resolutions
  are: fix the draft · confirm the fact and record it with `/fact` · fix the
  checker *and* pin a fixture proving the old defect. Editing the register to
  clear a red line is none of those.

Candidate-agnostic by construction: the technology lexicon and the positioning
constraint regexes live in `harness/fact_check_config.yaml`, and a constraint
family only runs when the user's own register declares a positioning_constraint
with that id.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HARNESS_DIR)
REGISTER = os.path.join(ROOT, "evidence", "register.yaml")
CONFIG = os.path.join(HARNESS_DIR, "fact_check_config.yaml")

# Units that make a bare number a factual claim rather than formatting noise.
#
# This is a whitelist on purpose: without it, page numbers, font sizes and
# postcodes would all read as claims. The cost is a stated ceiling — a numeral
# whose unit is not listed here is not checked at all (see
# test_numeral_with_an_unlisted_unit_is_a_known_ceiling). Add units when a real
# draft carries a claim past the gate; that strengthens the check.
NUMERAL_RE = re.compile(
    r"(?<![\w.])(\d[\d,]*\.?\d*)\s*(%|percent|\+?\s*years?|\+?\s*months?|hours?|minutes?|"
    r"days?|weeks?|people|staff|members|clients|projects|samples|students|users|"
    r"records|sites|volunteers|households|participants|reports|applications|"
    r"[kKmM]?\s*(?:CAD|USD|EUR|GBP|\$))",
    re.IGNORECASE,
)
# A credential-shaped phrase: up to five capitalised words ending in a credential
# marker, or a well-known standalone designation.
CREDENTIAL_RE = re.compile(
    r"(?:[A-Z][\w+#/&-]*(?:[ -](?:of|in|for|the)?[ ]?[A-Z(][\w+#/&)-]*){0,5}[ ]"
    r"(?:Certified|Certificate|Certification|Diploma|Designation|Licence|License)\b"
    r"(?:[ ][A-Z][\w+#/&-]*){0,3}"
    r"|(?:Certified|Licensed)[ ][A-Z][\w+#/&-]*(?:[ ][A-Z][\w+#/&-]*){0,4}"
    r"|\b(?:PMP|CAPM|P\.Eng|PMI-ACP|CSM|CISSP|CompTIA|Six Sigma(?:[ ](?:Green|Black)[ ]Belt)?"
    r"|ITIL|PRINCE2)\b)"
)
DATE_RANGE_RE = re.compile(
    r"\b((?:19|20)\d{2})\s*(?:-|--|---|–|—|to|until)\s*((?:19|20)\d{2}|present|current)\b",
    re.I,
)

# "30 percent", "30 %" (what LaTeX "30\%" extracts as) and "30%" are the same
# claim. The register stores the "%" form, so fold every spelling onto it before
# comparing; without this, a registered metric written out in words reads as a
# fabrication. Regression pinned by test_percent_spellings_are_equivalent.
PERCENT_RE = re.compile(r"\s*(?:%|percent)(?![a-z])", re.I)


def _require_yaml():
    try:
        import yaml
    except ImportError:
        sys.exit(
            "fact_check: PyYAML is required to read the evidence register. "
            "Run: pip install -r requirements.txt"
        )
    return yaml


def load_register(path: str = REGISTER):
    yaml = _require_yaml()
    if not os.path.exists(path):
        sys.exit(
            f"fact_check: no evidence register at {path}.\n"
            "Run /setup to build one, or copy evidence/register.example.yaml "
            "to evidence/register.yaml to see the schema."
        )
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_config(path: str = CONFIG) -> dict:
    yaml = _require_yaml()
    if not os.path.exists(path):
        sys.exit(f"fact_check: missing configuration file {path}")
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def strip_latex(text: str) -> str:
    """Reduce .tex source to the prose a reader actually sees."""
    text = re.sub(r"(?m)^\s*%.*$", " ", text)  # comment lines
    text = re.sub(
        r"\\(?:usepackage|documentclass|input|include|newcommand|renewcommand|"
        r"definecolor|geometry|hypersetup|photo|makecvtitle|label|ref)\b[^\n]*",
        " ",
        text,
    )
    text = re.sub(r"\\href\{[^}]*\}", " ", text)  # keep link text, drop the URL
    text = re.sub(r"\\[a-zA-Z@]+\*?", " ", text)  # remaining commands
    text = re.sub(r"[{}$\\&~^_]", " ", text)
    return re.sub(r"\s+", " ", text)


def read_doc(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    return strip_latex(raw) if path.lower().endswith((".tex", ".cls", ".sty")) else raw


def norm(value) -> str:
    """Fold whitespace, dashes and case so spelling variants compare cleanly."""
    text = str(value).lower().replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'")
    return re.sub(r"\s+", " ", text).strip()


def words_of(value) -> str:
    return norm(value).replace(",", "")


def canon_numeral(value) -> str:
    """Normalized numeral, with every percentage spelling folded onto '%'."""
    return PERCENT_RE.sub("%", words_of(value))


def canon_plus(value) -> str:
    """Normalized numeral with any '+' and its spacing removed.

    NUMERAL_RE's unit group is `\\+?\\s*years?`, so a draft's "5+ years" yields
    the unit "+ years" and the candidate "5 + years" — which never matched a
    registered "5 years". Folding both sides onto the plus-free form fixes it
    without loosening what counts as a claim.
    """
    return re.sub(r"\s*\+\s*", " ", canon_numeral(value)).strip()


# --------------------------------------------------------------------- views


def registered_names(reg: dict) -> set[str]:
    """Every employer name, alias, title, credential, institution, project."""
    names: set[str] = set()
    for employer in reg.get("employers", []) or []:
        names.add(norm(employer.get("name", "")))
        names.update(norm(a) for a in employer.get("aliases", []) or [])
        for title in employer.get("titles", []) or []:
            names.add(norm(title.get("title", "")))
    for item in reg.get("education", []) or []:
        names.add(norm(item.get("institution", "")))
        names.add(norm(item.get("degree", "")))
    for cred in reg.get("credentials", []) or []:
        names.add(norm(cred.get("name", "")))
        names.update(norm(a) for a in cred.get("aliases", []) or [])
    for section in ("projects", "public_repositories", "research", "leadership"):
        for item in reg.get(section, []) or []:
            names.add(norm(item.get("name", "")))
    names.discard("")
    return names


def registered_technologies(reg: dict) -> set[str]:
    tech: set[str] = set()
    for item in reg.get("technologies", []) or []:
        tech.add(norm(item.get("name", "")))
        tech.update(norm(a) for a in item.get("aliases", []) or [])
    rules = reg.get("technology_claim_rules", {}) or {}
    for group in ("direct", "ai_assisted", "ai-assisted", "familiarity_only"):
        for item in rules.get(group, []) or []:
            tech.add(norm(item))
    for project in reg.get("projects", []) or []:
        tech.update(norm(x) for x in project.get("technologies", []) or [])
    tech.discard("")
    return tech


def registered_numerals(reg: dict) -> set[str]:
    """Every numeric value the register supports, plus aliases, normalized.

    Employment start/end YEARS are deliberately not included. They used to be,
    which meant any claim whose number happened to equal a year someone started
    a job cleared the gate: "supported 2,020 participants" passed because a role
    began in 2020. Date ranges are check 2's job; this set is about metrics.
    """
    vals: set[str] = set()
    for metric in reg.get("metrics", []) or []:
        for raw in [metric.get("value", "")] + list(metric.get("aliases", []) or []):
            vals.add(words_of(raw))
            vals.add(canon_numeral(raw))
            # "5+ years" in a draft is the same claim as a registered
            # "5 years": the unit group captures the "+", so without this the
            # plus-form never matched anything and read as a fabrication.
            vals.add(canon_plus(raw))
    vals.discard("")
    return vals


def employment_spans(reg: dict) -> list[tuple[str, int, int]]:
    """(label, first_year, last_year) for employers, degrees, research, roles."""
    spans: list[tuple[str, int, int]] = []
    for employer in reg.get("employers", []) or []:
        for title in employer.get("titles", []) or []:
            start, end = str(title.get("start", "")), str(title.get("end", ""))
            if start[:4].isdigit():
                spans.append((
                    employer.get("name", "?"),
                    int(start[:4]),
                    int(end[:4]) if end[:4].isdigit() else 9999,
                ))
    for section in ("education", "research", "leadership"):
        for item in reg.get(section, []) or []:
            start, end = str(item.get("start", "")), str(item.get("end", ""))
            if start[:4].isdigit():
                label = item.get("institution") or item.get("name") or item.get("degree", "?")
                spans.append((
                    label,
                    int(start[:4]),
                    int(end[:4]) if end[:4].isdigit() else 9999,
                ))
    return spans


def credential_rules(reg: dict) -> list[tuple[list[str], str]]:
    """Credentials that may never render without a qualifier."""
    out = []
    for cred in reg.get("credentials", []) or []:
        status = str(cred.get("status", "")).lower()
        if status.startswith(("in-progress", "in progress")):
            qualifier = cred.get("qualifier_required") or "in progress"
            names = [cred.get("name", "")] + list(cred.get("aliases", []) or [])
            out.append(([n for n in names if n], qualifier))
    return out


def active_constraints(reg: dict, config: dict) -> list[tuple[str, str, str, list[str]]]:
    """(constraint_id, compiled_regex_source, description, exemption_markers).

    This is the candidate-agnostic gate: a pattern family from the config runs
    only when the user's own register declares a positioning_constraint with a
    matching id. A candidate who genuinely is a software engineer has no
    `programming_claims` constraint, so none of its patterns can ever fire.
    """
    declared = {
        str(c.get("id", "")).strip()
        for c in (reg.get("positioning_constraints", []) or [])
        if c.get("id")
    }
    families = config.get("constraint_patterns", {}) or {}
    active = []
    for constraint_id, family in families.items():
        if constraint_id not in declared:
            continue
        markers = [norm(m) for m in (family.get("exemption_markers", []) or [])]
        for pattern in family.get("patterns", []) or []:
            regex = pattern.get("regex")
            if regex:
                active.append((constraint_id, regex, pattern.get("description", ""), markers))
    return active


# -------------------------------------------------------------------- checks


def check(paths, posting_text: str = "", register_path: str = REGISTER,
          config_path: str = CONFIG):
    reg = load_register(register_path)
    config = load_config(config_path)

    names = registered_names(reg)
    techs = registered_technologies(reg)
    numerals = registered_numerals(reg)
    spans = employment_spans(reg)
    creds = credential_rules(reg)
    constraints = active_constraints(reg, config)
    lexicon = config.get("tech_lexicon", []) or []
    case_sensitive = {str(x) for x in (config.get("case_sensitive_lexicon", []) or [])}

    posting = norm(posting_text)
    red: list[tuple[str, str, str]] = []

    for path in paths:
        text = read_doc(path)
        low = norm(text)
        where = os.path.basename(path)

        # 1. Numerals with units must exist in the register or come from the posting.
        for match in NUMERAL_RE.finditer(text):
            value, unit = match.group(1), match.group(2)
            claim = norm(match.group(0))
            candidates = {
                words_of(value),
                words_of(value + " " + unit),
                claim,
                canon_numeral(claim),
                canon_numeral(value + " " + unit),
                canon_plus(claim),
                canon_plus(value + " " + unit),
            }
            if candidates & numerals:
                continue
            # Posting-derived numbers (salary, req ID, "3 to 5 years") are fine,
            # but the number must appear as its OWN token. A bare substring test
            # lets a posting containing "2047" silently clear a claimed "47
            # percent". Regression pinned by
            # test_posting_whitelist_requires_a_whole_number.
            if posting and (
                re.search(r"(?<![\d.,])%s(?![\d.,])" % re.escape(value), posting)
                or claim in posting
            ):
                continue
            red.append((where, claim, "no registered metric has this value"))

        # 2. Date ranges must sit inside a registered span — and where the
        #    sentence names an entity, inside THAT entity's span.
        #
        #    Matching against any span let "Acme Corp, 2015 - 2016" pass on the
        #    strength of a university course that ran 2014-2018. The span
        #    labels were collected and then never used.
        for match in DATE_RANGE_RE.finditer(text):
            start = int(match.group(1))
            end_raw = match.group(2)
            end = 9999 if not end_raw[:4].isdigit() else int(end_raw[:4])

            window = norm(text[max(0, match.start() - 200): match.end() + 200])
            named = [(label, s, x) for label, s, x in spans
                     if label and norm(label) in window]
            # An entity named nearby narrows the check to its own spans; with
            # no entity in sight, fall back to the any-span behaviour so a
            # skills-section date does not red-line spuriously.
            applicable = named or spans

            if any(s <= start and end <= x for _, s, x in applicable):
                continue
            if end == 9999 and any(s <= start <= x for _, s, x in applicable):
                # "2015 - present" is only honest if a span containing 2015 is
                # itself still open. Previously any span that merely STARTED in
                # 2015 satisfied this, so a role that ended in 2016 could be
                # rendered as ongoing.
                if any(s <= start and x == 9999 for _, s, x in applicable):
                    continue
            reason = ("date range is not contained in any registered "
                      "employment, education or project span")
            if named:
                reason = ("date range does not fit the registered span for "
                          + ", ".join(sorted({label for label, _, _ in named})))
            elif any(s <= start for _, s, _ in spans) and any(end <= x for _, _, x in spans):
                reason = ("date range spans two separate registered periods "
                          "rather than sitting inside one")
            red.append((where, match.group(0), reason))

        # 3. Unregistered technologies (posting keywords leaking into the draft).
        for tech in lexicon:
            if norm(tech) in techs:
                continue
            # Entries listed as case-sensitive are ordinary English words too
            # ("go", "spring", "react"), so they are matched against the
            # original text with case intact. Matching them in the lowercased
            # copy reported "the spring sampling programme" as a claim to the
            # Spring framework. Real keyword stuffing capitalises the name and
            # is still caught.
            if str(tech) in case_sensitive:
                haystack, needle = text, str(tech)
            else:
                haystack, needle = low, str(tech).lower()
            if re.search(r"(?<![\w-])" + re.escape(needle) + r"(?![\w-])", haystack):
                red.append((
                    where, str(tech),
                    "technology is not in the register - it may not be claimed as used",
                ))

        # 4. In-progress credentials may never render without their qualifier —
        #    at EVERY occurrence, not just the first.
        #
        #    The old check used low.find(), so a CV reading "PMP (in progress)"
        #    in the summary and a bare "PMP" in the skills list passed clean.
        #    The bare one is the rendering an employer reads as earned.
        for aliases, qualifier in creds:
            flagged = False
            for alias in aliases:
                if flagged:
                    break
                needle = norm(alias)
                if not needle:
                    continue
                for occurrence in re.finditer(re.escape(needle), low):
                    idx = occurrence.start()
                    window = low[max(0, idx - 120): idx + len(needle) + 160]
                    if (norm(qualifier) in window or "in progress" in window
                            or "in-progress" in window):
                        continue
                    red.append((
                        where, alias,
                        'credential is in progress and must not render without "%s"'
                        % qualifier,
                    ))
                    flagged = True
                    break

        # 5. Credential-shaped phrases must name a registered credential or degree.
        for match in CREDENTIAL_RE.finditer(text):
            phrase = norm(match.group(0))
            if any(name and name in phrase for name in names):
                continue
            if any(phrase in name for name in names if name):
                continue
            red.append((where, match.group(0).strip(), "credential is not in the register"))

        # 6. Positioning constraints declared by this candidate's own register.
        for constraint_id, regex, description, markers in constraints:
            for match in re.finditer(regex, low):
                window = low[max(0, match.start() - 160): match.end() + 160]
                if any(marker in window for marker in markers):
                    continue
                red.append((
                    where, match.group(0).strip(),
                    f"{constraint_id} constraint: {description}",
                ))

    return red, reg


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Tier-1 fact check against evidence/register.yaml"
    )
    parser.add_argument("files", nargs="+", help=".tex or text files to check")
    parser.add_argument(
        "--posting",
        help="archived posting text; numbers appearing in it (salary, req-ID) are allowed",
    )
    parser.add_argument("--register", default=REGISTER)
    parser.add_argument("--config", default=CONFIG)
    args = parser.parse_args(argv)

    posting_text = ""
    if args.posting and os.path.exists(args.posting):
        posting_text = read_doc(args.posting)

    missing = [f for f in args.files if not os.path.exists(f)]
    if missing:
        sys.exit("fact_check: file not found: " + ", ".join(missing))

    red, _ = check(args.files, posting_text, args.register, args.config)

    if not red:
        print("OK - %d file(s) checked, no red lines." % len(args.files))
        return 0

    # Wording matters here. "FABRICATION-RISK", aimed at a job seeker reading
    # about their own life, accuses them of lying when the usual cause is that
    # a true fact is simply not recorded yet — and it buried that resolution
    # third. The gate is exactly as strict; it just leads with the likely cause.
    print("%d unsupported claim(s). This package is on hold until each one is "
          "resolved." % len(red))
    print()
    print("Usually this means the fact is true and just is not recorded yet.")
    print("  1. True? Confirm it:  /fact <the fact, in your own words>")
    print("  2. Overstated? Fix the draft and re-run.")
    print("  3. Checker wrong about this whole class of text? Fix")
    print("     harness/fact_check.py and add a fixture pinning the correction.")
    print()
    print("Editing the register to silence a line is not on that list.\n")
    for index, (where, text, reason) in enumerate(red, 1):
        print('%2d. UNSUPPORTED: "%s" - %s  [%s]' % (index, text, reason, where))
    return min(len(red), 100)


if __name__ == "__main__":
    sys.exit(main())
