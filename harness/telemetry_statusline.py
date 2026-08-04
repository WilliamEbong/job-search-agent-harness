#!/usr/bin/env python3
"""Claude Code statusline script that also mirrors usage telemetry to disk.

Claude Code pipes a JSON blob to its statusline command on each update. That
blob is the **only** channel through which a running agent can learn how full
its context window is or how much of a subscription window has been consumed —
hooks receive no usage fields at all, and Codex exposes nothing programmatic.

So this script does two jobs:

1. prints a one-line status for the user (its actual job);
2. writes the interesting numbers to `state/telemetry.json`, where the
   continuity workflow reads them at milestones.

Register it during setup:

    claude config set statusLine.command "python harness/telemetry_statusline.py"

    (or in .claude/settings.local.json —
     never .claude/settings.json, which is guard-frozen)

Honest caveats, repeated in the JSON itself so nobody reads a number without
them:

* `context_window.used_percentage` counts **input tokens only**, so it
  understates true consumption.
* It is null before the first API call of a session, and resets after
  `/compact` — a low value can mean "fresh context", not "plenty of room".
* Rate-limit percentages are only present on Pro/Max plans.

If any field is missing this writes what it has and marks the rest `null`. It
never guesses, and it never fails the statusline: a telemetry mirror that
crashes the status bar would be a worse bug than having no telemetry.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_DIR = os.path.join(ROOT, "state")
TELEMETRY = os.path.join(STATE_DIR, "telemetry.json")

CAVEATS = [
    "context_pct counts input tokens only and understates true usage",
    "context_pct is null before the first API call and resets after /compact",
    "rate-limit percentages are present on Pro/Max plans only",
]


def _dig(data: dict, *path, default=None):
    """Fetch a nested key, returning default rather than raising."""
    current = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def extract(payload: dict) -> dict:
    return {
        "context_pct": _dig(payload, "context_window", "used_percentage"),
        "five_hour_pct": _dig(payload, "rate_limits", "five_hour", "used_percentage"),
        "seven_day_pct": _dig(payload, "rate_limits", "seven_day", "used_percentage"),
        "model": _dig(payload, "model", "display_name"),
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "caveats": CAVEATS,
    }


def write_telemetry(record: dict) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    # Write-and-replace so a reader never sees a half-written file.
    temporary = TELEMETRY + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)
    os.replace(temporary, TELEMETRY)


def render(record: dict) -> str:
    parts = []
    if record.get("model"):
        parts.append(str(record["model"]))
    if record.get("context_pct") is not None:
        parts.append(f"ctx {record['context_pct']:.0f}%")
    if record.get("five_hour_pct") is not None:
        parts.append(f"5h {record['five_hour_pct']:.0f}%")
    if record.get("seven_day_pct") is not None:
        parts.append(f"7d {record['seven_day_pct']:.0f}%")
    return " · ".join(parts) if parts else "harness"


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    record = extract(payload)
    try:
        write_telemetry(record)
    except OSError:
        # A read-only checkout or a locked file must not take the status bar
        # down with it. No telemetry is a degraded state, not a broken one.
        pass

    print(render(record))
    return 0


if __name__ == "__main__":
    sys.exit(main())
