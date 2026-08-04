# /fact - Record a Confirmed Career Fact

You are recording something the user has stated or confirmed about their own career, so
that it becomes claimable evidence instead of a sentence in a chat log.

```
/fact the inventory migration covered about 1,400 records
/fact the data analytics certificate was completed in March
/fact move SQL from ai-assisted to direct - I write those queries myself
```

This is the **only** sanctioned way a new fact enters `evidence/register.yaml`.
(`/setup` is the other writer, and it only runs during onboarding.)

---

## Step 1: Understand what kind of fact it is

Route it to the right register section: `employers` · `education` · `credentials` ·
`technologies` · `technology_claim_rules` · `metrics` · `projects` ·
`public_repositories` · `research` · `leadership` · `languages` · `responsibilities` ·
`positioning_constraints`.

**If the statement is ambiguous, ask — do not guess.** The distinctions that matter
most, because each is the difference between a defensible claim and one that collapses
in an interview:

- *led* vs *supported*
- *completed* vs *in progress*
- an exact figure vs an approximation
- hands-on use vs AI-assisted use of a technology

Never ask about something the register already answers.

## Step 2: Check it does not contradict what is already there

Search the register for the same subject.

- **New fact** → add it.
- **Correction of an existing entry** → edit that entry in place. Keep the original
  `source` and append the correction:
  `source: <original>; corrected owner-confirmed <date>`.
- **Contradiction of a document-sourced fact** → say so plainly, quote both versions,
  and ask which is right before writing anything.

Never delete an entry to resolve a conflict. Correct it, and keep the trail.

## Step 3: Write it to the register

Back up first: copy `evidence/register.yaml` into `evidence/backups/`, keeping the five
most recent. Then add the entry. **Every entry carries a `source`.** For a fact the user
states themselves:

```yaml
  - value: "1,400"
    claim: "records covered by the inventory migration"
    qualifier_required: about
    source: owner-confirmed 2026-08-04
```

Rules that are easy to get wrong:

- `qualifier_required` whenever they said "about", "roughly", "more than", "nearly".
  The qualifier then becomes mandatory in every rendering.
- `aliases` for any other way the fact will legitimately be written
  ("1,400 records", "~1400").
- In-progress credentials need `status: in-progress` **and** `qualifier_required`.
  Without both, the credential can render as earned.
- A project that is not finished needs `status: in-progress` and a `claim_ceiling`.
- If the fact touches a declared `positioning_constraint`, record the fact and its claim
  ceiling together. A fact recorded without its ceiling is a fact that will be
  overclaimed later.

## Step 4: Mirror it into the profile

Add the same fact to the candidate-profile file that `/apply`'s grounding audit reads.
This matters mechanically: the drafter reads the profile, not the register, so a fact
recorded only in the register is invisible to it. If the fact *corrects* something
already in the profile, fix it there too rather than leaving two sources disagreeing.

## Step 5: Re-validate

Both, every time:

```
python -m unittest tests_harness.test_fact_check
```

and a parse check that the register still loads and every entry still carries a source:

```
python -c "import yaml,io; d=yaml.safe_load(io.open('evidence/register.yaml',encoding='utf-8').read()); print('register parses, %d top-level sections' % len(d))"
```

If a fixture now fails, **the fixture is usually right and the edit is wrong** — a fact
that makes a planted fabrication pass is a fact recorded too loosely. Tighten it.

## Step 6: Confirm back

```
Recorded: <the fact, as written>
  register: evidence/register.yaml -> <section>
  profile:  <profile file> -> <section>
  source:   owner-confirmed <date>
  fixtures: PASS
```

If the new fact resolves a red line that was blocking an application package, say so and
re-run `/verify-facts` on that package.

## Never

- Never add a fact the user did not state or confirm.
- Never edit the register to make a `/verify-facts` red line disappear. That is
  backwards: the red line means the draft claims something unevidenced. Either the user
  confirms it is true — in which case `/fact` is the right route and this command is
  already what you are doing — or the draft is wrong and the draft is what changes.
