#!/usr/bin/env python3
"""Keep the last N copies of a file, and let a person get one back.

`/fact` and `/tracker` both told the agent to "copy the file into backups/,
keeping the five most recent" — and nothing implemented it, so it depended on
the model remembering to improvise the right shell commands. This is those six
lines, written once.

    python harness/rotate_backup.py evidence/register.yaml     # back it up
    python harness/rotate_backup.py job_search_tracker.csv --list
    python harness/rotate_backup.py job_search_tracker.csv --restore 1

`--restore` is the half that matters to a user: backups nobody can find are
not a safety net. Restoring first backs up the *current* file, so an
accidental restore is itself undoable.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKUP_DIR = ROOT / "backups"
KEEP = 5


def _stamp() -> str:
    # Microseconds, so two backups in the same second still sort correctly.
    # The old second-resolution stamp collided, and the collision was resolved
    # by appending "-2"/"-3" AFTER the timestamp - but "-" sorts before ".", so
    # `name-120000.yaml` sorted as newer than `name-120000-3.yaml`. A batch
    # /outcome writing three rows in one second then made `--restore 1` return
    # the OLDEST of the three, and the keep-5 prune delete genuinely newer ones.
    return datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def backups_for(path: Path, backup_dir: Path | None = None) -> list[Path]:
    """Existing backups for a file, newest first.

    `backup_dir` defaults to the module's BACKUP_DIR *at call time*, not at
    import time. Binding it as a default argument made the location impossible
    to redirect, which is the same untestable-path problem the review found in
    tracker_xlsx.
    """
    backup_dir = Path(backup_dir) if backup_dir else BACKUP_DIR
    if not backup_dir.is_dir():
        return []
    return sorted(backup_dir.glob(f"{path.stem}-*{path.suffix}"), reverse=True)


def rotate(path: Path, backup_dir: Path | None = None,
           keep: int = KEEP) -> Path | None:
    """Copy `path` into backups/, then delete all but the newest `keep`."""
    backup_dir = Path(backup_dir) if backup_dir else BACKUP_DIR
    path = Path(path)
    if not path.is_file():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"{path.stem}-{_stamp()}{path.suffix}"
    shutil.copy2(path, target)
    for stale in backups_for(path, backup_dir)[keep:]:
        stale.unlink()
    return target


def restore(path: Path, index: int = 1, backup_dir: Path | None = None) -> Path:
    """Restore the Nth-newest backup (1 = most recent) over `path`."""
    backup_dir = Path(backup_dir) if backup_dir else BACKUP_DIR
    available = backups_for(Path(path), backup_dir)
    if not available:
        sys.exit(f"rotate_backup: no backups found for {path}")
    if index < 1 or index > len(available):
        sys.exit(f"rotate_backup: pick 1..{len(available)} (see --list)")
    chosen = available[index - 1]
    # Back up what is there now, so restoring is itself reversible.
    rotate(Path(path), backup_dir)
    shutil.copy2(chosen, path)
    return chosen


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file")
    parser.add_argument("--list", action="store_true", help="show backups")
    parser.add_argument("--restore", type=int, metavar="N",
                        help="restore the Nth newest backup (1 = most recent)")
    parser.add_argument("--keep", type=int, default=KEEP)
    args = parser.parse_args(argv)
    path = Path(args.file)

    if args.list:
        available = backups_for(path)
        if not available:
            print(f"no backups for {path}")
            return 0
        print(f"backups for {path} (newest first):")
        for number, backup in enumerate(available, 1):
            size = backup.stat().st_size
            when = datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"  {number}. {backup.name}  "
                  f"{when:%Y-%m-%d %H:%M}  {size:,} bytes")
        print(f"\nRestore one with: python harness/rotate_backup.py {path} "
              f"--restore 1")
        return 0

    if args.restore:
        chosen = restore(path, args.restore)
        print(f"restored {chosen.name} over {path}")
        print("the previous contents were backed up first, so this is undoable")
        return 0

    made = rotate(path, keep=args.keep)
    if made is None:
        print(f"rotate_backup: {path} does not exist yet — nothing to back up")
        return 0
    print(f"backed up {path} -> {made.relative_to(ROOT)} "
          f"(keeping {args.keep})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
