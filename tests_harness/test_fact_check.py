"""Tests for harness/fact_check.py — the Tier-1 deterministic truth gate.

These run against the FICTIONAL demo register (evidence/register.example.yaml),
so they assert the same result on any machine and no real career data is
involved.

Read the two regression cases first. Both pin defects that were found in live
use of the private system this checker was ported from, and both are the kind
a well-meaning refactor silently reintroduces:

* `test_percent_spellings_are_equivalent` — a registered "22%" metric was
  flagged as a fabrication whenever a draft wrote "22 percent", or whenever
  LaTeX's `22\\%` extracted as "22 %".
* `test_posting_whitelist_requires_a_whole_number` — the posting whitelist was
  a bare substring test, so a posting containing "2047" silently cleared an
  unregistered "47 percent" claim. That one let a package pass spuriously.

A third pins a defect found while porting:

* `test_common_english_words_are_not_technology_claims` — the lexicon contains
  Go, Spring, React and friends, and matching them in lowercased text reported
  "the spring sampling programme" as a technology claim.

If a fixture fails after a register edit, the fixture is usually right: a fact
recorded loosely enough to let a planted fabrication through is recorded wrong.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "harness" / "fact_check.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
# The demo register stands in for a user's real evidence/register.yaml, which
# is gitignored and absent on a fresh clone and in CI.
REGISTER = ROOT / "evidence" / "register.example.yaml"


def run_checker(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(CHECKER), "--register", str(REGISTER), *args],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return proc.returncode, proc.stdout + proc.stderr


class WriteDraft:
    """Context manager for a throwaway draft file."""

    def __init__(self, text: str, suffix: str = ".txt"):
        self.text = text
        self.suffix = suffix

    def __enter__(self) -> str:
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=self.suffix, delete=False, encoding="utf-8"
        )
        handle.write(self.text)
        handle.close()
        self.path = handle.name
        return self.path

    def __exit__(self, *exc):
        os.unlink(self.path)


class CleanFixture(unittest.TestCase):
    def test_clean_fixture_passes(self):
        """False positives make the gate useless — the operator learns to ignore it."""
        code, out = run_checker(str(FIXTURES / "fixture_clean.txt"))
        self.assertEqual(code, 0, out)
        self.assertTrue(out.startswith("OK"), out)


class BadFixture(unittest.TestCase):
    """The fabrication test from the owner's guide, in mechanical form."""

    def setUp(self):
        self.code, self.out = run_checker(str(FIXTURES / "fixture_bad.txt"))

    def test_bad_fixture_is_blocked(self):
        self.assertNotEqual(self.code, 0, self.out)
        self.assertIn("RED LINE", self.out)

    def test_every_planted_class_is_named(self):
        expected = {
            "12,000 users": "unregistered metric",
            "7 years": "unregistered tenure figure",
            "2019 - 2026": "date range outside every registered span",
            "Docker": "unregistered technology",
            "AWS Certified Solutions Architect": "unregistered credential",
            "Google Data Analytics": "in-progress credential without its qualifier",
            "software engineer": "positioning constraint: developer self-description",
            "proficient in python": "positioning constraint: language fluency",
            "coded": "positioning constraint: bare build verb",
        }
        for needle, why in expected.items():
            self.assertIn(needle, self.out, f"{why} was not reported:\n{self.out}")

    def test_exit_code_counts_the_red_lines(self):
        self.assertGreaterEqual(self.code, 7, self.out)


