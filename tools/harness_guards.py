#!/usr/bin/env python3
"""Structural CI guard for the harness's personal-data families.

Companion to upstream's `tools/security_guards.py`, which this file never
edits and never duplicates. Upstream guards upstream's families; this guards
the ones the harness added.

Deliberately kept separate from `harness/privacy_sweep.py`. They fail
differently and run at different times:

  * **this file** is a *structural* check — are the ignore rules present, is
    anything personal actually tracked? Fast, runs on every commit in CI.
  * **privacy_sweep** is a *content* scan — does any shipped file contain
    something that looks like personal data? Slower, runs at the release gate
    and in the fresh-install test.

A structural guard cannot see a phone number pasted into a README, and a
content scan cannot see a deleted gitignore rule. Merging them would lose one
of those.

Stdlib only. Exit 0 on success, 1 with a failure list otherwise.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []

# Ignore rules the harness added. Losing one of these silently re-exposes a
# whole family — the register, the preference answers, the continuity handoff.
REQUIRED_IGNORE_RULES = [
    "evidence/register.yaml",
    "evidence/backups/",
    "preferences.yaml",
    "companies.yaml",
    "state/",
    "shortlist.csv",
    "run_log.csv",
    "Job_Search_Tracker.xlsx",
    "backups/",
    "documents/writing_samples/**",
    "documents/portfolio/**",
]

# Paths that must never be tracked by git, whatever the ignore file says. A
# file already in the index stays tracked even after a matching rule is added,
# which is exactly how personal data gets committed by accident.
FORBIDDEN_TRACKED = [
    "evidence/register.yaml",
    "preferences.yaml",
    "companies.yaml",
    "shortlist.csv",
    "run_log.csv",
    "job_search_tracker.csv",
    "Job_Search_Tracker.xlsx",
]

FORBIDDEN_TRACKED_PREFIXES = [
    "state/",
    "backups/",
    "evidence/backups/",
    "documents/applications/",
    "documents/cv/",
    "documents/linkedin/",
    "documents/diplomas/",
    "documents/references/",
    "documents/postings/",
    "documents/interview/",
    "documents/writing_samples/",
    "documents/portfolio/",
]

# The only candidate-shaped content allowed to ship (plan-D rule 4).
ALLOWED_CANDIDATE_CONTENT = [
    "evidence/register.example.yaml",
    "examples/preferences.example.yaml",
    "examples/companies.example.yaml",
    "documents/demo/",
    "examples/",
]


def tracked_files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files"], capture_output=True, text=True, cwd=str(ROOT),
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        errors.append(f"could not list tracked files: {exc}")
        return []
    return [line.strip().replace("\\", "/") for line in out.splitlines() if line.strip()]


def check_gitignore() -> None:
    path = ROOT / ".gitignore"
    try:
        lines = {line.strip() for line in path.read_text(encoding="utf-8").splitlines()}
    except OSError as exc:
        errors.append(f".gitignore: unreadable: {exc}")
        return
    for rule in REQUIRED_IGNORE_RULES:
        if rule not in lines:
            errors.append(
                f".gitignore: required harness rule missing: {rule!r}. "
                "These rules keep a user's own career data out of their commits. "
                "If the rule moved or was renamed intentionally, update "
                "REQUIRED_IGNORE_RULES in tools/harness_guards.py in the same change."
            )


def check_no_negations_added() -> None:
    """The harness block must stay negation-free.

    Upstream's guard already fails any negation outside its allowlist. This
    repeats the check with a harness-specific message, because the failure mode
    is subtle: a required rule can be physically present and no longer take
    effect because a later `!pattern` re-included the path.
    """
    path = ROOT / ".gitignore"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return  # already reported by check_gitignore
    if "harness:begin" not in text:
        errors.append(".gitignore: the harness:begin/end managed block is missing")
        return
    block = text.split("harness:begin", 1)[1].split("harness:end", 1)[0]
    for line in block.splitlines():
        if line.strip().startswith("!"):
            errors.append(
                f".gitignore harness block: negation rule {line.strip()!r} is not "
                "allowed. A negation re-includes a path an earlier rule excluded and "
                "can silently re-expose personal data. Name shipped files so they do "
                "not match an ignore rule instead (*.example.yaml, documents/demo/)."
            )


def check_nothing_personal_is_tracked() -> None:
    tracked = set(tracked_files())
    for path in FORBIDDEN_TRACKED:
        if path in tracked:
            errors.append(
                f"{path} is tracked by git. It holds personal data and must never be "
                "committed. Remove it from the index with: git rm --cached "
                f"{path}"
            )
    for prefix in FORBIDDEN_TRACKED_PREFIXES:
        # `.gitkeep` files are how upstream ships the empty folder structure —
        # they are zero-byte by definition and hold nothing. Upstream's own
        # guard allowlists the matching `!documents/**/.gitkeep` negation, so
        # flagging them here would fail the build on correct upstream content.
        hits = sorted(p for p in tracked
                      if p.startswith(prefix) and not p.endswith(".gitkeep"))
        if hits:
            shown = ", ".join(hits[:3]) + (" …" if len(hits) > 3 else "")
            errors.append(
                f"{len(hits)} tracked file(s) under {prefix} — this path holds personal "
                f"data and must not be committed: {shown}"
            )


def check_shipped_examples_exist() -> None:
    """The documented schemas have to ship, or onboarding has nothing to copy."""
    for path in ("evidence/register.example.yaml", "examples/preferences.example.yaml",
                 "examples/companies.example.yaml"):
        if not (ROOT / path).is_file():
            errors.append(f"{path} is missing — it documents a schema users depend on")


def check_demo_content_is_confined() -> None:
    """Candidate-shaped content ships from three places only.

    A CV that appears anywhere else is either a real person's or an
    undocumented second demo; both are problems, and both look innocuous in a
    diff.
    """
    tracked = tracked_files()
    suspicious = []
    for path in tracked:
        lower = path.lower()
        if not any(token in lower for token in ("cv_", "resume", "cover_letter", "_cv")):
            continue
        if any(path.startswith(allowed) for allowed in ALLOWED_CANDIDATE_CONTENT):
            continue
        # Upstream's own stock templates and their example files are expected.
        if path.startswith(("cv/", "cover_letters/", "templates/", ".claude/",
                            "docs/", "tests/", "tests_harness/", "tools/")):
            continue
        suspicious.append(path)
    if suspicious:
        errors.append(
            "candidate-shaped files outside the allowed locations "
            f"({', '.join(ALLOWED_CANDIDATE_CONTENT)}): {', '.join(suspicious)}"
        )


def main() -> int:
    check_gitignore()
    check_no_negations_added()
    check_nothing_personal_is_tracked()
    check_shipped_examples_exist()
    check_demo_content_is_confined()

    if errors:
        print(f"harness_guards: {len(errors)} failure(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("harness_guards: OK (ignore rules, tracked paths, shipped examples, "
          "demo confinement)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
