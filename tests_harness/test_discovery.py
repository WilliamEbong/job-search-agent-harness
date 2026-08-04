"""Contract tests for the discovery layer (P5): scopes, modes, cost posture.

The properties pinned here are the ones whose loss is invisible in a passing
run but changes what the user is told:

* all five scopes exist and are named (plan-M 38);
* an unreadable source is reported as `unverified`, never as "no openings"
  (plan-M 37) — the failure that silently removes an employer from a search;
* zero-result runs are still logged, because a broken CLI and a quiet market
  produce identical output without the log;
* the cost posture is printed *before* the run and invents no token arithmetic.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRAPE = ROOT / ".claude" / "commands" / "scrape.md"
BOARD_DOC = ROOT / "docs" / "board-intelligence.md"
JOBBANK = ROOT / ".agents" / "skills" / "jobbank-ca-search"


def flat(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8").lower())


class SearchScopes(unittest.TestCase):
    def setUp(self):
        self.text = flat(SCRAPE)

    def test_all_five_scopes_are_documented(self):
        for scope in ("--scope board", "--scope company", "--scope companies",
                      "--scope boards", "--scope all"):
            self.assertIn(scope, self.text)

    def test_both_rosters_are_described_as_living(self):
        self.assertIn("living lists", self.text)
        self.assertIn("nothing needs re-onboarding", self.text)

    def test_unknown_source_is_reported_not_silently_narrowed(self):
        self.assertIn("rather than silently searching a subset", self.text)


class UsageModes(unittest.TestCase):
    def setUp(self):
        self.text = flat(SCRAPE)

    def test_three_modes_are_documented(self):
        for mode in ("focused", "balanced", "full"):
            self.assertIn(mode, self.text)

    def test_focused_generates_no_documents(self):
        self.assertIn("max_packages_per_run: 0", self.text)

    def test_caps_apply_within_any_scope(self):
        self.assertIn("caps apply **within** any scope",
                      SCRAPE.read_text(encoding="utf-8").lower())


class CostPosture(unittest.TestCase):
    def setUp(self):
        self.text = flat(SCRAPE)

    def test_posture_is_printed_before_the_run(self):
        self.assertIn("before doing anything", self.text)

    def test_no_fabricated_token_arithmetic(self):
        self.assertIn("never fabricate token arithmetic", self.text)

    def test_heavy_runs_are_confirmed(self):
        self.assertIn("confirm before `full`", self.text)


class OpenJobValidation(unittest.TestCase):
    def setUp(self):
        self.text = flat(SCRAPE)

    def test_unverified_is_distinguished_from_closed(self):
        self.assertIn("never present an unverified posting as confidently open",
                      self.text)

    def test_unreadable_is_not_reported_as_no_openings(self):
        self.assertIn(
            'not "this employer has no openings."', self.text
        )

    def test_all_four_shortlist_verdicts_are_defined(self):
        for verdict in ("qualified", "not-drafted", "not-resolved", "gate-fail"):
            self.assertIn(verdict, self.text)


class HardConstraintGate(unittest.TestCase):
    def setUp(self):
        self.text = flat(SCRAPE)

    def test_gate_runs_before_scoring(self):
        self.assertIn("before scoring, not after", self.text)

    def test_gate_quotes_the_postings_own_wording(self):
        self.assertIn("posting's own wording quoted", self.text)

    def test_preferred_skills_do_not_trigger_a_hard_skip(self):
        self.assertIn("does not** trigger the skip",
                      SCRAPE.read_text(encoding="utf-8").lower())


class PayDemotion(unittest.TestCase):
    """Stated pay below the stated minimum demotes — with three boundaries.

    The owner declined to touch upstream's scoring weights, so this lives in
    the harness's own shortlist step. Each boundary guards a distinct failure:
    treating silence as a low offer discards most of the market, an invented
    annualisation is a fabricated number, and gate-fail would make a judgement
    call irreversible.
    """

    def setUp(self):
        self.text = flat(SCRAPE)

    def test_below_minimum_caps_the_verdict_not_the_shortlist(self):
        self.assertIn("cap the verdict at `not-drafted`", self.text)
        self.assertIn("demotion, not a gate", self.text)

    def test_only_a_stated_number_demotes(self):
        self.assertIn("only a *stated* number demotes", self.text)
        self.assertIn("silence is never treated as a low offer", self.text)

    def test_no_invented_annualisation(self):
        self.assertIn("converted honestly or not compared at all", self.text)

    def test_below_minimum_is_never_gate_fail(self):
        self.assertIn("below-minimum is never `gate-fail`", self.text)


class DiscoveryIsNotSplitBrained(unittest.TestCase):
    """REGRESSION: the documented /scrape never wrote seen_jobs.json.

    Two /scrape implementations existed — this command and the upstream
    job-scraper skill — with disjoint state. Upstream `/rank` reads *only*
    `job_scraper/seen_jobs.json` and stops with "run /scrape first" when it is
    empty, which is what a user saw immediately after running /scrape. The same
    file is the only cross-run dedup store, so a second run re-surfaced every
    posting the user had already dismissed.
    """

    def setUp(self):
        self.text = flat(SCRAPE)

    def test_delegates_fetching_to_the_job_scraper_skill(self):
        self.assertIn("job-scraper", self.text)
        self.assertIn(".claude/skills/job-scraper/skill.md", self.text)

    def test_names_the_dedup_store_that_rank_depends_on(self):
        self.assertIn("seen_jobs.json", self.text)

    def test_explains_why_skipping_it_breaks_downstream_commands(self):
        self.assertIn("/rank", self.text)
        self.assertIn("/upskill", self.text)

    def test_company_results_join_the_same_memory(self):
        self.assertIn("company:<name>", self.text.replace(" ", ""))

    def test_verdicts_are_mapped_to_ranks_bands(self):
        """Two vocabularies for one judgement look like disagreement."""
        for band in ("strong fit", "good fit", "moderate fit"):
            self.assertIn(band, self.text)


class RunLogging(unittest.TestCase):
    def test_empty_runs_are_still_logged(self):
        text = flat(SCRAPE)
        self.assertIn("including runs that found nothing", text)

    def test_run_log_writes_the_expected_columns(self):
        import csv
        import tempfile
        import importlib

        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "run_log.csv"
            sys.path.insert(0, str(ROOT / "harness"))
            run_log = importlib.import_module("run_log")
            original = run_log.LOG
            run_log.LOG = str(log)
            try:
                sys.argv = ["run_log.py", "--portal", "freehire",
                            "--query", "analyst", "--found", "0", "--new", "0",
                            "--notes", "board quiet"]
                run_log.main()
            finally:
                run_log.LOG = original
            with log.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(1, len(rows))
        self.assertEqual("freehire", rows[0]["portal"])
        self.assertEqual("0", rows[0]["found"])
        self.assertRegex(rows[0]["date"], r"^\d{4}-\d{2}-\d{2}$")


class JobBankCaPort(unittest.TestCase):
    def test_skill_and_cli_are_present(self):
        for path in ("SKILL.md", "url-reference.md", "cli/package.json",
                     "cli/src/cli.ts"):
            self.assertTrue((JOBBANK / path).is_file(), path)

    def test_no_owner_location_identifiers_survived_the_port(self):
        """The private CLI used the owner's own city in every example."""
        offenders = []
        for path in JOBBANK.rglob("*"):
            if not path.is_file() or "node_modules" in path.parts:
                continue
            if path.suffix not in {".ts", ".md", ".json"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if re.search(r"\bCalgary\b", text):
                offenders.append(str(path.relative_to(JOBBANK)))
        self.assertEqual([], offenders)

    def test_province_lookup_survived_sanitisation(self):
        """Sanitising examples must not have damaged functional code."""
        source = (JOBBANK / "cli" / "src" / "commands" / "search.ts").read_text(
            encoding="utf-8"
        )
        for province in ("alberta", "manitoba", "british columbia"):
            self.assertIn(province, source.lower())

    def test_package_manifest_has_no_lifecycle_scripts(self):
        """Same rule upstream's security guard applies to its own CLIs."""
        manifest = json.loads((JOBBANK / "cli" / "package.json").read_text(
            encoding="utf-8"
        ))
        forbidden = {"preinstall", "install", "postinstall", "prepare", "prepack"}
        self.assertEqual(set(), forbidden & set(manifest.get("scripts", {})))
        self.assertNotIn("trustedDependencies", manifest)


class BoardIntelligence(unittest.TestCase):
    def setUp(self):
        self.text = flat(BOARD_DOC)

    def test_records_the_core_ambiguity(self):
        self.assertIn("look identical", self.text)

    def test_records_that_ats_sites_are_not_aggregators(self):
        self.assertIn("employer ats sites", self.text)

    def test_records_the_js_shell_signature(self):
        self.assertIn("javascript-rendered", self.text)

    def test_records_crawl_delay_enforcement_in_code(self):
        self.assertIn("crawl-delay", self.text)
        self.assertIn("enforced between requests by the", self.text)


if __name__ == "__main__":
    unittest.main()
