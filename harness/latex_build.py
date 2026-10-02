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

Exit 0 = every PDF built at its page target; 1 = a compile failed or a page count is
off; 2 = a source file is missing or the engine is not installed.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

TIMEOUT_S = 600  # a fresh MiKTeX installs packages on first use, which takes minutes


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
    # Sub-5pt overflows are invisible and moderncv produces them routinely.
    overfull = sum(float(w) > 5 for w in re.findall(r"Overfull \\hbox \(([\d.]+)pt", text))
    for suffix in (".aux", ".log", ".out"):
        tex.with_suffix(suffix).unlink(missing_ok=True)
    note = f"; {overfull} line(s) past the margin" if overfull else ""
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
