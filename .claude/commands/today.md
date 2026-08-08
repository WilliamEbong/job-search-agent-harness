# /today - What Needs Doing, and What To Type

You are giving the user their job search in one screen, ending with a numbered list of
actions they can pick from. This is the command they run each morning; everything else is
reachable from it.

```
/today
```

It mostly reads, and it is always safe to run. The two things it can write are described
at the end.

---

## Step 0: Check they are set up

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
- **Trials to judge** — a `/discover` trial family whose finds have piled up. The script
  counts them; the keep-or-drop decision lives in `/discover review`, which asks first.

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
| a trial family to judge | `/discover review` |
| an offer to think about | `/offer <company>` |
| set-up | `/setup-harness` |

Confirm what you are about to do in one line, then do it. Do not re-print the dashboard
afterwards.

## Step 6: Offer to close out the stale ones

When several open applications have been silent a long time (60+ days, two follow-ups
already sent), offer to close them in one go rather than making the user run `/outcome`
six times:

> Six applications have been quiet for over two months with two follow-ups each.
> Mark them all as no reply? They stay in your history and your funnel; they just
> stop showing up here.

Only on a yes, and only for the ones listed:

```
python harness/tracker_row.py --company "<Company>" --role "<Role>" --set status=no_response
```

`no_response` is a real outcome, not a deletion — the rows stay, the response-rate
calculation stays honest, and the dashboard stops nagging about applications that are
finished in practice.

Never do this without asking, and never for anything at `interview_only`.

## What this command does not do

**Reading is always safe.** Reading the state and showing the screen create nothing and
change nothing, so `/today` can be run as often as you like.

Two steps write, and the distinction between them is the rule this whole system follows:
**a write that regenerates a view proceeds; a write that changes what is recorded asks
first.** So Step 3 refreshes the stale workbook without asking — it is rebuilt from the
CSV and can never hold the only copy of anything — while the batch close-out in Step 6
changes recorded statuses and always needs a yes. Nothing else writes.

It makes no decisions on the user's behalf. And if nothing needs attention it says so in
one line rather than manufacturing a task — a daily brief that always invents something
to do stops being worth reading.
