"""latex_build.py prints one line per PDF instead of a TeX log.

The log parsing is tested everywhere; the real compile only where TeX is installed
(CI has none).
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "harness"))
import latex_build  # noqa: E402

LOG = """This is LuaHBTeX, Version 1.24.0
(./main.tex
! Undefined control sequence.
l.12 \\cvitm
            {Skills}{Excel}
The control sequence at the end of the top line
of your error message was never \\def'ed.

Here is how much of LuaTeX's memory you used:
"""


class Parsing(unittest.TestCase):
    def test_first_error_stops_after_the_line_number(self):
        error = latex_build.first_error(LOG)
        self.assertTrue(error.startswith("! Undefined control sequence."))
        self.assertIn("l.12 \\cvitm", error)
        self.assertNotIn("memory", error)

    def test_no_error_marker_falls_back_to_the_tail(self):
        self.assertIn("last words", latex_build.first_error("a\nb\nlast words\n"))

    def test_layout_flags_stranded_heading_and_one_word_lines(self):
        source = ("\\section{Education}\n"
                  "\\cventry{2020-2024}{Senior Technician}{Northwind}{Winnipeg}{}{}\n")
        pages = [["- Reworked the sample intake process and cut average turnaround",
                  "time.", "Education"],
                 ["Senior Technician  Northwind", "- Trained new technicians."]]
        flags = latex_build.flags_for(pages, source)
        self.assertIn("page 1 ends with 'Education'", flags)
        self.assertIn("one-word lines: 'time.'", flags)
        clean = [["- One full bullet that ends where it should.", "Education"][:1],
                 ["Education", "Senior Technician  Northwind"]]
        self.assertEqual([], latex_build.flags_for(clean, source))

    def test_engine_by_folder(self):
        self.assertEqual("xelatex", latex_build.engine_for(Path("cover_letters/cover_x.tex")))
        self.assertEqual("lualatex", latex_build.engine_for(Path("cv/main_x.tex")))


@unittest.skipUnless(shutil.which("lualatex"), "lualatex not installed")
class RealCompile(unittest.TestCase):
    def test_page_target_and_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            tex = Path(tmp) / "cv" / "main_t.tex"
            tex.parent.mkdir()
            tex.write_text("\\documentclass{article}\\begin{document}Hello\\end{document}\n",
                           encoding="utf-8")
            ok, line = latex_build.build(tex, 1)
            self.assertTrue(ok, line)
            self.assertIn("1 page OK", line)
            self.assertFalse(tex.with_suffix(".log").exists())
            ok, line = latex_build.build(tex, 2)
            self.assertFalse(ok)
            self.assertIn("target 2", line)


if __name__ == "__main__":
    unittest.main()
