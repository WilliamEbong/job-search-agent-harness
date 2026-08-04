#!/usr/bin/env python3
"""The only writer of job_search_tracker.csv.

Before this existed, three commands each described appending a CSV row *in
prose* and the model hand-assembled the text every run. Two problems followed
from that, and both were live:

1. **Two different headers.** Upstream's `/outcome` documents a 13-column
   create-header with no `submitted_date`. `archive_applications.py` reads
   `submitted_date` to decide what moves to `applied/`. So on any tracker that
   `/outcome` created first, **the applied/ move silently never fired, forever.**
   `append()` heals that: a short header is upgraded to the full 16 columns on
   first write, existing data preserved, backup taken first.

2. **Quoting left to a language model.** `notes` and `rationale` are free text
   and routinely contain commas and quotes. `csv.DictWriter` handles that
   correctly by construction; prose instructions do not.

    python harness/tracker_row.py --company "Acme" --role "Data Analyst" \
        --status in_progress --fit 82 --source https://... --location "Winnipeg, MB"
    python harness/tracker_row.py --company "Acme" --role "Data Analyst" \
        --set submitted_date=2026-08-04 --set status=interview_only

Follows the DictWriter pattern already established by harness/run_log.py.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import date
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
ROOT = HARNESS_DIR.parent
TRACKER_CSV = ROOT / "job_search_tracker.csv"

sys.path.insert(0, str(HARNESS_DIR))
import rotate_backup  # noqa: E402
import status as status_mod  # noqa: E402

# The full header. Upstream's 13 columns in upstream's order, plus the three
# harness columns. Order matters: anything reading by position (a human in
# Excel) sees upstream's layout first.
HEADER = [
    "date", "company", "sector", "role", "role_type", "channel", "status",
    "contact_person", "fit_rating", "notes", "cv_file", "cover_letter_file",
    "source",
    # Harness additions.
    "location", "rationale", "submitted_date",
]


def read_rows(path: Path = TRACKER_CSV) -> tuple[list[dict], list[str]]:
    """Return (rows, header). Missing file → ([], HEADER)."""
    if not path.exists():
        return [], list(HEADER)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        existing_header = list(reader.fieldnames or HEADER)
        rows = []
        for row in reader:
            # A row with more fields than the header puts the surplus in a list
            # under the None key. Fold it back into notes rather than letting a
            # later `.strip()` raise AttributeError on a list.
            surplus = row.pop(None, None)
            if surplus:
                extra = " ".join(str(s) for s in surplus if s)
                row["notes"] = f"{row.get('notes', '')} {extra}".strip()
            if any((value or "").strip() for value in row.values()):
                rows.append(row)
    return rows, existing_header


def write_rows(rows: list[dict], path: Path = TRACKER_CSV) -> None:
    """Rewrite the file with the full header. Backup first — always."""
    if path.exists():
        rotate_backup.rotate(path)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in HEADER})
    os.replace(tmp, path)  # atomic: a crash never leaves a half-written tracker


def append(row: dict, path: Path = TRACKER_CSV) -> str:
    """Append one application. Returns 'created' | 'appended' | 'healed'."""
    rows, existing_header = read_rows(path)
    row = {key: row.get(key, "") for key in HEADER}
    row.setdefault("date", date.today().isoformat())
    if not row.get("date"):
        row["date"] = date.today().isoformat()
    row["status"] = status_mod.normalize(row.get("status")) or status_mod.IN_PROGRESS

    if not path.exists():
        write_rows(rows + [row], path)
        return "created"
    if set(existing_header) != set(HEADER):
        # The 13-column case. Rewrite once with the full header so
        # submitted_date exists and the applied/ move can work.
        write_rows(rows + [row], path)
        return "healed"
    with path.open("a", newline="", encoding="utf-8") as handle:
        csv.DictWriter(handle, fieldnames=HEADER,
                       extrasaction="ignore").writerow(row)
    return "appended"


def update(company: str, role: str, changes: dict,
           path: Path = TRACKER_CSV) -> int:
    """Apply field changes to matching rows. Returns the number updated."""
    rows, _ = read_rows(path)
    company_key = (company or "").strip().lower()
    role_key = (role or "").strip().lower()
    matched = 0
    for row in rows:
        if (row.get("company") or "").strip().lower() != company_key:
            continue
        if role_key and role_key not in (row.get("role") or "").strip().lower():
            continue
        for key, value in changes.items():
            if key not in HEADER:
                sys.exit(f"tracker_row: unknown column {key!r}. "
                         f"Known columns: {', '.join(HEADER)}")
            row[key] = status_mod.normalize(value) if key == "status" else value
        matched += 1
    if matched:
        write_rows(rows, path)
    return matched


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--company", required=True)
    parser.add_argument("--role", default="")
    parser.add_argument("--tracker", default=str(TRACKER_CSV))
    for column in ("date", "sector", "role_type", "channel", "status",
                   "contact_person", "notes", "cv_file", "cover_letter_file",
                   "source", "location", "rationale", "submitted_date"):
        parser.add_argument("--" + column.replace("_", "-"), dest=column,
                            default=None)
    parser.add_argument("--fit", dest="fit_rating", default=None)
    parser.add_argument("--set", action="append", default=[], metavar="COL=VALUE",
                        help="update an existing row instead of appending")
    args = parser.parse_args(argv)
    path = Path(args.tracker)

    if args.set:
        changes = {}
        for item in args.set:
            if "=" not in item:
                sys.exit(f"tracker_row: --set expects COL=VALUE, got {item!r}")
            key, value = item.split("=", 1)
            changes[key.strip()] = value
        count = update(args.company, args.role, changes, path)
        print(f"tracker_row: updated {count} row(s)" if count
              else f"tracker_row: no row matched {args.company} / {args.role}")
        return 0 if count else 1

    row = {key: getattr(args, key) or "" for key in HEADER
           if hasattr(args, key)}
    row["company"], row["role"] = args.company, args.role
    result = append(row, path)
    print(f"tracker_row: {result} - {args.company} / {args.role} "
          f"(status {row.get('status') or 'in_progress'})")
    if result == "healed":
        print("  note: the tracker was missing the location/rationale/"
              "submitted_date columns and has been upgraded. Without "
              "submitted_date, applications could never move to applied/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
