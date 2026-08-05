#!/usr/bin/env python3
"""Assemble a complete application package. One command, twelve operations.

Everything here used to be prose in `.claude/commands/apply-any.md` — folder
naming, friendly filenames, truncation, three format conversions per document,
a PDF merge, a Word page break, the tracker row — and the model re-derived all
of it on every run. That is how the combined document came to ship as a PDF
with no .md or .docx: the instructions listed all three, and nobody noticed the
two that were never written, because a contract test that reads a document
cannot notice a file that does not exist.

    python harness/apply_package.py \
        --company "Rivermouth Environmental Consulting" \
        --role "Environmental Data Analyst" \
        --cv cv/main_rivermouth_analyst.tex \
        --letter cover_letters/cover_rivermouth_analyst.tex \
        --build build --url https://... --score 82 \
        --location "Winnipeg, MB" --rationale "..."

Produces, in `documents/applications/<Company>_<Role>/`:

    posting_source/                     (created; intake fills it)
    .created                            creation stamp for the archiver
    job_posting.md, provenance.md       (written by the intake step)
    resume <Role> <Company> - <Name>.{tex,pdf,md,docx}
    cover letter <Role> <Company> - <Name>.{tex,pdf,md,docx}
    Resume & Cover Letter ... .{pdf,md,docx}
    cv_draft.tex, cover_letter.tex      canonical copies

Those last two matter: upstream's `/interview` and `/outcome` look for exactly
those names, and the harness writes friendly ones. Rather than edit upstream
(which must stay byte-identical for clean tag merges), the package simply also
writes what upstream expects.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
ROOT = HARNESS_DIR.parent
APPLICATIONS_DIR = ROOT / "documents" / "applications"
REGISTER = ROOT / "evidence" / "register.yaml"

sys.path.insert(0, str(HARNESS_DIR))
import tex_to_md  # noqa: E402
import tracker_row  # noqa: E402
from archive_applications import CREATED_MARKER  # noqa: E402

# Keep names readable in a file picker. A 200-character posting title in a
# filename is a Windows path-length failure waiting to happen.
MAX_PART = 45

PAGE_BREAK = ('\n\n```{=openxml}\n'
              '<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n'
              '```\n\n')


def slugify(*parts: str) -> str:
    """Build-source slug: lowercase, underscores, ASCII.

    The single forward function. `archive_applications.match_folder` exists to
    reverse-engineer a folder name from a tracker row precisely because this
    did not exist; three command files each described a different convention.
    """
    text = " ".join(p for p in parts if p)
    text = text.replace("&", " and ")
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
    return re.sub(r"_+", "_", text)


def folder_name(company: str, role: str) -> str:
    """`<Company>_<Role>` — the documented application-folder convention."""
    def part(text: str) -> str:
        text = text.replace("&", " and ")
        cleaned = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
        return cleaned[:MAX_PART].rstrip("_")
    return f"{part(company)}_{part(role)}"


def friendly(kind: str, role: str, company: str, name: str) -> str:
    """Human-readable stem, e.g. `resume Data Analyst Acme - Riley Chen`."""
    def part(text: str) -> str:
        cleaned = re.sub(r'[\\/:*?"<>|]', "", (text or "").strip())
        return cleaned[:MAX_PART].rstrip(" .")
    return f"{kind} {part(role)} {part(company)} - {part(name)}".strip()


def candidate_name(register: Path = REGISTER) -> str:
    try:
        import yaml
    except ImportError:
        return ""
    if not register.exists():
        return ""
    try:
        with register.open(encoding="utf-8") as handle:
            return str((yaml.safe_load(handle) or {}).get("meta", {}).get("owner", ""))
    except (OSError, ValueError):
        return ""


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def write_markdown(tex: Path, target: Path, register: Path) -> None:
    target.write_text(tex_to_md.convert(str(tex), str(register)), encoding="utf-8")


def to_docx(markdown: Path, target: Path) -> bool:
    """Convert via pandoc. Returns False (with a notice) if pandoc is absent."""
    if not have("pandoc"):
        return False
    result = subprocess.run(
        ["pandoc", str(markdown), "-o", str(target)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  pandoc failed for {target.name}: "
              f"{result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ''}")
        return False
    return True


def merge_pdfs(first: Path, second: Path, target: Path) -> bool:
    try:
        from pypdf import PdfWriter
    except ImportError:
        print("  pypdf not installed - skipping the combined PDF")
        return False
    writer = PdfWriter()
    for source in (first, second):
        if not source.is_file():
            return False
        writer.append(str(source))
    writer.write(str(target))
    writer.close()
    return True


def build_package(company: str, role: str, cv_tex: Path, letter_tex: Path,
                  build_dir: Path, register: Path = REGISTER,
                  applications_dir: Path = APPLICATIONS_DIR) -> tuple[Path, list[str]]:
    """Create the folder and every artifact. Returns (folder, files written)."""
    name = candidate_name(register)
    folder = applications_dir / folder_name(company, role)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "posting_source").mkdir(exist_ok=True)

    # The archiver reads this instead of guessing from file mtimes, which used
    # to make a new folder look eight weeks old the moment an older CV was
    # copied into it.
    marker = folder / CREATED_MARKER
    if not marker.exists():
        marker.write_text(datetime.now().isoformat(timespec="seconds"),
                          encoding="utf-8")

    written: list[str] = []

    def record(path: Path) -> None:
        written.append(path.name)

    pairs = [("resume", cv_tex), ("cover letter", letter_tex)]
    stems: dict[str, str] = {}

    for kind, source in pairs:
        if not source.is_file():
            sys.exit(f"apply_package: {source} not found")
        stem = friendly(kind, role, company, name)
        stems[kind] = stem

        target_tex = folder / f"{stem}.tex"
        shutil.copy2(source, target_tex)
        record(target_tex)

        pdf = build_dir / (source.stem + ".pdf")
        if pdf.is_file():
            shutil.copy2(pdf, folder / f"{stem}.pdf")
            record(folder / f"{stem}.pdf")
        else:
            print(f"  no compiled PDF at {pdf} - compile before packaging")

        markdown = folder / f"{stem}.md"
        write_markdown(source, markdown, register)
        record(markdown)
        if to_docx(markdown, folder / f"{stem}.docx"):
            record(folder / f"{stem}.docx")

    # Canonical copies for upstream /interview and /outcome, which look for
    # these exact names and cannot be taught the friendly ones.
    shutil.copy2(cv_tex, folder / "cv_draft.tex")
    shutil.copy2(letter_tex, folder / "cover_letter.tex")
    written += ["cv_draft.tex", "cover_letter.tex"]

    # Combined document: cover letter first, resume on a new page.
    combined = friendly("Resume & Cover Letter", role, company, name)
    letter_md, cv_md = folder / f"{stems['cover letter']}.md", folder / f"{stems['resume']}.md"
    if letter_md.is_file() and cv_md.is_file():
        merged = (letter_md.read_text(encoding="utf-8").rstrip()
                  + PAGE_BREAK
                  + cv_md.read_text(encoding="utf-8").lstrip())
        (folder / f"{combined}.md").write_text(merged, encoding="utf-8")
        record(folder / f"{combined}.md")
        if to_docx(folder / f"{combined}.md", folder / f"{combined}.docx"):
            record(folder / f"{combined}.docx")
    letter_pdf = folder / f"{stems['cover letter']}.pdf"
    cv_pdf = folder / f"{stems['resume']}.pdf"
    if letter_pdf.is_file() and cv_pdf.is_file():
        if merge_pdfs(letter_pdf, cv_pdf, folder / f"{combined}.pdf"):
            record(folder / f"{combined}.pdf")

    return folder, written


def posting_archive_gaps(folder: Path) -> list[str]:
    """What is missing from the archived posting, or [] if it is complete.

    The intake step is supposed to write these before packaging, and for the
    entire original build nothing checked that it had: the demo package
    shipped with an empty posting_source/ and no job_posting.md at all. A
    posting archived at apply time is the only record of what was applied to
    once the posting goes offline — which is what interview prep reads weeks
    later, and by then it cannot be re-fetched.
    """
    gaps: list[str] = []
    for doc in ("job_posting.md", "provenance.md"):
        path = folder / doc
        if not path.is_file():
            gaps.append(f"{doc} missing")
        elif not path.read_text(encoding="utf-8", errors="replace").strip():
            gaps.append(f"{doc} empty")
    source_dir = folder / "posting_source"
    if not any(p.is_file() for p in source_dir.glob("*")):
        gaps.append("posting_source/ has no artifacts")
    return gaps


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--company", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--cv", required=True, help="build-source CV .tex")
    parser.add_argument("--letter", required=True, help="build-source letter .tex")
    parser.add_argument("--build", default=str(ROOT / "build"),
                        help="directory holding the compiled PDFs")
    parser.add_argument("--register", default=str(REGISTER))
    parser.add_argument("--applications", default=str(APPLICATIONS_DIR))
    parser.add_argument("--url", default="", help="posting URL for the tracker row")
    parser.add_argument("--score", default="", help="fit score for the tracker row")
    parser.add_argument("--location", default="")
    parser.add_argument("--rationale", default="")
    parser.add_argument("--channel", default="")
    parser.add_argument("--sector", default="")
    parser.add_argument("--no-tracker", action="store_true",
                        help="build the package without touching the tracker")
    args = parser.parse_args(argv)

    folder, written = build_package(
        args.company, args.role, Path(args.cv), Path(args.letter),
        Path(args.build), Path(args.register), Path(args.applications),
    )

    print(f"package: {folder.relative_to(ROOT) if folder.is_relative_to(ROOT) else folder}")
    for filename in sorted(written):
        print(f"  {filename}")

    missing = [fmt for fmt in ("docx",)
               if not any(f.endswith(fmt) for f in written)]
    if missing:
        print("  note: .docx not produced (pandoc missing) - the other formats "
              "are complete")

    if not args.no_tracker:
        result = tracker_row.append({
            "company": args.company, "role": args.role,
            "status": "in_progress", "fit_rating": args.score,
            "source": args.url, "location": args.location,
            "rationale": args.rationale, "channel": args.channel,
            "sector": args.sector,
            "cv_file": args.cv, "cover_letter_file": args.letter,
            "notes": "drafted, not yet submitted",
        })
        print(f"tracker: {result}")

    gaps = posting_archive_gaps(folder)
    if gaps:
        # Everything above is built and the tracker row is written - the work
        # is preserved. The nonzero exit is the point: the package is not
        # presentable until the posting it answers is archived beside it.
        print("POSTING ARCHIVE INCOMPLETE - write these, then re-run:")
        for gap in gaps:
            print(f"  {gap}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
