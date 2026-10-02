"""Tests for harness/ats_check.py - the mechanical half of /apply Step 5d.

The script owns extraction, parseability and keyword coverage; the model keeps
only the have-it-or-gap judgment. These pin what a model checking by eye gets
wrong: a `(cid:)` run or a missing email must fail the run (exit 1), `R` must
not match inside "Rivermouth", C++ and Node.js must survive tokenising, and a
stock moderncv CV must not fail on the icon glyphs MiKTeX's pdftotext writes.

PDFs are written in-test (one page, a Helvetica text stream), so nothing binary
ships and no TeX is needed.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))

import ats_check  # noqa: E402


def text_pdf(path: Path, lines: list[str]) -> Path:
    """Write a one-page PDF whose text layer is `lines` (ASCII). ~800 bytes."""
    def escape(text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = ("BT /F1 10 Tf 50 800 Td "
              + " ".join(f"({escape(line)}) Tj 0 -14 Td" for line in lines) + " ET")
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
        "/Encoding /WinAnsiEncoding >>",
    ]
    out, offsets = "%PDF-1.4\n", []
    for number, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n{body}\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    out += "".join(f"{offset:010d} 00000 n \n" for offset in offsets)
    out += (f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n")
    path.write_bytes(out.encode("latin-1"))
    return path


# Contact details are the reserved fiction ranges privacy_sweep allows.
CV_TEX = r"""\documentclass{moderncv}
\phone[mobile]{+1 555-0100}
\email{candidate@example.com}
%\email{old.address@example.com}
\begin{document}\makecvtitle
\section{Experience}
\item{\cventry{2019 - 2024}{Analyst}{Acme}{Somewhere}{}{
\item Built dashboards in SQL and Python.
}}
\section{Education}
\end{document}"""

CLEAN_LINES = ["Alex Example", "+1 555-0100 | candidate@example.com", "Experience",
               "Analyst, Acme 2019 - 2024",
               "Built reporting dashboards in SQL and Python for the operations team.",
               "Education", "BSc Statistics"]

POSTING = """# Data Analyst

### Responsibilities
- Own the weekly reporting pack.

### Requirements
- 3+ years of experience with SQL and Python.
- Strong knowledge of Node.js, C++ or C#.
- Experience with dashboards (Power BI).

### Nice to have
- Familiarity with R.
- Kubernetes

