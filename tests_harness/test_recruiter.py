"""Tests for the recruiter pass (/recruiter) and the `target_positions` contract.

The example in `examples/preferences.example.yaml` is the schema `/scrape`,
`/lite search` and `/discover` read, so it is validated against Contract B here:
a typo in it is a typo in every preferences file built from it. The tests worth
reading:

* `test_fit_sits_inside_its_tier` — the tier is a claim about the evidence, and
  a stretch scored like core is exactly the overselling the pass must not do.
* `test_preferences_without_positions_offer_the_pass_first` — a user onboarded
  before the pass existed would otherwise never be told about it.
* `test_spec_fits_the_lite_budget` — `/lite` loads the spec on every lite
  onboarding, so its size is a running cost, not a style choice.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
COMMANDS = ROOT / ".claude" / "commands"
sys.path.insert(0, str(ROOT / "harness"))

import today as today_mod  # noqa: E402

REQUIRED_KEYS = {"rank", "title", "level", "fit", "tier", "because", "gap",
                 "search_terms", "status"}
LEVELS = {"entry", "intermediate", "senior", "lead"}
TIER_FIT = {"core": (85, 100), "adjacent": (65, 84), "stretch": (50, 64)}


class TargetPositionsExample(unittest.TestCase):
    def setUp(self):
        self.prefs = yaml.safe_load(
            (ROOT / "examples" / "preferences.example.yaml").read_text(encoding="utf-8"))
        self.block = self.prefs["target_positions"]
        self.positions = self.block["positions"]

    def test_records_when_and_from_what(self):
        self.assertRegex(str(self.block["generated"]), r"^\d{4}-\d{2}-\d{2}$")
        self.assertIn("evidence/register.yaml", self.block["source"])

    def test_entries_carry_every_contract_key(self):
        self.assertTrue(self.positions)
        for entry in self.positions:
            self.assertEqual(set(), REQUIRED_KEYS - set(entry), entry.get("title"))
            self.assertTrue(str(entry["because"]).strip(), entry["title"])
            self.assertTrue(str(entry["gap"]).strip(), entry["title"])

    def test_values_are_in_the_contract_vocabulary(self):
        for entry in self.positions:
            self.assertIn(entry["level"], LEVELS, entry["title"])
            self.assertIn(entry["tier"], TIER_FIT, entry["title"])
            self.assertIn(entry["status"], {"active", "dropped"}, entry["title"])
            self.assertIn(len(entry["search_terms"]), (2, 3), entry["title"])

    def test_fit_sits_inside_its_tier(self):
        for entry in self.positions:
            low, high = TIER_FIT[entry["tier"]]
            self.assertTrue(low <= entry["fit"] <= high,
                            f"{entry['title']}: fit {entry['fit']} is not {entry['tier']}")

    def test_ranks_ascend(self):
        ranks = [entry["rank"] for entry in self.positions]
        self.assertEqual(sorted(set(ranks)), ranks)

    def test_a_struck_position_is_kept_on_record(self):
        """Deleting a struck entry would let the next pass propose it again."""
        self.assertIn("dropped", {entry["status"] for entry in self.positions})

    def test_lite_mode_is_documented_with_caps(self):
        lite = self.prefs["usage"]["modes"]["lite"]
        for key in ("description", "max_evaluations", "max_packages_per_run"):
            self.assertIn(key, lite)


class TodayOffersTheRecruiterPass(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="harness-recruiter-"))
        (self.tmp / "evidence").mkdir()
        (self.tmp / "evidence" / "register.yaml").write_text("meta: {}\n",
                                                             encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def commands(self, preferences: str) -> list[str]:
        (self.tmp / "preferences.yaml").write_text(preferences, encoding="utf-8")
        state = today_mod.collect(today=date(2026, 8, 4), root=self.tmp)
        return [item["command"] for item in today_mod.actions(state)]

    def test_preferences_without_positions_offer_the_pass_first(self):
        self.assertEqual("/recruiter",
                         self.commands("role_families:\n  - analysis\n")[0])

    def test_only_struck_positions_still_offer_it(self):
        self.assertEqual("/recruiter", self.commands(
            "target_positions:\n  positions:\n"
            "    - {rank: 1, title: Analyst, status: dropped}\n")[0])

    def test_an_active_position_means_the_pass_is_done(self):
        self.assertNotIn("/recruiter", self.commands(
            "target_positions:\n  positions:\n"
            "    - {rank: 1, title: Analyst, status: active}\n"))


class RecruiterWiring(unittest.TestCase):
    def test_spec_fits_the_lite_budget(self):
        path = COMMANDS / "recruiter.md"
        self.assertTrue(path.read_text(encoding="utf-8").startswith("# /recruiter - "))
        self.assertLessEqual(len(path.read_bytes()), 5 * 1024)

    def test_onboarding_runs_it_right_after_the_register(self):
        text = (COMMANDS / "setup-harness.md").read_text(encoding="utf-8").lower()
        step3 = text.index("## step 3: build the register")
        step3b = text.index("## step 3b: recruiter pass")
        self.assertLess(step3, step3b)
        self.assertLess(step3b, text.index("## step 4:"))
        self.assertIn("steps 1–3 and 3b", text)  # quick start runs it too

    def test_search_and_discovery_read_the_positions(self):
        for name in ("scrape.md", "discover.md"):
            self.assertIn("target_positions",
                          (COMMANDS / name).read_text(encoding="utf-8"), name)


if __name__ == "__main__":
    unittest.main()
