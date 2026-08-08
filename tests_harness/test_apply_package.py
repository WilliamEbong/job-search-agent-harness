"""Tests for harness/apply_package.py — the deterministic package builder.

This script replaces roughly twelve filesystem operations that were previously
described in prose and re-derived by the model on every run. The test that
matters most is `test_combined_document_exists_in_all_three_formats`: the
combined cover-letter-plus-resume document shipped as a PDF only for the whole
of the original build, because the command file listed three formats and the
two that were never written were invisible to a contract test.

`test_writes_the_filenames_upstream_expects` guards the other quiet failure:
upstream's /interview reads `cv_draft.tex`, which the harness's friendly naming
never produced, so interview prep could not find the documents it prepares from.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))

import apply_package  # noqa: E402

REGISTER = ROOT / "evidence" / "register.example.yaml"

CV_TEX = r"""\begin{document}\makecvtitle
\section{Experience}
\item{\cventry{2020 - 2022}{Laboratory Technician}{Northwind}{Winnipeg, MB}{}{
\item Processed 1,400 samples.
}}
\end{document}"""

LETTER_TEX = r"""\begin{document}
\lettercontent{Dear Hiring Team,}
\lettercontent{Here is how it maps:}
\begin{itemize}
    \item \textbf{QA/QC:} logged 1,400 samples.
