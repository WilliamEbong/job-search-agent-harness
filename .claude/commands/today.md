# /today - What Needs Doing, and What To Type

You are giving the user their job search in one screen, ending with a numbered list of
actions they can pick from. This is the command they run each morning; everything else is
reachable from it.

```
/today
```

It reads. It never writes, so it is always safe to run.

---

## Step 1: Check they are set up

If `evidence/register.yaml` does not exist, this is a new user. Say so in one line and
offer to start:

> You have not set up a profile yet. Want to do that now? It takes about five minutes —
> I read your CV, ask a few questions, and then I can start finding jobs.

If they say yes, run `/setup-harness`. Do not print an empty dashboard at someone who has
nothing in it yet.

## Step 2: Gather the state

```
python harness/today.py --json
```

One read-only script assembles everything: open applications and how long each has been
quiet, interviews in progress, postings closing soon, shortlisted jobs not yet applied
to, and how long since the last search. It creates no state.

**Days quiet counts from the most recent dated note, not from the application date**, so
a follow-up you already sent resets the clock. If the workbook and this disagree, this is
right.

## Step 3: Refresh the workbook if it is stale

If `job_search_tracker.csv` is newer than `Job_Search_Tracker.xlsx`, run
`python harness/tracker_xlsx.py` quietly and mention it in one clause. The user should
never have to remember to run `/tracker` just to keep the spreadsheet current.

## Step 4: Show them the screen

Present the script's output, lightly. Keep it short — this is a glance, not a report:

- **Follow-ups due** — open applications quiet for 10+ days with fewer than two
  follow-ups already sent.
- **Interviewing** — anything at `interview_only`.
- **Closing soon** — shortlisted postings with a deadline inside two weeks.
- **Shortlisted, not yet applied to** — jobs that passed the gates and are still waiting
  on a decision.
- **Waiting** — one line with a count. These need nothing today; do not list them.
- **Last search** — how many days ago.

Then the numbered actions. **The point of this command is that the answer to "what now?"
is a number**, so always end with them, and keep each label to one line naming the
company.

## Step 5: Do what they pick

They will answer with a number, or in their own words ("chase Rivermouth", "find me
something new"). Either way, run the matching workflow:

| They pick | You run |
|---|---|
| a follow-up | `/outcome <company>` and go to its follow-up branch |
| a closing-soon or shortlisted job | `/apply-any <url>` |
| a new search | `/scrape` |
| set-up | `/setup-harness` |

Confirm what you are about to do in one line, then do it. Do not re-print the dashboard
afterwards.

## What this command does not do

It does not change the tracker, write state, or make decisions. If nothing needs
attention it says so in one line rather than manufacturing a task — a daily brief that
always invents something to do stops being worth reading.
