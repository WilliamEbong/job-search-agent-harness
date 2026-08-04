"""Move submitted applications to applied/, and archive folders older than 8 weeks.

Every application lives in `documents/applications/<Company>_<Role>/`. This
script does two things, and one call does both — which is why the apply and
tracker workflows call it every run and no scheduled task is needed:

1. **Move** folders whose tracker row carries a `submitted_date` into
   `documents/applications/applied/`.
2. **Archive** anything 8 weeks past creation into
   `documents/applications/archive/` as a zip, removing the live folder.
   Applied folders age out the same way.

    python harness/archive_applications.py            # do it
    python harness/archive_applications.py --dry-run  # report only

Creation age: on Windows `st_ctime` is the folder's creation time. The oldest
file mtime inside the folder is used when it is older still, so folders whose
metadata was rewritten (by a git operation, say) cannot dodge archiving.
Everything under `documents/applications/` is gitignored, so archiving never
touches a tracked file.
"""

from __future__ import annotations

import csv
import re
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APPLICATIONS_DIR = REPO_ROOT / "documents" / "applications"
ARCHIVE_DIR = APPLICATIONS_DIR / "archive"
APPLIED_DIR = APPLICATIONS_DIR / "applied"
TRACKER_CSV = REPO_ROOT / "job_search_tracker.csv"
MAX_AGE_DAYS = 56  # 8 weeks

# Subdirectories of documents/applications/ that are not themselves applications.
RESERVED = {"archive", "applied"}


def folder_created_at(folder: Path) -> float:
    """Best available creation timestamp for a folder (epoch seconds)."""
    candidates = [folder.stat().st_ctime]
    for path in folder.rglob("*"):
        if path.is_file():
            stat = path.stat()
            candidates.append(min(stat.st_ctime, stat.st_mtime))
    return min(candidates)


def archive_due(now: float | None = None, dry_run: bool = False) -> list[str]:
    """Zip and remove every application folder older than MAX_AGE_DAYS.

    Returns the names archived (or that would be, under --dry-run).
    """
    if now is None:
        now = time.time()
    if not APPLICATIONS_DIR.is_dir():
        return []

    archived: list[str] = []
    candidates = list(APPLICATIONS_DIR.iterdir())
    if APPLIED_DIR.is_dir():
        candidates += list(APPLIED_DIR.iterdir())  # submitted work ages out too
    for folder in sorted(candidates):
        if not folder.is_dir() or folder.name in RESERVED:
            continue
        age_days = (now - folder_created_at(folder)) / 86400
        if age_days < MAX_AGE_DAYS:
            continue
        archived.append(folder.name)
        if dry_run:
            continue
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        target = ARCHIVE_DIR / folder.name
        suffix = 1
        while target.with_suffix(".zip").exists():
            suffix += 1
            target = ARCHIVE_DIR / f"{folder.name}-{suffix}"
        shutil.make_archive(str(target), "zip", root_dir=folder)
        shutil.rmtree(folder)
    return archived


def _norm(text: str) -> str:
    """Lowercase, drop punctuation, and spell '&' as 'and'.

    Folder names write it out ("Learning_and_Development") while a tracker row
    keeps the ampersand ("Learning & Development"), so both must normalise to
    the same string.
    """
    return re.sub(r"[^a-z0-9]", "", (text or "").lower().replace("&", " and "))


def _tokens(text: str) -> list[str]:
    cleaned = (text or "").lower().replace("&", " and ")
    return [t for t in re.split(r"[^a-z0-9]+", cleaned) if t]


def _company_key(company: str) -> str:
    """First word of the company name.

    Folder names are built from the company name and then diverge from the
    tracker's version of it: a legal name like "Acme, Baker & Clark LLP" becomes
    the folder "Acme_...", and "Northwind Canada" becomes
    "Northwind_Lab_Technician". Matching on a fixed-length prefix of the full
    name fails on both.
    """
    parts = re.split(r"[^A-Za-z0-9]+", (company or "").strip())
    return (parts[0] if parts else "").lower()


def match_folder(company: str, role: str, names: list[str]) -> str:
    """Pick the application folder for a tracker row, or "".

    Shared by the archiver and the workbook generator so the workbook's links
    and the applied/ move can never disagree about which folder a row belongs to.

    Folder names are shortened ("Rivermouth_Environmental_Data_Analyst") while
    the tracker keeps the full posting title ("Environmental Data Analyst, Water
    Programmes"), and word order can differ ("Senior_Lab_Technician" vs
    "Technician, Senior Laboratory"). So the test is: what fraction of the
    folder's role words appear anywhere in the row's role? Substring matching
    cannot express that.
    """
    company_key = _company_key(company)
    role_words = set(_tokens(role))
    if not company_key or not role_words:
        return ""
    best, best_score, best_size = "", 0.0, -1
    for name in names:
        if company_key not in _norm(name):
            continue
        folder_words = [t for t in _tokens(name) if t not in _tokens(company)]
        if not folder_words:
            continue
        score = sum(1 for t in folder_words if t in role_words) / len(folder_words)
        # Ties go to the more specific folder: "Analyst_Water_Programmes" beats
        # "Analyst" when the row's role names the water programmes posting.
        if score > best_score or (score == best_score and len(folder_words) > best_size):
            best, best_score, best_size = name, score, len(folder_words)
    return best if best_score >= 0.6 else ""


def submitted_folders() -> set[str]:
    """Folder names for tracker rows carrying a submitted_date.

    `submitted_date` is a trailing column: empty means drafted but not sent, a
    date means the user actually applied. Rows written before the column existed
    read as empty, so nothing moves by accident.
    """
    if not TRACKER_CSV.exists() or not APPLICATIONS_DIR.is_dir():
        return set()
    live = [d.name for d in APPLICATIONS_DIR.iterdir()
            if d.is_dir() and d.name not in RESERVED]
    wanted: set[str] = set()
    with TRACKER_CSV.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if not (row.get("submitted_date") or "").strip():
                continue
            hit = match_folder(row.get("company", ""), row.get("role", ""), live)
            if hit:
                wanted.add(hit)
    return wanted


def move_applied(dry_run: bool = False) -> list[str]:
    """Move folders for submitted applications into documents/applications/applied/."""
    names = sorted(submitted_folders())
    if not dry_run and names:
        APPLIED_DIR.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    for name in names:
        source, destination = APPLICATIONS_DIR / name, APPLIED_DIR / name
        if destination.exists():
            continue
        moved.append(name)
        if not dry_run:
            shutil.move(str(source), str(destination))
    return moved


def main(argv: list[str]) -> int:
    dry_run = "--dry-run" in argv

    moved = move_applied(dry_run=dry_run)
    verb = "would move" if dry_run else "moved"
    for name in moved:
        print(f"{verb} to applied/: {name}")
    if not moved:
        print("no submitted applications to move")

    names = archive_due(dry_run=dry_run)
    verb = "would archive" if dry_run else "archived"
    if names:
        for name in names:
            print(f"{verb}: {name}")
    else:
        print("no application folders due for archiving")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
