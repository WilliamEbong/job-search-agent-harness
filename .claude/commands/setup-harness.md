# /setup-harness - Guided Onboarding (CV first, then everything else)

You are onboarding a new user. By the end they have an evidence register that decides
what may be claimed, a preference profile that decides which jobs are worth their
attention, a CV template they are happy with, and — if they want it — a list of
employers worth watching directly.

This command **wraps** upstream's `/setup`; it does not replace it. Upstream owns
building the profile files. This command owns the order things happen in, the interview
controls, the evidence register, and the three additions upstream has no concept of:
career review, companies of interest, and the preference profile.

```
/setup-harness              # full onboarding
/setup-harness --interview  # resume or extend the CV interview, nothing else
```

**Never re-ask a question the documents or a previous session already answered.** That
rule outranks completeness everywhere below. A user who is asked their job title twice
stops trusting the system with anything.

---

## Step 0: Offer a short path and a thorough one

Say what is about to happen, then let them choose — with the time cost stated, because
"onboarding" with no end in sight is where people give up:

> Two ways to do this:
>
> **Quick start (about 5 minutes)** — I read your CV, ask a handful of questions about
> the things a CV leaves out, and you can start searching. I'll ask about pay, location
> and dealbreakers the first time you search, when they actually matter.
>
> **Full setup (15–20 minutes)** — the above plus preferences, a look at your public
> work, a template choice, and a list of employers to watch.
>
> You can switch to the full version any time with `/setup-harness --interview`.

**Quick start** runs Steps 1–3 only, then stops and says what was skipped and how to add
it later. Everything skipped keeps a documented default (`focused` mode, boards scope,
keep postings with no stated salary). The first `/scrape` then asks only the three
questions it genuinely needs — location, role families, and anything they refuse
outright — and writes them to `preferences.yaml`.

**Full setup** runs every step below.

Either way, check what already exists first:

- `evidence/register.yaml` — if present, this is a returning user. Read it. Everything
  in it is answered; do not ask again.
- `preferences.yaml` — same.
- `documents/` — inventory it before asking for anything.

If `--interview` was passed, skip to Step 2 and resume the CV interview only.

## Step 1: CV first

The CV is the richest single source a user has, so it comes before every question.

Ask for it plainly: *"Start by pointing me at your CV or résumé — the most complete
version you have, not a trimmed one for a specific job. Drop it in `documents/` or give
me the path."*

Accept `.pdf`, `.docx`, `.md`, `.tex` or pasted text. Read it and produce a short,
concrete summary of what you found — employers, dates, education, credentials,
technologies, numbers. Ask them to correct anything wrong before you go further. A
misread date propagates into every application afterwards.

## Step 2: Interview them on the CV

A CV is a summary; the register needs what the summary left out. Interview them to fill
the gaps you actually found — never a fixed list of questions.

**Open the interview by telling them how to control it.** This is a feature of the
command, not a line in the manual, and it must be said every time:

> Before we start: this is a conversation, not a form. Say **"speed up"** at any point
> and I'll switch to only the highest-value questions. Say **"that's enough"** and I'll
> stop immediately and keep everything gathered so far. You can pick this up later with
> `/setup-harness --interview` — I won't re-ask anything you've already answered.

Honour both, immediately and without argument:

- **"speed up"** (or "faster", "fewer questions", "keep it short") → drop to the
  questions whose answers change what may be claimed: unregistered metrics, credential
  status, ambiguous date ranges, and any technology whose claim level is unclear. Skip
  everything decorative. Acknowledge the change in one line.
- **"that's enough"** (or "stop", "done", "that's plenty") → stop asking *that turn*.
  Write everything gathered so far to the register. Tell them exactly what is recorded
  and what is still blank, and how to resume. Never discard collected answers because
  the interview ended early.

What to probe, in priority order — this is a checklist for *you*, not a script:

