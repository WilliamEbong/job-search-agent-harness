"""Tests for harness/status.py, harness/tracker_row.py, harness/rotate_backup.py.

These three modules exist because of defects the post-build review found, and
each defect was silent:

* **status.py** — three writers used three vocabularies. A row `/outcome` wrote
  as `applied` matched none of the workbook's six known values, so it counted as
  neither Open nor Closed and **vanished from the funnel** with no warning.
* **tracker_row.py** — upstream's `/outcome` documents a 13-column create-header
  with no `submitted_date`. The archiver reads that column to decide what moves
  to `applied/`, so on an outcome-created tracker **the move never fired,
  forever**. Rows were also hand-assembled as raw CSV by a language model, with
  quoting of free-text `notes`/`rationale` left to chance.
* **rotate_backup.py** — two commands described keep-5 backups; nothing
  implemented them.
"""

from __future__ import annotations

import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))

import rotate_backup  # noqa: E402
import status  # noqa: E402
import tracker_row  # noqa: E402


class StatusVocabulary(unittest.TestCase):
    def test_upstream_outcome_vocabulary_normalizes(self):
        """The values upstream's /outcome actually instructs writing."""
        self.assertEqual(status.IN_PROGRESS, status.normalize("applied"))
        self.assertEqual(status.INTERVIEW_ONLY, status.normalize("interview"))
        self.assertEqual(status.NO_RESPONSE, status.normalize("no response"))
        self.assertEqual(status.OFFER_DECLINED, status.normalize("offer declined"))

    def test_apply_any_vocabulary_is_already_canonical(self):
        self.assertEqual(status.IN_PROGRESS, status.normalize("in_progress"))

    def test_applied_rows_no_longer_fall_between_buckets(self):
        """REGRESSION: `applied` was in neither OPEN nor CLOSED."""
        self.assertTrue(status.is_open("applied"))
        self.assertFalse(status.is_closed("applied"))

    def test_interview_only_is_open_and_counts_as_responded(self):
        """upstream /html-report classifies this as Rejected/Closed; it isn't."""
        self.assertTrue(status.is_open("interview_only"))
        self.assertTrue(status.responded("interview_only"))

    def test_withdrawn_is_closed_but_is_not_a_rejection(self):
        """Collapsing withdrawn into rejected would corrupt the funnel."""
        self.assertEqual(status.WITHDRAWN, status.normalize("withdrawn"))
        self.assertTrue(status.is_closed("withdrawn"))
        self.assertFalse(status.responded("withdrawn"))

    def test_unknown_status_is_kept_and_treated_as_open(self):
        """Safe direction: is_open gates deletion by the archiver.

        Keeping a finished application costs disk; deleting a live one destroys
        the documents /interview prepares from.
        """
        self.assertEqual("awaiting_panel", status.normalize("awaiting_panel"))
        self.assertTrue(status.is_open("awaiting_panel"))

    def test_blank_is_neither_open_nor_closed(self):
        self.assertFalse(status.is_open(""))
        self.assertFalse(status.is_closed(None))


