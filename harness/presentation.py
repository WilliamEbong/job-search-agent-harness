#!/usr/bin/env python3
"""The one place that answers "how many pages should the CV be?".

The 2-page rule used to be hard-coded in eight prose files. It is now a user
preference (`preferences.yaml` -> `presentation.cv_pages`): an integer page
target, or `adaptive` (drafter picks 1 or 2 per posting and justifies it).
Anything missing or unreadable falls back to 2 — the historical default — so
a register created before this field existed behaves exactly as before.

The cover letter is not configurable: always 1 page.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CV_PAGES = 2
ADAPTIVE = "adaptive"


def cv_page_target(prefs_path: Path | str = ROOT / "preferences.yaml") -> int | str:
    """Return the configured CV page target: an int, or `"adaptive"`.

    Defaults to 2 on a missing file, missing section, missing key, or any
    unparseable value — backward compatibility is the point, so this never
    raises.
    """
    path = Path(prefs_path)
    if not path.is_file():
        return DEFAULT_CV_PAGES
    try:
        import yaml
        prefs = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return DEFAULT_CV_PAGES
    if not isinstance(prefs, dict):
        return DEFAULT_CV_PAGES
    value = (prefs.get("presentation") or {}).get("cv_pages", DEFAULT_CV_PAGES)
    if isinstance(value, str) and value.strip().lower() == ADAPTIVE:
        return ADAPTIVE
    if isinstance(value, int) and value >= 1:
        return value
    return DEFAULT_CV_PAGES


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("preferences", nargs="?", default=str(ROOT / "preferences.yaml"),
                        help="path to preferences.yaml (default: repo root)")
    # Without argparse, `--help` was read as a path, missed, and printed the
    # default 2 - a confidently wrong answer to a question about the help text.
    print(cv_page_target(parser.parse_args().preferences))
