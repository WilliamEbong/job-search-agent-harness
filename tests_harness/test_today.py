"""Tests for /today — the daily brief and action menu.

The system had every ingredient for this and assembled none of them: a user
opening a session had no way to ask "where am I?" short of reading a
spreadsheet. The tests worth reading:

* `test_logged_followup_resets_the_clock` — the workbook counted days from the
  application date alone, so it kept demanding a follow-up that had already been
  sent. This adopts /outcome's formula (date or latest dated note) as the one
  formula.
* `test_new_user_is_offered_onboarding_not_an_empty_dashboard` — running any
  command before setup used to fail into undefined behaviour.
* `test_nothing_to_do_produces_no_actions` — a daily brief that always invents a
  task stops being worth reading.
"""

from __future__ import annotations

import csv
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))

import today as today_mod  # noqa: E402

TRACKER_HEADER = ["date", "company", "sector", "role", "role_type", "channel",
                  "status", "contact_person", "fit_rating", "notes", "cv_file",
                  "cover_letter_file", "source", "location", "rationale",
                  "submitted_date"]
SHORTLIST_HEADER = ["date", "company", "role", "location", "source", "url",
                    "score", "verdict", "rationale", "deadline"]
RUNLOG_HEADER = ["date", "portal", "query", "found", "new", "notes"]

TODAY = date(2026, 8, 4)


