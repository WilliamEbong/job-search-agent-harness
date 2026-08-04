#!/usr/bin/env python3
"""What needs doing today, and what to type to do it.

Every ingredient for this already existed — the tracker CSV, the run log, the
per-application outcome files, the shortlist — and nothing assembled them. A
user opening a session on Monday had no way to ask "where am I?" short of
opening a spreadsheet and reading it themselves.

Read-only. It creates no state and changes nothing, so it is always safe to run.

    python harness/today.py
    python harness/today.py --json     # for the agent to turn into an action menu

The output ends with numbered actions, because a list of facts still leaves the
user to work out the command. The whole point is that the answer to "what now?"
is a number.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
ROOT = HARNESS_DIR.parent

sys.path.insert(0, str(HARNESS_DIR))
import status as status_mod  # noqa: E402

TRACKER = ROOT / "job_search_tracker.csv"
SHORTLIST = ROOT / "shortlist.csv"
RUN_LOG = ROOT / "run_log.csv"
APPLICATIONS = ROOT / "documents" / "applications"
REGISTER = ROOT / "evidence" / "register.yaml"
PREFERENCES = ROOT / "preferences.yaml"

# Matches tracker_xlsx's FOLLOWUP_DAYS and /outcome's threshold. One number.
FOLLOWUP_DAYS = 10
STALE_SEARCH_DAYS = 7
DATE_IN_NOTE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [row for row in csv.DictReader(handle)
                if any((value or "").strip() for value in row.values())]


def parse_date(value: str | None):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime((value or "").strip(), fmt).date()
        except ValueError:
            continue
    return None


def days_quiet(row: dict, today: date) -> int | None:
    """Days since the last thing that happened on this application.

    Counts from the most recent of the application date and any dated entry in
    `notes` — so a logged follow-up resets the clock. The workbook used to count
    from the application date alone, which meant it kept saying a follow-up was
    due after one had been sent.
    """
    stamps = [parse_date(row.get("date"))]
    stamps += [parse_date(found) for found in DATE_IN_NOTE.findall(row.get("notes") or "")]
    stamps = [s for s in stamps if s]
    if not stamps:
        return None
    return (today - max(stamps)).days


def followups_sent(row: dict) -> int:
    return len(re.findall(r"followed up", (row.get("notes") or ""), re.I))


def collect(today: date | None = None, root: Path = ROOT) -> dict:
    today = today or date.today()
    tracker = read_csv(root / "job_search_tracker.csv")
    shortlist = read_csv(root / "shortlist.csv")
    runs = read_csv(root / "run_log.csv")

    open_rows = [r for r in tracker if status_mod.is_open(r.get("status"))]

    followups = []
    waiting = []
    for row in open_rows:
        quiet = days_quiet(row, today)
        entry = {
            "company": row.get("company", ""),
            "role": row.get("role", ""),
            "days_quiet": quiet,
            "followups_sent": followups_sent(row),
            "status": status_mod.normalize(row.get("status")),
        }
        # Two follow-ups is the cap /outcome enforces; past that, chasing is
        # not the next useful action.
        if quiet is not None and quiet >= FOLLOWUP_DAYS and entry["followups_sent"] < 2:
            followups.append(entry)
        else:
            waiting.append(entry)

    interviews = [r for r in open_rows
                  if status_mod.normalize(r.get("status")) == status_mod.INTERVIEW_ONLY]

    # Shortlisted and worth acting on, but no application exists yet.
    applied_keys = {((r.get("company") or "").strip().lower(),
                     (r.get("role") or "").strip().lower()) for r in tracker}
    undrafted = [
        {"company": r.get("company", ""), "role": r.get("role", ""),
         "score": r.get("score", ""), "url": r.get("url", ""),
         "deadline": r.get("deadline", "")}
        for r in shortlist
        if r.get("verdict") == "qualified"
        and ((r.get("company") or "").strip().lower(),
             (r.get("role") or "").strip().lower()) not in applied_keys
    ]

    last_run = None
    for row in runs:
        found = parse_date(row.get("date"))
        if found and (last_run is None or found > last_run):
            last_run = found
    search_age = (today - last_run).days if last_run else None

    # Deadlines worth naming, from whichever rows carry one.
    deadlines = []
    for row in shortlist:
        due = parse_date(row.get("deadline"))
        if due and 0 <= (due - today).days <= 14:
            deadlines.append({"company": row.get("company", ""),
                              "role": row.get("role", ""),
                              "closes_in": (due - today).days})

    return {
        "date": today.isoformat(),
        "onboarded": (root / "evidence" / "register.yaml").exists(),
        "followups": followups,
        "interviews": interviews and [
            {"company": r.get("company", ""), "role": r.get("role", ""),
             "notes": (r.get("notes") or "")[:80]} for r in interviews] or [],
        "waiting": waiting,
        "undrafted": undrafted,
        "deadlines": sorted(deadlines, key=lambda d: d["closes_in"]),
        "search_age_days": search_age,
        "total_open": len(open_rows),
        "total_applications": len(tracker),
    }


def actions(state: dict) -> list[dict]:
    """The numbered menu. Each item carries the command that performs it."""
    items: list[dict] = []
    if not state["onboarded"]:
        return [{"label": "Set up your profile (about 5 minutes)",
                 "command": "/setup-harness"}]

    for entry in state["followups"][:3]:
        items.append({
            "label": f"Follow up with {entry['company']} "
                     f"({entry['days_quiet']} days quiet)",
            "command": f"/outcome {entry['company']}",
        })
    for entry in state["deadlines"][:2]:
        items.append({
            "label": f"{entry['company']} closes in {entry['closes_in']} days",
            "command": f"apply {entry['company']} {entry['role']}",
        })
    for entry in state["undrafted"][:2]:
        score = f" (scored {entry['score']})" if entry.get("score") else ""
        items.append({
            "label": f"Apply to {entry['company']} - {entry['role']}{score}",
            "command": f"apply {entry['url'] or entry['company']}",
        })
    age = state["search_age_days"]
    if age is None:
        items.append({"label": "Search for jobs - you have not run one yet",
                      "command": "/scrape"})
    elif age >= STALE_SEARCH_DAYS:
        items.append({"label": f"Search for new jobs (last run {age} days ago)",
                      "command": "/scrape"})
    return items


def render(state: dict) -> str:
    lines = [f"Job search - {state['date']}", ""]

    if not state["onboarded"]:
        lines += ["You have not set up a profile yet, so there is nothing to "
                  "report.", ""]
    else:
        if state["followups"]:
            lines.append(f"Follow-ups due ({len(state['followups'])}):")
            for entry in state["followups"]:
                lines.append(f"  - {entry['company']} - {entry['role']} "
                             f"({entry['days_quiet']} days quiet)")
            lines.append("")
        if state["interviews"]:
            lines.append(f"Interviewing ({len(state['interviews'])}):")
            for entry in state["interviews"]:
                lines.append(f"  - {entry['company']} - {entry['role']}")
            lines.append("")
        if state["deadlines"]:
            lines.append("Closing soon:")
            for entry in state["deadlines"]:
                lines.append(f"  - {entry['company']} - {entry['role']} "
                             f"(in {entry['closes_in']} days)")
            lines.append("")
        if state["undrafted"]:
            lines.append(f"Shortlisted, not yet applied to "
                         f"({len(state['undrafted'])}):")
            for entry in state["undrafted"]:
                score = f" - scored {entry['score']}" if entry.get("score") else ""
                lines.append(f"  - {entry['company']} - {entry['role']}{score}")
            lines.append("")

        waiting = len(state["waiting"])
        if waiting:
            lines.append(f"Waiting on {waiting} other application(s); nothing "
                         f"to do about those today.")
        age = state["search_age_days"]
        if age is None:
            lines.append("No job search has been run yet.")
        elif age >= STALE_SEARCH_DAYS:
            lines.append(f"Last job search was {age} days ago.")
        else:
            lines.append(f"Last job search: {age} day(s) ago.")
        lines.append("")

    menu = actions(state)
    if menu:
        lines.append("What would you like to do?")
        for number, item in enumerate(menu, 1):
            lines.append(f"  {number}. {item['label']}")
        lines.append("")
        lines.append("Say a number, or just tell me what you want to do.")
    else:
        lines.append("Nothing needs your attention today.")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true",
                        help="emit the raw state plus the action list")
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)

    state = collect(root=Path(args.root))
    if args.json:
        print(json.dumps({**state, "actions": actions(state)}, indent=2))
    else:
        print(render(state))
    return 0


if __name__ == "__main__":
    sys.exit(main())
