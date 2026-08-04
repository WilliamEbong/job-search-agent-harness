# /scrape - Find Jobs (usage modes, five search scopes, cost posture)

You are searching for open jobs and producing a ranked shortlist. This is the one wrapper
around discovery: it decides **what to search** (scope), **how hard to look** (mode), and
tells the user **what the run will cost** before it starts.

```
/scrape                                   # default scope and mode from preferences.yaml
/scrape --mode focused --board freehire   # one board, shallow screen
/scrape --scope companies                 # every companies.yaml careers page
/scrape --scope company "Prairie Grid Utilities"
/scrape --scope boards --mode balanced
/scrape --scope all --mode full --limit 40
```

---

## Step 0: Check they are set up

If `evidence/register.yaml` or `preferences.yaml` is missing, stop and say so in one
line, then offer to fix it — never fail into undefined behaviour, and never read the
shipped `.example.yaml` as though it were the user's:

> You have not set up a profile yet. Want to do that now? It takes about five minutes.

If they say yes, run `/setup-harness` and come back here afterwards.

## Step 1: Resolve scope and mode

A bare `/scrape` should never require the user to choose. Resolve in this order:

1. the scope and mode of the **last run**, from the newest `run_log.csv` row;
2. `default_search_scope` and `usage.mode` in `preferences.yaml`;
3. `boards` + `focused`.

Then print one line naming what you are about to search and the nearest
alternative — so the fifteen scope-and-mode combinations stay available without
anyone having to learn them:

> Searching your 4 job boards (focused). Say "companies" to check your saved
> employers instead, or "everything" for both.

Per-run flags override all of it; nothing is written back unless the user says
"make that the default".

**The five scopes** — this is the whole selection surface:

| Scope | Searches |
|---|---|
| `--scope board <name(s)>` | Only the named board(s). |
| `--scope company <name(s)>` | Only the named companies-of-interest careers page(s). |
| `--scope companies` | Every enabled entry in `companies.yaml`. |
| `--scope boards` | Every enabled board in `.agents/skills/*-search/`. |
| `--scope all` | Both rosters — every board and every company. |

Both rosters are **living lists**. A board added last week via `/add-portal` and a company
added this morning via `/companies` are both included by the next matching run; nothing
needs re-onboarding. If a named board or company does not exist, say so and list what is
available rather than silently searching a subset.

**The three modes** decide depth and volume, with caps from `preferences.yaml`:

| Mode | Depth | Caps |
|---|---|---|
| `focused` | One source per run, shallow fit screen, **no documents generated** | `max_evaluations`, `max_packages_per_run: 0` |
| `balanced` | All sources in scope, dedupe and rank, deeper evaluation for promising jobs | documents only on selection |
| `full` | Deep evaluation and research, automatic packages above `auto_package_threshold` | `max_packages_per_run` |

Caps apply **within** any scope. `--scope all --mode full` is still bounded.

## Step 2: Print the cost posture, before doing anything

Every run states what it is about to do, in plain language, **before** it starts:

```
Cost posture for this run
  Scope: all boards (4) + companies of interest (5) = 9 sources
  Mode:  full — deep evaluation, research, and up to 3 application packages
  Caps:  60 evaluations, 3 packages
  This is the heaviest mode. On a standard subscription a run like this can
  consume a large share of a session window.
Proceed? (yes / switch to balanced / cancel)
```

Two rules about that block:

- **Never fabricate token arithmetic.** State sources, caps and qualitative weight. A
  precise-looking number nobody can verify is worse than an honest description, because
  it invites the user to plan around it.
- In `focused` mode the posture is one line and the run proceeds; the whole point of that
  mode is minimal ceremony. Confirm before `full`, and before any run that will generate
  documents.

## Step 3: Search — delegate the fetch, own the selection

**This command decides *what* to search and *how hard*. The `job-scraper` skill does the
fetching and owns the memory of what has already been seen.** That split matters: the
skill writes `job_scraper/seen_jobs.json`, and upstream `/rank` and `/upskill` read only
that file. A search that skips it leaves both of them with nothing to work on and
re-surfaces yesterday's postings as though they were new.