class DailyBrief(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="harness-today-"))
        (self.tmp / "evidence").mkdir()
        (self.tmp / "evidence" / "register.yaml").write_text("meta: {}\n",
                                                             encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name: str, header: list[str], rows: list[dict]) -> None:
        with (self.tmp / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in header})

    def collect(self):
        return today_mod.collect(today=TODAY, root=self.tmp)

    # ---------------------------------------------------------------- setup

    def test_new_user_is_offered_onboarding_not_an_empty_dashboard(self):
        (self.tmp / "evidence" / "register.yaml").unlink()
        state = self.collect()
        self.assertFalse(state["onboarded"])
        menu = today_mod.actions(state)
        self.assertEqual(1, len(menu))
        self.assertEqual("/setup-harness", menu[0]["command"])

    def test_a_future_date_in_notes_does_not_suppress_the_followup(self):
        """REGRESSION: a scheduled date made days_quiet negative, forever.

        `/outcome` routinely writes forward-looking dates into notes ("phone
        screen 2026-09-15", a posting's "ref 2026-12-31"). days_quiet took
        max() over every date it found, so the row reported negative silence,
        never crossed the follow-up threshold, and sat in `waiting` for good -
        the longer the silence, the more invisible it became.
        """
        self.write("job_search_tracker.csv", TRACKER_HEADER, [
            {"date": "2026-05-01", "company": "Rivermouth", "role": "Analyst",
             "status": "in_progress", "notes": "phone screen 2026-09-15"}])
        state = self.collect()
        self.assertEqual(95, state["followups"][0]["days_quiet"])
        self.assertEqual(1, len(state["followups"]))

    # ---------------------------------------------------------------- trials

    def _trial_prefs(self, status: str = "trial") -> None:
        (self.tmp / "preferences.yaml").write_text(
            "discovery:\n"
            "  trial_families:\n"
            "    - name: business analysis\n"
            f"      status: {status}\n",
            encoding="utf-8")

    def _trial_shortlist(self) -> None:
        self.write("shortlist.csv", SHORTLIST_HEADER, [
            {"company": "Acme", "role": "Business Analyst", "verdict": "qualified",
             "rationale": "trial: business analysis - strong requirements match"},
            {"company": "Beta", "role": "BA", "verdict": "not-drafted",
             "rationale": "trial: business analysis - seniority too high"},
            {"company": "Gamma", "role": "Analyst", "verdict": "qualified",
             "rationale": "core role family"}])

    def test_a_trial_family_with_results_is_surfaced_for_judging(self):
        """Without this the return path to /discover review did not exist."""
        self._trial_prefs()
        self._trial_shortlist()
        state = self.collect()
        self.assertEqual(1, len(state["trials"]))
        trial = state["trials"][0]
        self.assertEqual("business analysis", trial["family"])
        self.assertEqual(2, trial["found"])       # only the tagged rows
        self.assertEqual(1, trial["shortlisted"])
        self.assertIn("/discover review",
                      [item["command"] for item in today_mod.actions(state)])

    def test_a_kept_or_dropped_family_is_not_offered_for_judging(self):
        self._trial_prefs(status="dropped")
        self._trial_shortlist()
        self.assertEqual([], self.collect()["trials"])

    def test_a_trial_with_no_finds_yet_stays_quiet(self):
        self._trial_prefs()
        self.assertEqual([], self.collect()["trials"])

    def test_no_preferences_file_is_not_an_error(self):
        self._trial_shortlist()
        self.assertEqual([], self.collect()["trials"])

    # ------------------------------------------------------------ follow-ups

    def test_quiet_application_becomes_a_followup(self):
        self.write("job_search_tracker.csv", TRACKER_HEADER, [
            {"date": "2026-06-20", "company": "Rivermouth", "role": "Analyst",
             "status": "in_progress"}])
        state = self.collect()
        self.assertEqual(1, len(state["followups"]))
        self.assertEqual(45, state["followups"][0]["days_quiet"])

    def test_logged_followup_resets_the_clock(self):
        """REGRESSION: two formulas disagreed about "is this due?".

        The workbook counted from the application date, so it kept saying YES
        after a follow-up had been sent and logged.
        """
        self.write("job_search_tracker.csv", TRACKER_HEADER, [
            {"date": "2026-06-20", "company": "Rivermouth", "role": "Analyst",
             "status": "in_progress", "notes": "followed up 2026-08-01"}])
        state = self.collect()
        self.assertEqual(3, state["waiting"][0]["days_quiet"])
        self.assertEqual([], state["followups"])

    def test_recent_application_is_waiting_not_due(self):
        self.write("job_search_tracker.csv", TRACKER_HEADER, [
            {"date": "2026-08-01", "company": "Rivermouth", "role": "Analyst",
             "status": "in_progress"}])
        state = self.collect()
        self.assertEqual([], state["followups"])
        self.assertEqual(1, len(state["waiting"]))

    def test_two_followups_already_sent_stops_the_nudge(self):
        """/outcome caps chasing at two; past that it is not the next action."""
        self.write("job_search_tracker.csv", TRACKER_HEADER, [
            {"date": "2026-05-01", "company": "Rivermouth", "role": "Analyst",
             "status": "in_progress",
             "notes": "followed up 2026-05-20; followed up 2026-06-01"}])
        state = self.collect()
        self.assertEqual([], state["followups"])

    def test_closed_applications_are_ignored(self):
        self.write("job_search_tracker.csv", TRACKER_HEADER, [
            {"date": "2026-01-01", "company": "Rivermouth", "role": "Analyst",
             "status": "rejected"}])
        state = self.collect()
        self.assertEqual([], state["followups"])
        self.assertEqual(0, state["total_open"])

    def test_upstream_status_vocabulary_is_understood(self):
        """A row /outcome wrote as `applied` is an open application."""
        self.write("job_search_tracker.csv", TRACKER_HEADER, [
            {"date": "2026-06-20", "company": "Rivermouth", "role": "Analyst",
             "status": "applied"}])
        self.assertEqual(1, len(self.collect()["followups"]))

    # ------------------------------------------------------------ interviews

    def test_interviews_are_surfaced(self):
        self.write("job_search_tracker.csv", TRACKER_HEADER, [
            {"date": "2026-07-28", "company": "Prairie Grid", "role": "Officer",
             "status": "interview_only"}])
        self.assertEqual(1, len(self.collect()["interviews"]))

    # ------------------------------------------------------------- shortlist

    def test_qualified_but_unapplied_is_surfaced(self):
        self.write("shortlist.csv", SHORTLIST_HEADER, [
            {"date": "2026-08-01", "company": "Boreal", "role": "Field Analyst",
             "score": "84", "verdict": "qualified"}])
        state = self.collect()
        self.assertEqual(1, len(state["undrafted"]))

    def test_already_applied_shortlist_rows_are_not_repeated(self):
        self.write("shortlist.csv", SHORTLIST_HEADER, [
            {"date": "2026-08-01", "company": "Boreal", "role": "Field Analyst",
             "score": "84", "verdict": "qualified"}])
        self.write("job_search_tracker.csv", TRACKER_HEADER, [
            {"date": "2026-08-02", "company": "Boreal", "role": "Field Analyst",
             "status": "in_progress"}])
        self.assertEqual([], self.collect()["undrafted"])

    def test_gate_failed_rows_are_never_suggested(self):
        self.write("shortlist.csv", SHORTLIST_HEADER, [
            {"date": "2026-08-01", "company": "Continental", "role": "Hydrologist",
             "score": "44", "verdict": "gate-fail"}])
        self.assertEqual([], self.collect()["undrafted"])

    def test_deadline_inside_two_weeks_is_flagged(self):
        self.write("shortlist.csv", SHORTLIST_HEADER, [
            {"date": "2026-08-01", "company": "Boreal", "role": "Field Analyst",
             "verdict": "qualified", "deadline": "2026-08-10"}])
        state = self.collect()
        self.assertEqual(1, len(state["deadlines"]))
        self.assertEqual(6, state["deadlines"][0]["closes_in"])

    def test_distant_deadline_is_not_noise(self):
        self.write("shortlist.csv", SHORTLIST_HEADER, [
            {"date": "2026-08-01", "company": "Boreal", "role": "Field Analyst",
             "verdict": "qualified", "deadline": "2026-12-01"}])
        self.assertEqual([], self.collect()["deadlines"])

    # ---------------------------------------------------------- search age

    def test_stale_search_is_reported(self):
        self.write("run_log.csv", RUNLOG_HEADER, [
            {"date": "2026-07-20", "portal": "boards", "found": "12", "new": "3"}])
        self.assertEqual(15, self.collect()["search_age_days"])

    def test_no_search_yet_prompts_one(self):
        state = self.collect()
        self.assertIsNone(state["search_age_days"])
        commands = [item["command"] for item in today_mod.actions(state)]
        self.assertIn("/scrape", commands)

    # -------------------------------------------------------------- actions

    def test_actions_carry_runnable_commands(self):
        self.write("job_search_tracker.csv", TRACKER_HEADER, [
            {"date": "2026-06-20", "company": "Rivermouth", "role": "Analyst",
             "status": "in_progress"}])
        menu = today_mod.actions(self.collect())
        self.assertTrue(menu)
        for item in menu:
            self.assertTrue(item["label"])
            self.assertTrue(item["command"].startswith(("/", "apply")))

    def test_nothing_to_do_produces_no_actions(self):
        """A brief that always invents a task stops being worth reading."""
        self.write("job_search_tracker.csv", TRACKER_HEADER, [
            {"date": "2026-08-03", "company": "Rivermouth", "role": "Analyst",
             "status": "in_progress"}])
        self.write("run_log.csv", RUNLOG_HEADER, [
            {"date": "2026-08-03", "portal": "boards", "found": "5", "new": "1"}])
        self.assertEqual([], today_mod.actions(self.collect()))

    def test_render_is_a_glance_not_a_report(self):
        self.write("job_search_tracker.csv", TRACKER_HEADER, [
            {"date": "2026-06-20", "company": "Rivermouth", "role": "Analyst",
             "status": "in_progress"}])
        text = today_mod.render(self.collect())
        self.assertLess(len(text.splitlines()), 25)
        self.assertIn("Rivermouth", text)
        self.assertIn("1.", text)

    def test_waiting_applications_are_counted_not_listed(self):
        rows = [{"date": "2026-08-03", "company": f"Company {n}",
                 "role": "Analyst", "status": "in_progress"} for n in range(6)]
        self.write("job_search_tracker.csv", TRACKER_HEADER, rows)
        text = today_mod.render(self.collect())
        self.assertIn("Waiting on 6", text)
        self.assertNotIn("Company 3", text)

    def test_read_only_creates_nothing(self):
        before = sorted(p.name for p in self.tmp.iterdir())
        self.collect()
        self.assertEqual(before, sorted(p.name for p in self.tmp.iterdir()))