class TrackerRowWriting(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="harness-rows-"))
        self.csv_path = self.tmp / "job_search_tracker.csv"
        self.backups = self.tmp / "backups"
        self._saved_backup_dir = rotate_backup.BACKUP_DIR
        rotate_backup.BACKUP_DIR = self.backups

    def tearDown(self):
        rotate_backup.BACKUP_DIR = self._saved_backup_dir
        shutil.rmtree(self.tmp, ignore_errors=True)

    def rows(self):
        with self.csv_path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))

    def test_creates_the_file_with_the_full_header(self):
        result = tracker_row.append(
            {"company": "Acme", "role": "Analyst"}, self.csv_path)
        self.assertEqual("created", result)
        self.assertEqual(tracker_row.HEADER, list(self.rows()[0]))

    def test_heals_the_thirteen_column_outcome_header(self):
        """REGRESSION: without submitted_date the applied/ move is dead."""
        short_header = tracker_row.HEADER[:13]
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=short_header)
            writer.writeheader()
            writer.writerow({"date": "2026-07-01", "company": "Acme Inc.",
                             "role": "Data Analyst", "status": "applied",
                             "notes": "drafted, not sent"})

        result = tracker_row.append(
            {"company": "Rivermouth", "role": "Analyst"}, self.csv_path)

        self.assertEqual("healed", result)
        rows = self.rows()
        self.assertIn("submitted_date", rows[0])
        self.assertEqual(2, len(rows))
        # The pre-existing row survives intact, including its comma'd note.
        self.assertEqual("Acme Inc.", rows[0]["company"])
        self.assertEqual("drafted, not sent", rows[0]["notes"])

    def test_free_text_with_commas_and_quotes_round_trips(self):
        """Quoting was previously left to a language model writing raw CSV."""
        note = 'Recruiter said "strong fit", asked about travel, 15%'
        tracker_row.append({"company": "Acme", "role": "Analyst",
                            "notes": note, "rationale": "a, b, c"},
                           self.csv_path)
        self.assertEqual(note, self.rows()[0]["notes"])
        self.assertEqual("a, b, c", self.rows()[0]["rationale"])

    def test_status_is_normalized_on_write(self):
        tracker_row.append({"company": "Acme", "role": "Analyst",
                            "status": "applied"}, self.csv_path)
        self.assertEqual(status.IN_PROGRESS, self.rows()[0]["status"])

    def test_missing_status_defaults_to_in_progress(self):
        tracker_row.append({"company": "Acme", "role": "Analyst"}, self.csv_path)
        self.assertEqual(status.IN_PROGRESS, self.rows()[0]["status"])

    def test_update_sets_submitted_date(self):
        tracker_row.append({"company": "Acme", "role": "Data Analyst"},
                           self.csv_path)
        count = tracker_row.update("Acme", "Data Analyst",
                                   {"submitted_date": "2026-08-04",
                                    "status": "interview"}, self.csv_path)
        self.assertEqual(1, count)
        self.assertEqual("2026-08-04", self.rows()[0]["submitted_date"])
        self.assertEqual(status.INTERVIEW_ONLY, self.rows()[0]["status"])

    def test_update_leaves_other_rows_alone(self):
        tracker_row.append({"company": "Acme", "role": "Analyst"}, self.csv_path)
        tracker_row.append({"company": "Rivermouth", "role": "Analyst"},
                           self.csv_path)
        tracker_row.update("Acme", "Analyst", {"status": "rejected"},
                           self.csv_path)
        rows = {r["company"]: r["status"] for r in self.rows()}
        self.assertEqual(status.REJECTED, rows["Acme"])
        self.assertEqual(status.IN_PROGRESS, rows["Rivermouth"])

    def test_surplus_columns_do_not_crash_the_reader(self):
        """An unquoted comma used to produce a list under the None key, which
        later raised AttributeError on .strip() and took the workbook down."""
        with self.csv_path.open("w", newline="", encoding="utf-8") as handle:
            handle.write(",".join(tracker_row.HEADER) + "\n")
            handle.write("2026-07-01,Acme,Env,Analyst,FT,board,applied,,80,"
                         "note with, a stray comma,,,,,,\n")
        rows, _ = tracker_row.read_rows(self.csv_path)
        self.assertEqual(1, len(rows))

    def test_rewrite_backs_up_first(self):
        tracker_row.append({"company": "Acme", "role": "Analyst"}, self.csv_path)
        tracker_row.update("Acme", "Analyst", {"status": "rejected"},
                           self.csv_path)
        self.assertTrue(rotate_backup.backups_for(self.csv_path, self.backups))


class BackupRotation(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="harness-backup-"))
        self.target = self.tmp / "register.yaml"
        self.target.write_text("version: 1\n", encoding="utf-8")
        self.backups = self.tmp / "backups"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_keeps_only_the_newest_five(self):
        for index in range(8):
            self.target.write_text(f"version: {index}\n", encoding="utf-8")
            rotate_backup.rotate(self.target, self.backups, keep=5)
        self.assertEqual(5, len(rotate_backup.backups_for(self.target,
                                                          self.backups)))

    def test_rapid_backups_restore_the_newest_not_the_oldest(self):
        """REGRESSION: `--restore 1` returned the OLDEST of a same-second batch.

        The stamp had second resolution, so a collision was resolved by
        appending "-2"/"-3" after it. `-` sorts before `.`, which put the
        un-suffixed (first, oldest) name at the head of a reverse sort. A batch
        /outcome or /gmail-sync updating three rows within one second then made
        the documented undo restore the wrong file and silently discard two
        updates - while keep-5 pruned genuinely newer copies.

        The old count-only test passes with that bug intact.
        """
        for version in ("v1", "v2", "v3"):
            self.target.write_text(version + "\n", encoding="utf-8")
            rotate_backup.rotate(self.target, self.backups, keep=5)
        newest = rotate_backup.backups_for(self.target, self.backups)[0]
        self.assertEqual("v3\n", newest.read_text(encoding="utf-8"))

        self.target.write_text("clobbered\n", encoding="utf-8")
        rotate_backup.restore(self.target, 1, self.backups)
        self.assertEqual("v3\n", self.target.read_text(encoding="utf-8"))

    def test_restore_brings_content_back(self):
        self.target.write_text("good content\n", encoding="utf-8")
        rotate_backup.rotate(self.target, self.backups)
        self.target.write_text("clobbered\n", encoding="utf-8")

        rotate_backup.restore(self.target, 1, self.backups)
        self.assertEqual("good content\n",
                         self.target.read_text(encoding="utf-8"))

    def test_restore_is_itself_undoable(self):
        """Restoring backs up the current file first."""
        rotate_backup.rotate(self.target, self.backups)
        self.target.write_text("current\n", encoding="utf-8")
        before = len(rotate_backup.backups_for(self.target, self.backups))
        rotate_backup.restore(self.target, 1, self.backups)
        self.assertGreater(
            len(rotate_backup.backups_for(self.target, self.backups)), before)

    def test_missing_file_is_not_an_error(self):
        self.assertIsNone(rotate_backup.rotate(self.tmp / "nope.yaml",
                                               self.backups))


if __name__ == "__main__":
    unittest.main()
