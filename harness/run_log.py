#!/usr/bin/env python3
"""Append one search-run record. Feeds the workbook's Search Runs tab.

Called by /scrape after every run, including runs that found nothing — a search
that returned zero results is a fact worth keeping, because a board that goes
quiet for a fortnight looks identical to a board that broke.

    python harness/run_log.py --portal linkedin --query "environmental analyst Winnipeg" \
        --found 24 --new 6
    python harness/run_log.py --portal companies --query "scope: companies (4)" \
        --found 3 --new 1 --notes "boreal: unverified (bot wall)"
"""

from __future__ import annotations

import argparse
import csv
import datetime
import os

LOG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run_log.csv"
)
COLUMNS = ["date", "portal", "query", "found", "new", "notes"]


def append(row: dict, path=None) -> None:
    """Append one run; `date` defaults to today, missing columns are blank."""
    path = path or LOG  # read at call time, so a patched LOG is honoured
    # An empty file needs the header just as much as a missing one. A zero-byte
    # run_log.csv (interrupted first write, a `touch`, an editor saving an empty
    # buffer) otherwise makes the first data row the header: `today.py` then
    # finds no `date` column and reports "no search has been run yet" after
    # every single search, permanently.
    is_new = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if is_new:
            writer.writerow(COLUMNS)
        writer.writerow([row.get("date") or datetime.date.today().isoformat()]
                        + [row.get(column, "") for column in COLUMNS[1:]])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for column in COLUMNS[1:]:
        parser.add_argument("--" + column, default="")
    args = parser.parse_args()
    append(vars(args))
    print("logged run to", LOG)


if __name__ == "__main__":
    main()