if __name__ == "__main__":
    unittest.main()


class Wave4Capabilities(unittest.TestCase):
    """Offer stage, referrals, deadlines, conversion analytics.

    Each closes a gap the review named: the system surfaced "an offer needs
    your decision" and then had nothing to say; it measured `channel: referral`
    conversion while offering no way to get a referral; it extracted posting
    deadlines and then discarded them; and it reported counts by source but
    never conversion, leaving "which board actually works?" unanswerable.
    """

    @staticmethod
    def _flat(path: Path) -> str:
        import re as _re
        return _re.sub(r"\s+", " ", path.read_text(encoding="utf-8").lower())

    def test_offer_command_exists_with_a_codex_stub(self):
        self.assertTrue((ROOT / ".claude" / "commands" / "offer.md").is_file())
        self.assertTrue((ROOT / ".codex" / "prompts" / "offer.md").is_file())

    def test_offer_never_invents_a_competing_offer(self):
        text = self._flat(ROOT / ".claude" / "commands" / "offer.md")
        self.assertIn("never invent a competing offer", text)

    def test_offer_compares_against_stated_preferences(self):
        text = self._flat(ROOT / ".claude" / "commands" / "offer.md")
        self.assertIn("preferences.yaml", text)
        self.assertIn("minimum", text)
        self.assertIn("target", text)

    def test_offer_disclaims_advice_and_invented_market_data(self):
        text = self._flat(ROOT / ".claude" / "commands" / "offer.md")
        self.assertIn("not a licensed financial or legal adviser", text)
        self.assertIn("do not invent market data", text)

    def test_offer_accepts_not_negotiating_as_an_answer(self):
        text = self._flat(ROOT / ".claude" / "commands" / "offer.md")
        self.assertIn("not everyone does", text)

    def test_offer_draft_goes_through_the_fact_gate(self):
        text = self._flat(ROOT / ".claude" / "commands" / "offer.md")
        self.assertIn("harness/fact_check.py", text)

    def test_contacts_are_modelled_and_surfaced_before_drafting(self):
        example = self._flat(ROOT / "examples" / "companies.example.yaml")
        self.assertIn("contacts:", example)
        apply_any = self._flat(ROOT / ".claude" / "commands" / "apply-any.md")
        self.assertIn("do they know anyone there", apply_any)
        # A prompt, not a gate - it must not block the application.
        self.assertIn("this is a prompt, not a gate", apply_any)

    def test_deadline_is_persisted_not_just_displayed(self):
        scrape = self._flat(ROOT / ".claude" / "commands" / "scrape.md")
        self.assertIn("deadline", scrape)
        self.assertIn("survives exactly one run", scrape)

    def test_batch_close_out_requires_consent_and_spares_interviews(self):
        text = self._flat(ROOT / ".claude" / "commands" / "today.md")
        self.assertIn("never do this without asking", text)
        self.assertIn("never for anything at `interview_only`", text)

    def test_today_still_declares_what_it_writes(self):
        """The command has two write paths; the honesty note must match.

        It used to say both needed a yes while Step 3 said "quietly" — so the
        model chose, and /today behaved differently run to run. The rule is now
        stated once and is principled: regenerating a view proceeds, changing
        what is recorded asks.
        """
        text = self._flat(ROOT / ".claude" / "commands" / "today.md")
        self.assertIn("reading is always safe", text)
        self.assertIn("regenerates a view proceeds", text)
        self.assertIn("changes what is recorded asks", text)
        self.assertNotIn("both need a yes", text)