### How to apply
Send a CV through the portal.
"""


def keyword(term: str, *synonyms: str) -> dict:
    return {"keyword": term, "priority": "required", "synonyms": list(synonyms)}


class KeywordExtraction(unittest.TestCase):
    def test_reads_required_and_preferred_sections_only(self):
        found = {k["keyword"]: k["priority"]
                 for k in ats_check.extract_keywords(POSTING)}
        for term in ("SQL", "Python", "Node.js", "C++", "C#", "dashboards", "Power BI"):
            self.assertEqual(found.get(term), "required", (term, found))
        for term in ("R", "Kubernetes"):
            self.assertEqual(found.get(term), "preferred", (term, found))
        # Filler is stripped and other sections are not requirements.
        for absent in ("reporting", "3+ years", "Strong knowledge of Node.js",
                       "Experience", "BI", "CV"):
            self.assertNotIn(absent, found)

    def test_without_sections_falls_back_to_tech_tokens_and_repeated_phrases(self):
        found = [k["keyword"] for k in ats_check.extract_keywords(
            "We build data pipelines on AWS. Our data pipelines feed CI/CD checks.")]
        self.assertEqual(found, ["AWS", "CI/CD", "data pipelines"])


class Matching(unittest.TestCase):
    def status(self, text: str, *keywords: dict) -> list[str]:
        return [row["status"] for row in ats_check.match(text, list(keywords))]

    def test_tech_names_with_punctuation_match_as_written(self):
        self.assertEqual(
            self.status("Wrote C++ services and Node.js tools.",
                        keyword("C++"), keyword("Node.js"), keyword("C")),
            ["covered", "covered", "missing"])  # C is not inside C++

    def test_simple_plurals_fold_both_ways(self):
        self.assertEqual(self.status("Built dashboards.", keyword("dashboard")), ["covered"])
        self.assertEqual(self.status("Built a dashboard.", keyword("dashboards")), ["covered"])

    def test_single_letter_r_does_not_match_inside_a_word(self):
        self.assertEqual(self.status("Rivermouth R&D for operators.", keyword("R")),
                         ["missing"])
        self.assertEqual(self.status("Statistics in R.", keyword("R")), ["covered"])

    def test_keywords_file_synonym_hit_is_synonym_only(self):
        tmp = Path(tempfile.mkdtemp(prefix="harness-ats-"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        path = tmp / "main_acme.keywords.txt"
        path.write_text("# the posting's terms\nrequired: spreadsheet | Excel\n"
                        "preferred: Power BI   # nice to have\nGIS\nC#\n",
                        encoding="utf-8")
        keywords = ats_check.load_keywords(path)
        self.assertEqual([(k["keyword"], k["priority"]) for k in keywords],
                         [("spreadsheet", "required"), ("Power BI", "preferred"),
                          ("GIS", "required"), ("C#", "required")])
        rows = ats_check.match("Advanced Excel and C# for reporting.", keywords)
        self.assertEqual([(r["status"], r["matched"]) for r in rows],
                         [("synonym-only", "Excel"), ("missing", ""), ("missing", ""),
                          ("covered", "C#")])


class Parseability(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="harness-ats-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.tex = self.tmp / "main_acme.tex"
        self.tex.write_text(CV_TEX, encoding="utf-8")
        self.posting = self.tmp / "job_posting.md"
        self.posting.write_text(POSTING, encoding="utf-8")

    def run_check(self, lines: list[str], *extra: str) -> tuple[int, dict]:
        pdf = text_pdf(self.tmp / "cv.pdf", lines)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ats_check.main(["--cv", str(pdf), "--posting", str(self.posting),
                                   "--tex", str(self.tex), "--json", *extra])
        return code, json.loads(out.getvalue())

    def test_a_clean_text_pdf_exits_0(self):
        code, result = self.run_check(CLEAN_LINES)
        self.assertEqual(code, 0, result["parse"])
        self.assertTrue(result["summary"].startswith("ATS: parse OK · required "))
        self.assertEqual(result["parse"]["warnings"], [])

    def test_cid_markers_exit_1(self):
        code, result = self.run_check(CLEAN_LINES + ["Python (cid:31)(cid:42)"])
        self.assertEqual(code, 1)
        self.assertIn("parse FAIL ((cid:) markers)", result["summary"])

    def test_email_missing_from_the_text_layer_exits_1(self):
        lines = [line.replace("candidate@example.com", "Envelope") for line in CLEAN_LINES]
        code, result = self.run_check(lines)
        self.assertEqual(code, 1)
        self.assertEqual(result["parse"]["failures"], ["email not in the text layer"])

    def test_pypdf_fallback_reads_the_same_pdf(self):
        """Without poppler the check still runs - pypdf is a pinned dependency."""
        with mock.patch.object(ats_check.shutil, "which", return_value=None):
            code, result = self.run_check(CLEAN_LINES)
        self.assertEqual((code, result["extractor"]), (0, "pypdf"))

    def test_headings_out_of_source_order_warn_without_failing(self):
        lines = CLEAN_LINES[:2] + ["Education", "BSc Statistics", "Experience",
                                   "Analyst, Acme 2019 - 2024"]
        code, result = self.run_check(lines)
        self.assertEqual(code, 0)
        self.assertIn("out of source order", " ".join(result["parse"]["warnings"]))

    def test_cesu8_icon_glyphs_are_not_replacement_characters(self):
        """REGRESSION: MiKTeX's pdftotext writes moderncv's icons (outside the
        BMP) as surrogate halves. A plain UTF-8 decode with errors="replace"
        turned them into U+FFFD and failed every clean stock CV."""
        text = ats_check.decode(b"\xed\xa0\xbd\xed\xb6\x82 Winnipeg")
        self.assertEqual(text, "\U0001f582 Winnipeg")

    def test_a_missing_input_is_a_usage_error_not_a_parse_failure(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = ats_check.main(["--cv", str(self.tmp / "nope.pdf"),
                                   "--posting", str(self.posting)])
        self.assertEqual(code, 2)
        self.assertIn("no such file", err.getvalue())


if __name__ == "__main__":
    unittest.main()
