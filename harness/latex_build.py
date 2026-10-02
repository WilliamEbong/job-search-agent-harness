#!/usr/bin/env python3
"""Compile CVs and cover letters quietly: one line per PDF instead of a TeX log.

A raw lualatex run prints several kilobytes of package chatter, and the model reads
all of it on every compile of every application. This prints only what matters: the
page count against the target, or the first error with its line number.

    python harness/latex_build.py cv/main_acme_analyst.tex cover_letters/cover_acme_analyst.tex --pages 2

Engine by folder: `cover_letters/` uses xelatex (cover.cls needs fontspec), anything
else lualatex (pdflatex fails on fontawesome5 under modern MiKTeX). `--pages` is the CV
target; a cover letter is always 1. Build files (.aux/.log/.out) are removed after a
clean compile, as /apply Step 5e does.

Exit 0 = every PDF built at its page target (layout notes, if any, follow "fix:");
1 = a compile failed or a page count is off; 2 = a source file is missing or the
engine is not installed.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ats_check  # noqa: E402  (its pdftotext decoder handles MiKTeX's xpdf)

TIMEOUT_S = 600  # a fresh MiKTeX installs packages on first use, which takes minutes
PAGE_NUMBER = re.compile(r"^\d+\s*/\s*\d+$")


def norm(text: str) -> str:
    return " ".join(re.findall(r"\w+", text.lower()))


def layout_flags(pdf: Path, tex: Path) -> list[str]:
    """Defects a reader sees that a page count cannot: a heading or entry title left
    at the foot of a page, and one-word last lines. Needs pdftotext (-layout keeps
    visual lines; pypdf merges them); without it the visual check covers these."""
    exe = shutil.which("pdftotext")
    if not exe:
        return []
    raw = subprocess.run([exe, "-layout", "-enc", "UTF-8", str(pdf), "-"],
                         capture_output=True).stdout
    pages = [[line.strip() for line in page.splitlines()
              if line.strip() and not PAGE_NUMBER.match(line.strip())]
             for page in ats_check.decode(raw).split("\f")]
    return flags_for([page for page in pages if page],
                     tex.read_text(encoding="utf-8", errors="replace"))


def flags_for(pages: list[list[str]], source: str) -> list[str]:
    """`pages`: each page's non-empty visual lines, page numbers removed."""
    headings = {norm(h) for h in re.findall(r"\\section\*?\{([^{}]*)\}", source)}
    entries = {norm(part) for pair in re.findall(
        r"\\cventry\{[^{}]*\}\{([^{}]*)\}\{([^{}]*)\}", source) for part in pair} - {""}
    flags = []
    for number, page in enumerate(pages[:-1], 1):
        last = page[-1]
        if norm(last) in headings or (not last.startswith("-")
                                      and any(e in norm(last) for e in entries)):
            flags.append(f"page {number} ends with '{last[:40]}'")
    widows = [line for page in pages for before, line in zip(page, page[1:])
              if len(line.split()) == 1 and len(before) >= 40 and line[-1] in ".%)"
              and norm(line) not in headings]
    if widows:
        flags.append("one-word lines: " + ", ".join(f"'{w}'" for w in widows[:4]))
    return flags


def engine_for(tex: Path) -> str:
    return "xelatex" if tex.parent.name == "cover_letters" else "lualatex"


def first_error(log: str, limit: int = 8) -> str:
    """The first `! ...` error from a TeX log and the lines that place it (`l.42 ...`)."""
    lines = log.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("!"):
            block = lines[i:i + limit]
            end = next((j for j, text in enumerate(block) if text.startswith("l.")), None)
            return "\n".join(block[:end + 2] if end is not None else block).strip()
    tail = [line for line in lines if line.strip()][-limit:]
    return "\n".join(tail) or "no error message in the log"


def build(tex: Path, pages: int) -> tuple[bool, str]:
    engine = shutil.which(engine_for(tex))
    if not engine:
        return False, f"{tex}: {engine_for(tex)} is not installed (python harness_setup.py --doctor)"
    command = [engine, "-interaction=nonstopmode", "-halt-on-error", tex.name]
    log = tex.with_suffix(".log")
    for _ in range(2):  # a second pass only when TeX asks for one (cross-references)
        try:
            proc = subprocess.run(command, cwd=tex.parent, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            return False, f"{tex}: {engine_for(tex)} timed out after {TIMEOUT_S}s"
        text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else proc.stdout
        if proc.returncode != 0:
            return False, f"{tex}: compile failed\n{first_error(text)}"
        if "Rerun to get" not in text:
            break
    pdf = tex.with_suffix(".pdf")
    count = len(PdfReader(pdf).pages)
    for suffix in (".aux", ".log", ".out"):
        tex.with_suffix(suffix).unlink(missing_ok=True)
    flags = layout_flags(pdf, tex)
    note = f"; fix: {'; '.join(flags)}" if flags else ""
    if count != pages:
        return False, f"{pdf}: {count} pages, target {pages} - cut content, never shrink fonts or margins{note}"
    return True, f"{pdf}: {count} page{'s' if count != 1 else ''} OK{note}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tex", nargs="+", help="LaTeX sources (CV and/or cover letter)")
    parser.add_argument("--pages", type=int, default=2, help="CV page target (default 2)")
    args = parser.parse_args(argv)
    missing = [t for t in args.tex if not Path(t).is_file()]
    if missing:
        print(f"latex_build: no such file: {', '.join(missing)}")
        return 2
    status = 0
    for name in args.tex:
        tex = Path(name)
        target = 1 if tex.parent.name == "cover_letters" else args.pages
        ok, line = build(tex, target)
        print(line)
        if not ok:
            status = 2 if "not installed" in line else max(status, 1)
    return status


if __name__ == "__main__":
    sys.exit(main())
