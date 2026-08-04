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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for column in COLUMNS[1:]:
        parser.add_argument("--" + column, default="")
    args = parser.parse_args()

    is_new = not os.path.exists(LOG)
    with open(LOG, "a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if is_new:
            writer.writerow(COLUMNS)
        writer.writerow(
            [datetime.date.today().isoformat()]
            + [getattr(args, column) for column in COLUMNS[1:]]
        )
    print("logged run to", LOG)


if __name__ == "__main__":
    main()