\end{itemize}
\lettercontent{I look forward to hearing from you.}
\closing{Kind regards,}
\signature{Riley Chen}
\end{document}"""


class Slugging(unittest.TestCase):
    def test_slugify_is_lowercase_underscored_ascii(self):
        self.assertEqual("acme_inc_data_analyst",
                         apply_package.slugify("Acme, Inc.", "Data Analyst"))

    def test_ampersand_becomes_and(self):
        self.assertEqual("learning_and_development",
                         apply_package.slugify("Learning & Development"))

    def test_folder_name_uses_the_documented_convention(self):
        self.assertEqual("Acme_Inc_Data_Analyst",
                         apply_package.folder_name("Acme, Inc.", "Data Analyst"))

    def test_long_names_are_truncated_but_stay_readable(self):
        name = apply_package.folder_name(
            "A Very Long Environmental Consulting Company Limited Partnership",
            "Senior Environmental Data Analyst, Water Quality Programmes")
        self.assertLessEqual(len(name), 2 * apply_package.MAX_PART + 1)
        self.assertTrue(name.startswith("A_Very_Long"))

    def test_friendly_name_drops_characters_windows_rejects(self):
        stem = apply_package.friendly("resume", 'Analyst: "Water/Data"',
                                      "Acme", "Riley Chen")
        for bad in '\\/:*?"<>|':
            self.assertNotIn(bad, stem)


class PackageAssembly(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="harness-package-"))
        self.applications = self.tmp / "applications"
        self.build = self.tmp / "build"
        self.build.mkdir()
        self.cv = self.tmp / "main_acme_analyst.tex"
        self.letter = self.tmp / "cover_acme_analyst.tex"
        self.cv.write_text(CV_TEX, encoding="utf-8")
        self.letter.write_text(LETTER_TEX, encoding="utf-8")
        # Stand-in compiled PDFs so the copy and merge paths run.
        for stem in ("main_acme_analyst", "cover_acme_analyst"):
            self._fake_pdf(self.build / f"{stem}.pdf")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def _fake_pdf(path: Path) -> None:
        try:
            from pypdf import PdfWriter
        except ImportError:  # pragma: no cover
            path.write_bytes(b"%PDF-1.4\n")
            return
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        with path.open("wb") as handle:
            writer.write(handle)

    def build_package(self):
        return apply_package.build_package(
            "Acme Environmental", "Data Analyst", self.cv, self.letter,
            self.build, REGISTER, self.applications,
        )

    def test_creates_the_application_folder_and_posting_source(self):
        folder, _ = self.build_package()
        self.assertTrue(folder.is_dir())
        self.assertTrue((folder / "posting_source").is_dir())

    def test_writes_a_created_marker_for_the_archiver(self):
        """Without it the archiver falls back to guessing from file mtimes,
        which is what made new folders look eight weeks old."""
        folder, _ = self.build_package()
        marker = folder / ".created"
        self.assertTrue(marker.is_file())
        self.assertRegex(marker.read_text(encoding="utf-8"), r"^\d{4}-\d{2}-\d{2}T")

    @staticmethod
    def _files_starting(folder: Path, prefix: str, suffix: str) -> list[Path]:
        """Exact prefix match.

        Not glob: pathlib's glob is case-insensitive on Windows, so a pattern
        of "resume *.pdf" also matches "Resume & Cover Letter ....pdf" and the
        counts come out wrong on one platform only.
        """
        return [p for p in folder.iterdir()
                if p.name.startswith(prefix) and p.name.endswith("." + suffix)]

    def test_resume_and_letter_exist_in_every_format(self):
        folder, _ = self.build_package()
        for kind in ("resume", "cover letter"):
            for suffix in ("tex", "pdf", "md"):
                matches = self._files_starting(folder, kind + " ", suffix)
                self.assertEqual(1, len(matches), f"{kind}.{suffix}")

    def test_combined_document_exists_in_all_three_formats(self):
        """REGRESSION: the combined document shipped as a PDF only.

        apply-any.md specified md, docx and pdf. Two were never written, and no
        test noticed, because the tests read the command file rather than the
        output directory.
        """
        folder, _ = self.build_package()
        for suffix in ("md", "pdf"):
            matches = self._files_starting(folder, "Resume & Cover Letter ", suffix)
            self.assertEqual(1, len(matches), f"combined .{suffix} missing")
        if shutil.which("pandoc"):
            self.assertEqual(1, len(self._files_starting(
                folder, "Resume & Cover Letter ", "docx")))

    def test_combined_markdown_carries_a_word_page_break(self):
        """Without the raw-openxml block the resume does not start on its own
        page in Word, only in the merged PDF."""
        folder, _ = self.build_package()
        combined = self._files_starting(folder, "Resume & Cover Letter ", "md")[0]
        text = combined.read_text(encoding="utf-8")
        self.assertIn("=openxml", text)
        self.assertIn('w:br w:type="page"', text)

    def test_combined_order_is_letter_then_resume(self):
        folder, _ = self.build_package()
        combined = self._files_starting(folder, "Resume & Cover Letter ", "md")[0]
        text = combined.read_text(encoding="utf-8")
        self.assertLess(text.index("Dear Hiring Team"), text.index("Experience"))

    def test_combined_pdf_has_both_documents(self):
        folder, _ = self.build_package()
        found = self._files_starting(folder, "Resume & Cover Letter ", "pdf")
        merged = found[0] if found else None
        if merged is None:
            self.skipTest("pypdf unavailable")
        from pypdf import PdfReader
        self.assertEqual(2, len(PdfReader(str(merged)).pages))

    def test_writes_the_filenames_upstream_expects(self):
        """REGRESSION: /interview reads cv_draft.tex and cover_letter.tex.

        The harness wrote only friendly names, so upstream's interview prep
        could not find the documents that were actually submitted. Upstream
        cannot be edited, so the package writes both.
        """
        folder, _ = self.build_package()
        self.assertTrue((folder / "cv_draft.tex").is_file())
        self.assertTrue((folder / "cover_letter.tex").is_file())

    def test_markdown_mirror_takes_identity_from_the_register(self):
        folder, _ = self.build_package()
        resume_md = self._files_starting(folder, "resume ", "md")[0]
        self.assertIn("Riley Chen", resume_md.read_text(encoding="utf-8"))

    def test_rebuilding_does_not_duplicate_or_lose_files(self):
        folder, first = self.build_package()
        _, second = self.build_package()
        self.assertEqual(sorted(first), sorted(second))
        self.assertEqual(len(set(second)), len(second))

    def test_rebuilding_keeps_the_original_creation_stamp(self):
        folder, _ = self.build_package()
        stamp = (folder / ".created").read_text(encoding="utf-8")
        self.build_package()
        self.assertEqual(stamp, (folder / ".created").read_text(encoding="utf-8"))

    def test_missing_source_fails_loudly(self):
        with self.assertRaises(SystemExit):
            apply_package.build_package(
                "Acme", "Analyst", self.tmp / "nope.tex", self.letter,
                self.build, REGISTER, self.applications)


class PostingArchiveGate(unittest.TestCase):
    """The package is not complete until the posting it answers is archived.

    REGRESSION: for the entire original build nothing checked this. The demo
    package shipped with an empty posting_source/ and no job_posting.md, and a
    contract test that reads a document cannot notice a file that does not
    exist — the same failure mode the combined-document bug had.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="harness-gate-"))
        self.folder = self.tmp / "Acme_Data_Analyst"
        (self.folder / "posting_source").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _fill_archive(self):
        (self.folder / "job_posting.md").write_text("# Data Analyst\nAcme.",
                                                    encoding="utf-8")
        (self.folder / "provenance.md").write_text("# Provenance\n- Rung 1",
                                                   encoding="utf-8")
        (self.folder / "posting_source" / "pasted.md").write_text(
            "raw posting", encoding="utf-8")

    def test_a_complete_archive_passes(self):
        self._fill_archive()
        self.assertEqual(apply_package.posting_archive_gaps(self.folder), [])

    def test_missing_files_and_empty_source_dir_are_each_named(self):
        gaps = apply_package.posting_archive_gaps(self.folder)
        self.assertEqual(len(gaps), 3)
        self.assertTrue(any("job_posting.md" in g for g in gaps))
        self.assertTrue(any("provenance.md" in g for g in gaps))
        self.assertTrue(any("posting_source" in g for g in gaps))

    def test_a_blank_posting_doc_is_a_gap_not_a_pass(self):
        """The reported symptom: the file exists and there is nothing in it."""
        self._fill_archive()
        (self.folder / "job_posting.md").write_text("  \n\n", encoding="utf-8")
        gaps = apply_package.posting_archive_gaps(self.folder)
        self.assertEqual(gaps, ["job_posting.md empty"])


class TrainingGate(unittest.TestCase):
    """A package leaning on an unpractised rapidly-closable skill is not final.

    `/apply-any` writes TRAINING-REQUIRED.md when a draft uses a skill the
    evaluation classified as learnable in hours. The package must stay at
    exit 2 until the user has actually done the exercise — otherwise the
    training flow is decoration and the draft ships on an unearned claim.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="harness-training-"))
        self.folder = self.tmp / "Acme_Data_Analyst"
        self.folder.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_absent_file_passes(self):
        self.assertEqual(apply_package.training_gaps(self.folder), [])

    def test_blank_file_passes(self):
        """A stale empty leftover must not block a finished package."""
        (self.folder / apply_package.TRAINING_FILE).write_text(
            "  \n\n", encoding="utf-8")
        self.assertEqual(apply_package.training_gaps(self.folder), [])

    def test_nonempty_file_is_a_gap_naming_the_file(self):
        (self.folder / apply_package.TRAINING_FILE).write_text(
            "# Training required\n- PivotTables: 2h exercise pending\n",
            encoding="utf-8")
        gaps = apply_package.training_gaps(self.folder)
        self.assertEqual(len(gaps), 1)
        self.assertIn(apply_package.TRAINING_FILE, gaps[0])


if __name__ == "__main__":
    unittest.main()
