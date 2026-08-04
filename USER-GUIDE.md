# User Guide

Everything this system does, and how to use it. Read the README first for what it is and
why; this is the manual.

**Contents**
[Install](#install) · [Onboarding](#onboarding) · [Career review](#career-review) ·
[Companies of interest](#companies-of-interest) · [Finding jobs](#finding-jobs) ·
[Applying](#applying) · [Truth checking](#truth-checking) · [Tracking](#tracking) ·
[Interviews](#interviews) · [Continuity](#continuity) · [Both runtimes](#both-runtimes) ·
[Command reference](#command-reference) · [When something goes wrong](#when-something-goes-wrong)

---

## Install

```bash
git clone https://github.com/<you>/job-search-agent-harness
cd job-search-agent-harness
python setup.py
```

Setup finishes with a doctor table. Read it — it is written to be honest rather than
green:

| Status | Meaning |
|---|---|
| `OK` | Present and verified working. TeX is verified by *compiling a document*, not by `--version`. |
| `MISSING` | Not installed. The fix is printed. |
| `DEGRADED` | **Installed but broken.** The dangerous one. Bun on a CPU without AVX2 installs perfectly and crashes on every call. |
| `RESTART SHELL` | Installed, but your open terminal has a stale PATH. Close it and reopen. |
| `UNVERIFIED` | Could not be confirmed either way — never silently treated as OK. |
| `OPTIONAL` | Declined or not needed. |

Flags: `--doctor` (check only, change nothing), `--yes` (accept recommended defaults),
`--quick` (skip the test compiles — faster, less proof).

**Optional extras setup offers.** Ponytail (recommended). Caveman — optional, explained at
the prompt, `lite` mode recommended; it only ever touches the agent's internal chatter,
never your applications. Playwright and Firecrawl MCP — let posting intake read
JavaScript-heavy and bot-walled pages; without them such pages are marked `unverified`
rather than guessed at.

---

## Onboarding

```
/setup-harness
/setup-harness --interview     # resume or extend the interview later
```

**It starts with your CV.** Give it the most complete version you have, not one trimmed
for a particular job. It reads it and summarises what it found; correct anything wrong
before continuing, because a misread date propagates into every application afterwards.

**Then it interviews you** about what the CV left out — and tells you how to control that
interview before it starts:

- **"speed up"** → only the questions that change what you may claim.
- **"that's enough"** → stops immediately, keeps everything gathered so far.
- **`/setup-harness --interview`** → picks up later, never re-asking an answered question.

It asks about numbers, whether credentials are finished, exact date ranges, whether you
*led* or *supported*, and — the one that prevents the most trouble — whether you used a
technology hands-on, with AI assistance, or barely at all.

**What it builds.** `evidence/register.yaml`, the answer to "what may this person claim?".
Every entry carries a `source:` — a document path, or `owner-confirmed <date>` for
something you said. An entry with no source is a rumour, and the system will not treat it
as evidence.

**Then preferences** — pay, location, commute, remote trade-offs, exclusions, and skills
you would rather not see jobs requiring. Two defaults worth knowing:

- Postings with **no stated salary are kept**, not discarded. Most postings state nothing;
  discarding them throws away most of the market.
- A skill you listed as a hard skip only blocks a job when the posting makes it a
  **requirement**. Listed under "nice to have", it does not block anything.

**Then a template**: the stock one, one inferred from a previous résumé of yours (it
reconstructs the structure — sections, spacing, bullet style, length — and test-compiles
it; it is not a pixel-perfect clone, and it is shown to you before it is used), or one you
supply.

> **The rule of separation.** A résumé used as a template contributes *structure only*.
> Its facts do not enter the register and do not become claimable.

---

## Career review

```
/career-review
/career-review https://github.com/you https://you.example.com
```

Looks at what a hiring manager would find, and reports it — including the parts you might
not want to hear: the abandoned repository pinned to your profile, the personal site whose
contact form is broken, the fork with no commits of yours. Most valuably, the strong thing
you have done that never made it onto your CV.

Output is grouped into what to add, what to reword, and what to fix in your public
presence. **It only suggests.** A new fact goes in only when you confirm it, and then it
goes through `/fact` so it arrives with a source. Rewordings touch templates only.

---

## Companies of interest

```
/companies                          # review, add, remove
/companies add Acme Environmental
/companies research                 # propose employers from your CV and location
/companies remove Acme Environmental
```

Job boards only find jobs that were advertised on job boards. Plenty of employers —
public-sector bodies, small consultancies, many local firms — post only to their own
careers page, sometimes days earlier, sometimes exclusively.

Entries come from you, or from research you approve: large employers in your field, plus
local ones hiring your skill set. Every careers URL is checked to load before it is
recorded, because a dead URL later produces an empty run that looks exactly like "no
openings".

**It is a living list.** Add or remove whenever; the next scoped run reflects it
immediately. There is no re-onboarding.

---

## Finding jobs

```
/scrape                                    # your defaults
/scrape --mode focused --board freehire
/scrape --scope companies
/scrape --scope company "Prairie Grid Utilities"
/scrape --scope boards --mode balanced
/scrape --scope all --mode full --limit 40
```

**Five scopes:** one named board · one named company · all your companies · all your
boards · everything.

**Three modes:**

| Mode | What it does | Documents generated |
|---|---|---|
| `focused` | One source, shallow screen. Default for new users. | None until you pick a job |
| `balanced` | All sources in scope, deduplicated and ranked; deeper look at promising ones | Only on selection |
| `full` | Deep evaluation and research | Automatic, above your threshold, up to a cap |

**Every run tells you the cost first** — how many sources, which mode, what the caps are,
and whether it is heavy. It will not invent token arithmetic; a precise-looking number
nobody can verify is worse than an honest description.

**Before ranking**, hard constraints are checked and each job is validated as actually
open. A job that fails a constraint is never drafted, and the refusal quotes *the
posting's own words* so you can check it yourself. A posting that cannot be confirmed open
is marked `unverified` — which means "we don't know", not "it's closed".

---

## Applying

```
apply <url>
/apply-any                # with screenshots or a PDF attached
/apply-any                # with the posting pasted in
```

Works from a link, screenshots, a PDF, pasted text, or several at once. It resolves them
into one posting, prefers the employer's own listing when sources disagree, records every
conflict rather than silently picking one, and archives the raw artifacts alongside a
provenance note.

Then: fit evaluation → drafting → a reviewer pass with fresh context → revision →
humanizing → **recompile and re-check the facts** → page-count and ATS checks → archive →
tracker row.

**You get four formats** of each document — `.tex`, `.pdf`, `.md`, `.docx` — plus a
combined cover-letter-then-resume file, named so they make sense in a file picker. The
`.md` is generated from the `.tex`, never written by hand, so the two cannot drift.

**Nothing is submitted.** You send it, then tell the system you did.

---

## Truth checking

```
/verify-facts <files>
/fact <something true about you>
```

`/verify-facts` runs automatically before any package is shown to you, and again after any
wording change. It checks numbers, date ranges, credentials (including that an in-progress
one never renders as finished), technologies, and any positioning rules you set.

**If it finds something, the package is blocked.** There are exactly three legitimate
resolutions:

1. The draft overstated something → **fix the draft**.
2. The claim is true and simply not recorded → confirm it, and `/fact` records it with a
   source.
3. The checker is wrong about a whole *class* of text → fix the checker and add a test
   pinning the correction.

Editing the register to make a red line disappear is not on that list, and neither is
shipping the package "with a note". A red line is a blocker, not a caveat.

**What it does not do:** judge whether your phrasing is persuasive, or whether "led" is
fair where the evidence says "supported". That is the reviewer's job. A clean run is
necessary, not sufficient.

---

## Tracking

```
/tracker
/tracker --dry-run
/outcome <what happened>
```

`job_search_tracker.csv` is the truth. `Job_Search_Tracker.xlsx` is a view with four tabs
— Applications, Summary (your funnel and response rates), Shortlist (jobs that did *not*
become applications, and why), and Search Runs.

**The workbook is never read back.** That is what makes it safe to regenerate whenever you
like: it can never hold the only copy of a note. So editing a status in Excel does
nothing — say "rejected by Acme" instead, and `/outcome` records it.

Tell it you applied and the folder moves itself to `applied/` on the next run. After eight
weeks, applications zip themselves into `archive/`.

---

## Interviews

```
/interview <company>
```

Builds a preparation pack from the posting and **the exact documents you actually
submitted** — which is why the archive matters. Postings disappear; the archived copy is
the only remaining record of what you applied to.

---

## Continuity

```
/continue
```

Work is saved at every milestone into `state/HANDOFF.md` and `state/session-log.md`.
`/continue` reads the handoff, **verifies it against git and the filesystem** — reality
wins where they disagree — and resumes at the exact next step, redoing nothing.

On Claude Code, if you let setup register the statusline, it also watches how full the
context window is and suggests handing off before you run out. On Codex no such signal
exists, so it uses milestones instead and never prints a percentage it cannot measure.

---

## Both runtimes

Everything above works in Claude Code and in Codex. In Codex, invoke a workflow with `@`
or paste the matching stub from `.codex/prompts/`.

[RUNTIME-MAP.md](RUNTIME-MAP.md) lists every difference. There are few, and they are
mechanical: Codex has no subagent tool, so the reviewer runs as a sequential fresh pass;
tool names differ; usage telemetry exists only on Claude.

**Switching mid-task works.** `/continue` in the other runtime picks up from the same
state files. Set your expectations honestly: the state carries fully, the conversation
does not. Decisions, files and the next step survive; the feel of the discussion does not.

---

## Command reference

| Command | Does |
|---|---|
| `/setup-harness` | Onboarding: CV, interview, register, preferences, template |
| `/setup-harness --interview` | Resume or extend the interview |
| `/career-review` | Review public presence, suggest CV improvements |
| `/companies` | Manage the companies-of-interest list |
| `/scrape` | Find jobs (five scopes, three modes) |
| `/apply-any` | Apply from any input form |
| `/verify-facts` | Run the truth gate on a package |
| `/fact` | Record a confirmed career fact |
| `/tracker` | Regenerate the workbook, run the archiver |
| `/outcome` | Record what happened to an application |
| `/interview` | Build an interview prep pack |
| `/continue` | Resume interrupted work |
| `/rank`, `/add-portal`, `/add-template`, `/expand`, `/html-report` | Upstream commands, unchanged |

---

## When something goes wrong

| Symptom | What it means |
|---|---|
| Doctor says `DEGRADED` | Installed but broken. Bun is the usual case — on a CPU without AVX2, install `Oven-sh.Bun.Baseline`. |
| Doctor says `RESTART SHELL` | Real; your terminal has a stale PATH. Reopen it. |
| A CV will not compile | See [docs/latex-gotchas.md](docs/latex-gotchas.md). Compile from the template's own directory — `cover.cls` resolves its fonts relative to the working directory. |
| A search returns nothing | Check `run_log.csv`. A board whose CLI broke looks exactly like a quiet market unless the log shows the runs happened. See [docs/board-intelligence.md](docs/board-intelligence.md). |
| A posting says `unverified` | It could not be confirmed live. That is "we don't know", not "it's closed". |
| The fact gate blocks a package | Read the red lines. Fix the draft, or confirm the fact with `/fact`. Do not edit the register to silence it. |
| A session ended mid-task | `/continue`. |
