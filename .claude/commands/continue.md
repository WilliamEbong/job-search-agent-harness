# /continue - Resume Work From the Handoff

You are picking up work that stopped — because a session ended, a context window filled,
a subscription window ran out, or the user simply came back the next day. Possibly in a
different runtime from the one that started it.

```
/continue
```

The promise this command makes: **nothing already done is done again, and nothing already
answered is asked again.**

---

## The bootstrap ritual, in this order

Order matters. Each step is a check on the one before it, and the filesystem outranks
every document.

### 1. Read the orientation file
`AGENTS.md` (both runtimes read it; Claude also reads `CLAUDE.md`). This tells you what
the project is and where things live.

### 2. Read `state/HANDOFF.md`
The durable record of what was happening. If it does not exist, say so plainly and fall
back to step 3 — an absent handoff means work stopped without a milestone, not that
nothing happened.

### 3. Verify against git and the filesystem
**Do not trust the handoff over reality.** It was written at the last milestone; work may
have continued after it. Check:

- `git status` and `git log --oneline -5` — what is committed, what is dirty?
- Does the application folder named in the handoff exist? What is in it?
- Do the drafts named in the handoff exist, and are they newer than the handoff?
- Has the tracker row already been written?

Where the handoff and the filesystem disagree, **the filesystem is right**. Say so, and
adjust the plan.

### 4. Resume at the exact next step
State what you are about to do in one line, then do it. Do not re-summarise the whole
task, do not re-derive decisions the handoff already records, and do not re-ask a
question whose answer is written down.

---

## Writing the handoff (the other half of the contract)

`/continue` only works if something wrote `state/HANDOFF.md`. Refresh it **at every
milestone**, not on a timer:

posting acquired · research done · positioning strategy settled · CV drafted · reviewer
pass done · humanizer pass done · fact gate passed · package archived · tracker updated.

Also append one line per milestone to `state/session-log.md` (append-only — it is the
audit trail of what happened when, and rewriting it destroys the only record).

`state/HANDOFF.md` holds, and is rewritten in full each time:

```markdown
# Handoff — <date/time>

## Objective          what we are trying to achieve
## User intent        what the user actually asked for, in their words
## Authoritative inputs   posting path, register, preferences, template
## Decisions made     with the reason for each
## Session-confirmed facts   anything the user confirmed that is NOT yet in the register
## Work done          completed steps
## Work underway      the step in flight, and how far it got
## Files touched      paths, and what changed in each
## Verification state compile? page counts? ATS? fact gate? — with results
## Unresolved         open questions, blockers, things to ask
## Task list          remaining steps in order
## EXACT NEXT STEP    one sentence, actionable without re-reading anything
## Do not redo        things that are finished and must not be repeated
## Git state          branch, last commit, dirty files
```

Two rules about its content:

- **Durable context only.** No chain-of-thought, no transcript. A handoff is what a
  competent stranger needs, not a diary.
- **"Session-confirmed facts" is a holding pen, not a truth store.** A fact the user
  confirmed in conversation belongs in the register via `/fact`. Until it is there it is
  not claimable, and the handoff says so explicitly so the next session does not treat it
  as evidence.

---

## When to refresh, per runtime

**Claude Code** — `harness/telemetry_statusline.py` mirrors usage into
`state/telemetry.json` if it is registered as the statusline. Read it at milestones:

| Signal | Action |
|---|---|
| context ≥ 80% | Refresh the handoff now. |
| context ≥ 90% | Refresh, then advise finishing the sub-step and starting a fresh session. |
| five-hour or seven-day ≥ 90% | Refresh, and offer to continue in the other runtime. |

Treat those numbers with the caveats the file itself carries: the context percentage
counts input tokens only, is null before the first call, and resets after `/compact`. A
low number is not proof of a fresh start.

If `state/telemetry.json` is absent, that is the normal state for a user who never
registered the statusline — degrade to milestone cadence without comment.

**Codex** — no programmatic usage signal exists. Use milestone cadence plus a
conservative turn-count heuristic (roughly every ten turns). **Never print a percentage
on Codex.** A fabricated number is worse than no number, because the user will plan
around it.

---

## Cross-runtime continuation

The same ritual works in either runtime; the state files are runtime-neutral by design.

Set the expectation honestly when handing over: **the state carries fully, the
conversation does not.** Decisions, files, verification results and the next step all
survive. The feel of the discussion — what was tried and rejected, the user's tone about
a particular employer — does not. If something like that matters, it belongs in
"Decisions made" with its reason, where it becomes durable.

---

## Report

```
Resumed from state/HANDOFF.md (written <when>).
  Verified against: git (<last commit>), <files checked>
  Discrepancies:    <handoff said X, filesystem shows Y — or "none">
  Not redoing:      <list>
  Next step:        <the one sentence>
```

Then do it.