1. **Numbers.** Every figure the CV states, plus the ones it implies ("managed a large
   inventory" — how large?). Each becomes a `metrics` entry or is not claimable.
2. **Credential status.** Completed or in progress? An in-progress credential gets
   `status: in-progress` and a `qualifier_required`, and can then never render as earned.
3. **Date ranges.** Exact start and end months. Gaps are noted, not interrogated.
4. **Technology claim levels.** For each technology: hands-on, AI-assisted, or
   familiarity only? This is the single most common source of an overclaim, because a
   CV lists tools without saying what the person actually did with them.
5. **Led vs supported.** For anything that sounds like leadership.
6. **Positioning constraints.** Anything they do *not* want to be presented as. Record
   as a `positioning_constraints` entry with an `id`; if a machine-checkable pattern
   family exists for that id in `harness/fact_check_config.yaml`, it activates
   automatically.

## Step 3: Build the register

Write `evidence/register.yaml` following the schema and section order in
`evidence/register.example.yaml`.

**Every entry carries a `source:`** — a document path for anything read from a file,
`owner-confirmed <YYYY-MM-DD>` for anything they told you. An entry without a source is
a rumour. Verify before moving on:

```
python -c "import yaml,io; d=yaml.safe_load(io.open('evidence/register.yaml',encoding='utf-8').read()); print('%d sections' % len(d))"
python -m unittest tests_harness.test_fact_check
```

Then hand the profile-file work to upstream `/setup` (Path A if documents exist, Path B
for a single CV). Upstream owns those files; do not write them yourself.

**Do not let it start over.** `/setup` opens with its own welcome and a three-path menu,
and its interview mode re-asks identity, education, experience, skills and salary — all
of which are already answered above. Tell it, in your own framing, to skip the welcome
and the path menu, and to skip every question the register already answers. A user who
is asked their job title twice stops trusting the system with anything, and this is the
one place in the flow where that nearly happens.

**The rule of separation, which matters most at the next step:** career evidence decides
what may be claimed; templates decide how claims are presented. Facts never enter the
register from a template.

## Step 4: Career review (offer, don't impose)

Offer once: *"Want me to look at your portfolio, personal site or GitHub and suggest CV
improvements? I'll only suggest — nothing gets added without your say-so."*

If yes, run `/career-review`. If no, move on and do not offer again this session.

## Step 5: Preference interview

Now the questions that decide which jobs are worth their attention. Conversational and
conditional — **skip anything the documents or the register already answer**, and skip
whole branches that do not apply (do not ask a remote data analyst about a driving
licence).

Cover, in `examples/preferences.example.yaml`'s shape:

- **Compensation** — minimum, target, currency, salary or hourly, and what would make
  them flex. Postings that state no compensation are **kept** by default; only discard
  them if the user says so outright.
- **Location** — home, commute radius, remote/hybrid/onsite preference, relocation and
  where to.
- **Driving** — only if plausibly relevant. Licence, vehicle, willingness, and whether
  to exclude licence-requiring jobs outright.
- **Exclusions** — ask openly: *"What jobs would you not take?"* Take the free
  description and structure it into occupations, industries, schedules, shifts, travel,
  physical demands, commission-only, management-required, customer-facing, contract type.
- **Remote trade-offs** — *"Would you trade anything for fully remote work?"* and if so,
  exactly what. **Ask, never assume.** Quietly deciding someone will take less money for
  remote work fills their shortlist with jobs they resent.
- **Hard skill-skips** — *"Any skills or credentials you clearly don't have, where you'd
  rather not see the job at all?"* Record each with `mandatory_only: true` unless they
  say otherwise. This field carries real weight: a posting listing the skill as
  *preferred* must NOT be skipped, or transferable-fit candidates lose jobs they would
  have got.
- **Role families, seniority, employment type, work authorization, industries,
  direction.**
- **CV length** — *"How long should your CV be?"* Options: 1 page, 2 pages, another
  number, or *adaptive* (the drafter picks 1 or 2 per posting and says why). Default 2 if
  they have no opinion. Record as `presentation.cv_pages`. Changeable later without
  redoing onboarding — a one-line edit to `preferences.yaml` or a re-run of this step.
- **Usage mode** — explain the three modes in terms of cost and control, and default new
  users to `focused`.

Write `preferences.yaml`. Read the whole thing back in plain language and let them
correct it.

## Step 6: Template choice

Three options; describe all three and let them choose:

1. **Stock** — upstream's moderncv CV and cover-letter templates. Nothing to do.
2. **A previous résumé as the template.** Run the bounded inference step: reconstruct a
   *maintainable* LaTeX structure from their file — sections, hierarchy, spacing, bullet
   style, length — then hand it to upstream `/add-template`, which registers it and
   test-compiles it. **Say plainly what this does not promise: it is not a pixel-perfect
   clone.** Show the compiled PDF and let them accept or fall back to stock.
   **Facts from that résumé do not enter the register.** It contributes structure only.
3. **A template they supply** — straight to `/add-template`.

## Step 7: Companies of interest (offer, once the CV is settled)

Offer: *"Want me to start a list of employers worth watching directly? Job boards miss
employers who only post on their own careers page."*

If yes, run `/companies`. Mention it is a living list they can change any time.

## Step 8: Confirm and hand over

Report what exists now, in plain language:

```
Onboarding complete.
  evidence/register.yaml   — N facts across M sections, every one sourced
  preferences.yaml         — mode: focused, N hard constraints recorded
  companies.yaml           — N employers (or: not started)
  template                 — stock (or: inferred from your résumé, compiled and checked)

Next: /scrape to find jobs, or `apply <a posting>` if you already have one.
Anything wrong? `/fact <correction>` fixes a career fact; `/setup-harness --interview`
resumes the interview.
```

## Never

- Never write a fact into the register that the user did not state or that is not in a
  document, and never without a `source`.
- Never let a résumé used as a template contribute facts.
- Never ask a question the register, preferences, or documents already answer.
- Never continue interviewing after "that's enough" — and never discard what was already
  gathered because the interview ended early.
- Never assume a remote trade-off.