class UnsupportedMetric(unittest.TestCase):
    """plan-M test 16."""

    def test_planted_numeral_not_in_register_is_blocked(self):
        with WriteDraft("The programme reached 4,912 households last year.\n") as draft:
            code, out = run_checker(draft)
        self.assertNotEqual(code, 0)
        self.assertIn("4912", out.replace(",", ""))

    def test_registered_metric_passes(self):
        with WriteDraft("Turnaround time fell 22 percent after the redesign.\n") as draft:
            code, out = run_checker(draft)
        self.assertEqual(code, 0, out)

    def test_numeral_with_an_unlisted_unit_is_a_known_ceiling(self):
        """Documents the gate's real limit rather than implying it has none.

        The numeral check fires only for units in NUMERAL_RE, which is a
        whitelist so that page numbers and postcodes are not treated as claims.
        A claim carrying a unit nobody listed therefore passes Tier 1 and is
        left to the Tier-2 reviewer. When a real draft slips one through, the
        fix is to add the unit — which is why this test asserts the ceiling
        exists rather than asserting it is acceptable.
        """
        with WriteDraft("The programme reached 4,912 municipalities.\n") as draft:
            code, _ = run_checker(draft)
        self.assertEqual(code, 0)


class UnsupportedCredential(unittest.TestCase):
    """plan-M test 17 — both halves."""

    def test_unregistered_credential_is_blocked(self):
        with WriteDraft("Holder of the PMP designation.\n") as draft:
            code, out = run_checker(draft)
        self.assertNotEqual(code, 0)
        self.assertIn("PMP", out)

    def test_in_progress_credential_without_qualifier_is_blocked(self):
        with WriteDraft(
            "Riley holds the Google Data Analytics Professional Certificate.\n"
        ) as draft:
            code, out = run_checker(draft)
        self.assertNotEqual(code, 0, out)
        self.assertIn("in progress", out)

    def test_in_progress_credential_with_qualifier_passes(self):
        with WriteDraft(
            "Riley is completing the Google Data Analytics Professional "
            "Certificate, currently in progress.\n"
        ) as draft:
            code, out = run_checker(draft)
        self.assertEqual(code, 0, out)


class DateRanges(unittest.TestCase):
    def test_range_outside_every_span_is_blocked(self):
        with WriteDraft("Northwind Analytical Services, 2014 - 2019.\n") as draft:
            code, out = run_checker(draft)
        self.assertNotEqual(code, 0, out)

    def test_range_inside_a_registered_span_passes(self):
        with WriteDraft("Northwind Analytical Services, 2020 - 2022.\n") as draft:
            code, out = run_checker(draft)
        self.assertEqual(code, 0, out)


