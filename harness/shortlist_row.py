#!/usr/bin/env python3
"""Append a scored candidate to `shortlist.csv`. The one writer.

Same reason `tracker_row.py` exists, and the same failure it prevents.
`rationale` is free text written by a language model and routinely contains
the commas and quotes a verdict needs — "states NOK 540,000; your minimum is
620,000" — and hand-assembled CSV gets that wrong eventually rather than
never. A row whose `rationale` field bleeds into `deadline` silently stops
`/today` warning about closing dates for every row read after it.

Two writers used to be told to produce this file in prose: `/scrape` Step 6,
which at least published the column list, and `/apply-any`'s autonomy ladder,
which named neither a path nor a schema.

    python harness/shortlist_row.py --company "Acme" --role "Data Analyst" \\
        --score 82 --verdict qualified --url https://... \\
        --rationale "strong QA/QC match; GIS is a gap" --deadline 2026-09-15

Verdicts are the four `/scrape` defines. An unknown one is rejected rather
than written, because the workbook colours on these and a typo would show up
as an uncoloured row nobody notices.
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
ROOT = HARNESS_DIR.parent
SHORTLIST_CSV = ROOT / "shortlist.csv"

HEADER = ["date", "company", "role", "location", "source", "url", "score",
          "verdict", "rationale", "deadline"]

# `/scrape` Step 6's table, and what tracker_xlsx colours the Shortlist tab on.
VERDICTS = ("qualified", "not-drafted", "not-resolved", "gate-fail")


def append(row: dict, path: Path = SHORTLIST_CSV) -> str:
    """Append one scored candidate. Returns 'created' or 'appended'."""
    verdict = (row.get("verdict") or "").strip()
    if verdict not in VERDICTS:
        sys.exit(f"shortlist_row: unknown verdict {verdict!r}. "
                 f"Use one of: {', '.join(VERDICTS)}")
    row = {key: row.get(key, "") for key in HEADER}
    if not row["date"]:
        row["date"] = date.today().isoformat()

    is_new = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, extrasaction="ignore")
        if is_new:
            writer.writeheader()
        writer.writerow(row)
    return "created" if is_new else "appended"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--company", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--verdict", required=True, choices=VERDICTS)
    parser.add_argument("--shortlist", default=str(SHORTLIST_CSV))
    for column in ("date", "location", "source", "url", "score", "rationale",
                   "deadline"):
        parser.add_argument("--" + column, default="")
    args = parser.parse_args(argv)

    path = Path(args.shortlist)
    result = append({key: getattr(args, key) for key in HEADER}, path)
    print(f"shortlist: {result} {args.company} - {args.role} ({args.verdict})")
    return 0


def demo() -> None:
    """Runnable check: the quoting that prose CSV gets wrong."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "shortlist.csv"
        assert append({"company": "Acme", "role": "Data Analyst",
                       "verdict": "not-drafted",
                       "rationale": 'states NOK 540,000; minimum is 620,000, so "low"',
                       "deadline": "2026-09-15"}, path) == "created"
        assert append({"company": "Beta", "role": "Analyst",
                       "verdict": "qualified"}, path) == "appended"
        rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
        assert len(rows) == 2, rows
        # The comma and the quotes stay inside rationale; deadline is intact.
        assert rows[0]["deadline"] == "2026-09-15", rows[0]
        assert "540,000" in rows[0]["rationale"], rows[0]
        assert rows[1]["date"], "date defaults to today"
    print("shortlist_row: OK")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-check":
        demo()
    else:
        sys.exit(main())