**Boards** — invoke the **`job-scraper` skill** (`.claude/skills/job-scraper/SKILL.md`)
for the boards in scope and let it run each board's CLI, deduplicate against
`seen_jobs.json`, extract deadlines, flag mass-postings, and check portal health. Never
write scraping code here; a board with no CLI gets one through upstream `/add-portal`,
which handles robots/ToS checking, scaffolding and a live test.

**Companies of interest** — for each selected entry, fetch its `careers_url` and look for
openings matching the profile. Escalate per `RUNTIME-MAP.md`: plain fetch → Firecrawl
structured extraction → Playwright. **No custom scrapers.**

Record company-sourced results in `seen_jobs.json` too, with `source: company:<name>`, so
a role found on an employer's own page is deduplicated against the same memory as a board
hit and is visible to `/rank`. The entry fields are additive — adding a source tag does
not disturb anything upstream reads.

If a careers page cannot be read — JavaScript shell, bot wall, login — record
`access: unverified` with a note on that entry in `companies.yaml` and report it as
unverified. **"We could not read this page" is not "this employer has no openings."**
Reporting the second when the first is true is the failure mode that quietly removes an
employer from someone's job search.

**Deduplicate** across sources by URL first, then by (company, role, location). The same
posting routinely appears on two boards and the employer's own site; the employer's own
listing wins as the canonical source.

## Step 4: Validate that each job is actually open

Before ranking, check the best available signals: does the posting still fetch, does it
carry closure text ("no longer accepting applications"), has its stated closing date
passed, has the listing been removed?

- Confirmed open → rank normally.
- Confirmed closed → drop it, and record it in the shortlist as `not-resolved` with the
  reason, so the same dead posting is not re-surfaced next run.
- Cannot tell → mark `unverified` and say so. Never present an unverified posting as
  confidently open.

## Step 5: Hard constraints, then rank

**The hard-constraint gate runs before scoring, not after.** Read `preferences.yaml`:
`exclusions`, `hard_skips`, location and commute limits, work authorization. A posting
that breaks one is never drafted and never ranked — it is recorded with verdict
`gate-fail` and **the posting's own wording quoted**.

The `mandatory_only` rule, again because it is the one most easily got wrong: a hard-skip
skill listed under "preferred" or "nice to have" **does not** trigger the skip. Only a
stated requirement does.

Then rank what remains on qualifications, actual responsibilities, transferable skills,
compensation, location, remote arrangement, stated preferences, missing mandatories and
job status. ATS keyword counting is never the primary signal.

## Step 6: Record the run

Write a shortlist row per scored candidate to `shortlist.csv`
(`date,company,role,location,source,url,score,verdict,rationale`), with verdict from:

| Verdict | Meaning |
|---|---|
| `qualified` | Gates passed, worth an application |
| `not-drafted` | Gates passed but a stated requirement is unmet |
| `not-resolved` | Title-level triage only, or the posting could not be confirmed |
| `gate-fail` | Failed a hard constraint — do not revisit |

These are the shortlist's vocabulary. Upstream `/rank` scores the same jobs on its own
five-band scale, so the two are mapped here rather than left to look like disagreement:

| `/rank` band | score | shortlist verdict |
|---|---|---|
| Strong Fit | 75+ | `qualified` |
| Good Fit | 60–74 | `qualified` if drafted, else `not-drafted` |
| Moderate Fit | 45–59 | `not-drafted` |
| Weak / Poor Fit | below 45 | `not-drafted` |
| any band | — | `gate-fail` overrides everything: a hard constraint failed |

Log the run, including runs that found nothing:

```
python harness/run_log.py --portal <source> --query "<query>" --found N --new M \
    --notes "<anything unverified>"
```

A search that returned zero results is a fact worth keeping: a board that has gone quiet
for a fortnight looks identical to a board whose CLI broke, unless the log shows the runs
happened.

Then regenerate the workbook: `python harness/tracker_xlsx.py`.

## Step 7: Present

```
Searched: <scope> — N sources, M postings seen, K new
Ranked:   <top candidates with score, company, role, location, one-line rationale>
Gated out: <company/role — the posting's own words that failed the constraint>
Unverified: <anything that could not be confirmed, and why>
Run log: <portal> N found / M new
```

Then stop. In `focused` and `balanced` modes nothing is drafted until the user picks a
job; in `full` mode, packages are generated only above the threshold and only up to the
cap, and each one goes through `/apply-any` in full — including the fact gate.
