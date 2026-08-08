# /tracker - Regenerate the Tracker Workbook and Run the Archiver

You are refreshing the owner-facing view of the job search and tidying the application
folders. Both are mechanical; neither invents or changes any fact.

```
/tracker
/tracker --dry-run     # report what would move, change nothing
/tracker --archive     # also zip and REMOVE folders 8+ weeks old
```

Run this after `/outcome`, after `/apply-any`, or any time the CSV changes.

---

## The rule that makes this safe

`job_search_tracker.csv` and the per-application `outcome.md` files are the **only**
sources of truth. `Job_Search_Tracker.xlsx` is a **view**, regenerated from them and never
read back.

That one-directional design is what makes it safe to regenerate whenever you like: the
workbook can never hold the only copy of a note, so rebuilding it cannot lose one. The
cost is that editing a status in Excel does nothing — corrections travel through
conversation ("rejected by Rivermouth") into `/outcome`, which is the single writer of
the status column.

Never add a write-back path. It is the obvious feature to want and it converts a
lossless view into a second, competing truth store.

## Step 1: Nothing to back up — this command does not write the CSV

`harness/tracker_row.py` rotates a backup on **every** write, so the pre-edit copy
already exists by the time you get here. Rotating again from this command would be worse
than useless: it keeps only the five most recent, so five routine `/tracker` runs would
evict every genuine pre-edit backup — exactly the ones wanted after a bad `/outcome`.

To undo a bad change: `python harness/rotate_backup.py job_search_tracker.csv --list`,
then `--restore 1`. The workbook needs no backup; it is regenerated from the CSV.

## Step 2: Regenerate the workbook

```
python harness/tracker_xlsx.py
```

If the CSV does not exist yet the script says so and exits 0 — that is a new user, not an
error.

**Four tabs** are produced:

| Tab | What it holds |
|---|---|
| **Applications** | Every row, newest first. Frozen header, autofilter, status colours, Open/Closed split, days-since, follow-up-due flag, live hyperlinks to the posting and to the application folder. |
| **Summary** | Funnel (applied → responded → interviewed → offers), response and interview rates, applications per week, follow-ups due, breakdown by status and by channel. |
| **Shortlist** | Scored candidates that did *not* become applications, with the verdict and the reason — so the reasoning is visible instead of lost. Highest score first, gate failures last. |
| **Search Runs** | One row per `/scrape` run: date, portal, query, found, new, notes. |

Verify the file was written and report the counts the script prints. Do not claim the
workbook regenerated without checking the script's exit status.

## Step 3: Run the archiver

```
python harness/archive_applications.py
```

One call does two things; never skip it:

- **Moves submitted applications** into `documents/applications/applied/`. The trigger is
  the tracker's `submitted_date` column (ISO `YYYY-MM-DD`; empty means drafted but not
  sent). Fill it in when the user says they applied — `python harness/tracker_row.py
  --company "..." --role "..." --set submitted_date=<YYYY-MM-DD>` — and the folder moves
  itself on the next run. Nothing else fills that column, so nothing else triggers the
  move.
- **Reports anything 8+ weeks past creation.** It does **not** delete: zipping those
  folders into `documents/applications/archive/` and removing them needs an explicit
  `--archive`, because doing it unattended once destroyed folders belonging to live
  interview processes. Applied folders age the same way.

Use `--dry-run` first if the user wants to see what would happen.

## Step 4: Report

```
Tracker updated.
  Job_Search_Tracker.xlsx — N applications, M follow-ups due
  moved to applied/:   <names, or "none">
  due for archiving:   <names, or "none">   <- reported only; nothing deleted
  backup: backups/job_search_tracker-<timestamp>.csv
```

If any follow-ups are due, name the companies — that number is the reason this command
exists, and a count on its own is not actionable.

## Self-test

```
python -m unittest tests_harness.test_tracker
```

Covers the four tabs, the Open/Closed split, hyperlink generation, regenerate-twice
idempotence, the note-preservation guarantee, the shared folder matcher, and the
archiver's move and zip behaviour.
