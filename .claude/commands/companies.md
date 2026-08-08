# /companies - Manage the Companies-of-Interest List

You are maintaining `companies.yaml`: the employers worth checking directly, rather than
waiting for a job board to surface them.

```
/companies                          # review the list, add, remove
/companies add Acme Environmental   # add a specific employer
/companies research                 # propose new employers from the CV and location
/companies remove Acme Environmental
```

**This is a living list.** Onboarding is only the first run. Employers get added and
removed as the search evolves, and the next `/scrape --scope companies` reflects the
change immediately — there is no re-onboarding step and nothing is frozen at setup time.

Why the list exists: boards find jobs that were advertised on boards. Public-sector
bodies, small consultancies and many local employers post only to their own careers
page, sometimes days earlier, sometimes exclusively.

---

## Step 0: Check they are set up

Run the standing first-run check ("Before any harness workflow runs" in `AGENTS.md` /
`CLAUDE.md`): no `evidence/register.yaml` or `preferences.yaml` means offer
`/setup-harness` in one line and stop. Never read the shipped `.example.yaml` as though
it were the user's.

## Step 1: Show what is there

Read `companies.yaml` (schema in `examples/companies.example.yaml`). Show the current list
compactly — name, scope, where it came from, and any access problem recorded by the last
scrape run. If the file does not exist yet, say so and go to Step 2.

## Step 2: Ask for their own names first

*"Which employers would you like to keep an eye on? Anywhere you'd take a job if the
right role opened."*

These are recorded with `source: user`. They need no justification — a user naming an
employer is the strongest possible signal.

For each, find the careers page and **verify it loads and lists jobs** before recording
it. A `careers_url` that 404s produces a silent zero-results run later, which reads
exactly like "no openings" and is a much worse failure than an error at entry time.

## Step 3: Research proposals

Offer to propose more, drawn from two directions — both grounded in the register and
`preferences.yaml`, never generic:

1. **Large employers in their field** — the recognisable names that hire this skill set,
   whether or not they are nearby.
2. **Local and regional employers** — organisations within their stated location and
   commute radius that hire this skill set. This is the half that matters most, because
   these are the employers least likely to appear on a national board.

Use web search, escalating to Firecrawl or Playwright per `RUNTIME-MAP.md` when a page
resists a plain fetch. No custom scrapers.

Present proposals as a numbered list, each with a reason tied to their actual profile
and a working careers URL:

```
Proposed employers — say which to add (numbers, "all", or "none"):

1. Continental Environmental Group — national
   Hires water quality analysts across Canada; several roles listed remote.
   Careers: https://... (verified, 40+ open roles)

2. Lakeshore Municipal Water Authority — regional, 18 km from home
   Public-sector employer hiring this skill set; posts only to its own site,
   so the configured boards will never surface it.
   Careers: https://... (verified, 6 open roles)
```

**Every proposal needs the user's approval before it lands.** A proposal that is not
approved is not recorded — not as a rejected entry, not as a note. Approved entries get
`source: researched <YYYY-MM-DD>`.

Record what the research was based on under `meta.research_basis`, so a later run
proposes genuinely new names instead of repeating itself.

## Step 3b: Anyone they know there

For each employer, ask once whether they know anybody there — a former colleague, someone
from a conference, a friend of a friend. Record it under `contacts:` on that entry: a
name, how they know them, and one line of context.

This is a list, not a CRM, and that is deliberate. A referral is the highest-converting
channel in most job searches, and the system has always *measured* `channel: referral`
outcomes while offering nothing to help produce one. A name attached to an employer is
enough to close that gap: `/apply-any` surfaces it before drafting, so the user can ask
before applying cold rather than remembering afterwards.

Do not press. "No" is a complete answer and is not asked again for that employer.

## Step 4: Removals and edits

Removing is as ordinary as adding — say the name, it goes. Do not ask them to justify
it, and do not keep a tombstone.

Editing a `careers_url` is common and worth encouraging: employers move to new applicant
tracking systems constantly, and a stale URL degrades into silent empty runs.

## Step 5: Write and confirm

Write `companies.yaml`, preserving the schema. Then report:

```
companies.yaml updated — N employers
  added:   <names> (user: N, researched: N)
  removed: <names>
  changed: <names>

Next `/scrape --scope companies` checks all N.
Or check one now: /scrape --scope company "<name>"
```

## Access problems are recorded, never hidden

When a scrape run cannot read a careers page — JavaScript shell, bot wall, login
required — it sets `access: unverified` with a note on that entry. Surface those here so
the user can decide whether to keep the employer, and be exact about what is unknown:

> Boreal Water Sciences — last run couldn't read the listing (bot wall). Results from
> this employer are marked `unverified`. That means "we don't know", not "no openings" —
> the two get confused constantly and they are very different facts.

Never quietly drop an employer because its page is hard to read. Never report an
unreadable page as having no openings.

## Never

- Never add a researched proposal without explicit approval.
- Never record a careers URL that was not verified to load.
- Never treat an unreadable careers page as an empty one.
- Never let this list silently grow from postings the user merely applied to — an
  employer joins because they said so, or because they approved a proposal.