class PositioningConstraints(unittest.TestCase):
    def test_ai_assisted_framing_exempts_the_build_verb(self):
        with WriteDraft(
            "Built a reporting pipeline with Claude Code for the monthly report.\n"
        ) as draft:
            code, out = run_checker(draft)
        self.assertEqual(code, 0, out)

    def test_the_same_sentence_without_the_framing_is_blocked(self):
        with WriteDraft("Built a reporting pipeline for the monthly report.\n") as draft:
            code, out = run_checker(draft)
        self.assertNotEqual(code, 0, out)

    def test_constraint_patterns_do_not_fire_without_a_declared_constraint(self):
        """The candidate-agnostic gate.

        A candidate who really is a software engineer has no
        `programming_claims` entry in their register, and the family must then
        be completely silent — otherwise this checker would be unusable for
        anyone in the industry it most often screens.
        """
        import yaml

        register = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
        register["positioning_constraints"] = [
            c for c in register["positioning_constraints"]
            if c.get("id") != "programming_claims"
        ]
        with tempfile.NamedTemporaryFile(
            "w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as handle:
            yaml.safe_dump(register, handle, allow_unicode=True)
            trimmed = handle.name
        try:
            with WriteDraft("I am a software engineer and I coded the service.\n") as draft:
                proc = subprocess.run(
                    [sys.executable, str(CHECKER), "--register", trimmed, draft],
                    capture_output=True, text=True, cwd=str(ROOT),
                )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        finally:
            os.unlink(trimmed)


class PostingDerivedNumbers(unittest.TestCase):
    def test_posting_numbers_are_allowed(self):
        """A salary or requisition ID quoted from the posting is not invented."""
        draft_text = ("I am applying for requisition 88421, advertised at "
                      "62,000 CAD per year.\n")
        posting_text = "Requisition 88421. Salary: 62,000 CAD per year.\n"
        with WriteDraft(draft_text) as draft, WriteDraft(posting_text) as posting:
            code, out = run_checker(draft, "--posting", posting)
            self.assertEqual(code, 0, out)
            bare, _ = run_checker(draft)
            self.assertNotEqual(bare, 0,
                                "without the posting the same numbers must be flagged")

    def test_posting_whitelist_requires_a_whole_number(self):
        """REGRESSION: a substring match let a real fabrication through.

        The whitelist was `value in posting`, so a posting mentioning 2047 or
        470 silently cleared an unregistered "47 percent" claim.
        """
        draft_text = "I improved throughput by 47 percent in the first year.\n"
        posting_text = ("Our strategic plan runs to 2047 and the team supports "
                        "470 clients.\n")
        with WriteDraft(draft_text) as draft, WriteDraft(posting_text) as posting:
            code, out = run_checker(draft, "--posting", posting)
        self.assertNotEqual(
            code, 0,
            "47 appears only inside 2047/470, so it must NOT be whitelisted:\n" + out,
        )


class PercentSpellings(unittest.TestCase):
    def test_percent_spellings_are_equivalent(self):
        """REGRESSION: registered percentages were flagged when spelled out.

        The register stores "22%"; drafts legitimately write "22 percent", and
        LaTeX's `22\\%` extracts as "22 %". All three are the same claim.
        """
        draft_text = (
            "Turnaround time fell 22 percent.\n"
            "Volunteer retention rose 35 %.\n"
            "The same figure again: 22%.\n"
        )
        with WriteDraft(draft_text) as draft:
            code, out = run_checker(draft)
        self.assertEqual(code, 0,
                         "registered percentages must pass in any spelling:\n" + out)


class LexiconFalsePositives(unittest.TestCase):
    def test_common_english_words_are_not_technology_claims(self):
        """REGRESSION: Go, Spring and React are English words as well as tools.

        Matching the lexicon in lowercased text reported "the spring sampling
        programme" as a claim to the Spring framework.
        """
        draft_text = (
            "The spring sampling programme runs every year.\n"
            "Volunteers go further than the minimum protocol.\n"
            "The board tends to react to the trend lines.\n"
        )
        with WriteDraft(draft_text) as draft:
            code, out = run_checker(draft)
        self.assertEqual(code, 0, "ordinary English words must not be red lines:\n" + out)

    def test_capitalised_technology_names_are_still_caught(self):
        """The fix must not blind the check to real keyword stuffing."""
        with WriteDraft("Production experience with Go and Rust.\n") as draft:
            code, out = run_checker(draft)
        self.assertNotEqual(code, 0, out)
        self.assertIn("Go", out)
        self.assertIn("Rust", out)


class LatexHandling(unittest.TestCase):
    def test_latex_commands_are_stripped_before_checking(self):
        """A \\section{...} must not be read as prose, but its text must be."""
        tex = (r"\section{Experience}" "\n"
               r"\cventry{2020--2022}{Laboratory Technician}{Northwind "
               r"Analytical Services}{}{}{Processed 1,400 samples.}" "\n")
        with WriteDraft(tex, suffix=".tex") as draft:
            code, out = run_checker(draft)
        self.assertEqual(code, 0, out)


class MissingRegister(unittest.TestCase):
    def test_absent_register_fails_loudly(self):
        """No register must never mean 'nothing to check, therefore fine'."""
        with WriteDraft("Anything at all.\n") as draft:
            proc = subprocess.run(
                [sys.executable, str(CHECKER), "--register",
                 str(ROOT / "evidence" / "does_not_exist.yaml"), draft],
                capture_output=True, text=True, cwd=str(ROOT),
            )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("no evidence register", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
