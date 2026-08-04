# /verify-facts - Tier-1 Fact Check

You are running the deterministic immutable-facts check over a finished application
package. This is Tier 1 of the harness's two-tier truth model. It runs **after** the
drafter, the reviewer and the compile-and-inspect loop, and **before** the package is
shown to the user.

`evidence/register.yaml` is the authority. A claim that is not in the register is not
claimable.

---

## When this runs

- **Automatically**, as the last step of `/apply` and `/apply-any`, before the summary
  is presented. It is not optional and it is not skipped for a rush.
- **Again, after any humanization pass.** Stylistic rewriting can strengthen a claim
  past its evidence — "supported the migration" becomes "led the migration" and no
  human notices. Any wording change means recompile, then re-run this check.
- **On demand**, whenever the user asks to check a document.

## Step 1: Collect the inputs

- The final CV: `cv/main_<company>_<role>.tex`
- The final cover letter: `cover_letters/cover_<company>_<role>.tex`
- The archived posting, if one exists:
  `documents/applications/<Company>_<Role>/job_posting.md`

If a compiled PDF exists and `pdftotext` is available, check the extracted text layer
too — that is what an ATS actually reads, and it is not always what the `.tex` says:

```
pdftotext -layout cv/main_<company>_<role>.pdf cv/main_<company>_<role>.txt
```

## Step 2: Run the checker

```
python harness/fact_check.py <cv.tex> <cover_letter.tex> [<extracted.txt>] --posting <job_posting.md>
```

Pass `--posting` whenever an archived posting exists. Numbers that appear in the
posting (salary, requisition ID, a team size quoted back to the employer) are
legitimate; without the flag they are reported as unsupported.

Exit code is the number of red lines. `0` means OK.

## Step 3: Act on the result

**Exit 0** — print the `OK` line and continue to the presentation step.

**Non-zero** — **the package is blocked.** Do not present it. For each red line,
exactly one of three things is true:

| Situation | Correct resolution |
|---|---|
| The draft overstates, invents, or drops a required qualifier | **Fix the draft**, then re-run. |
| The claim is genuinely true and the register is simply missing it | Ask the user to confirm it, record it with `/fact` (which writes it with an `owner-confirmed <date>` source), then re-run. |
| The checker is wrong about a whole class of text | Fix `harness/fact_check.py` **and** add a fixture to `tests_harness/` pinning the corrected behaviour, so the defect cannot return. |

**Never** edit `evidence/register.yaml` by hand to make a red line disappear. Never
weaken a pattern in `fact_check.py` or its config to let one draft through. Never
present a package "with a note about the red lines". A red line is a blocker, not a
caveat.

The distinction that matters in the third row: fixing a checker defect means the
checker was wrong about *every* document of that shape. If the fix only helps the
document in front of you, it is not a fix — it is the second row wearing a disguise.

## Step 4: Report

Append a short pass/fail block to the application summary:

```
### Tier-1 fact check
python harness/fact_check.py ... -> OK (N files checked, 0 red lines)
```

or, when blocked:

```
### Tier-1 fact check - BLOCKED (N red lines)
 1. FABRICATION-RISK: "<text>" - <reason>  [<file>]
 ...
Resolution taken: <draft corrected | fact confirmed and registered | checker corrected>
Re-run: OK
```

## What this check does and does not cover

**Covers (Tier 1, mechanical):** numerals with units against registered metrics · date
ranges against registered employment, education and project spans · in-progress
credentials rendering without their required qualifier · credential names absent from
the register · technologies absent from the register (posting keywords leaking into the
draft) · the machine-checkable forms of whichever positioning constraints the user's own
register declares.

**Does not cover (Tier 2, the reviewer pass's job):** whether a reframing is persuasive,
whether "led" is fair where the evidence says "supported", whether a company-enthusiasm
claim is researched, whether a gap is handled honestly. A clean Tier-1 run is necessary,
not sufficient.

**Stated ceilings** — these are limits, not excuses, and each has a test pinning it:

- The unregistered-technology check works from a lexicon, so it cannot flag a technology
  nobody listed. Broaden `tech_lexicon` in `harness/fact_check_config.yaml` when a real
  draft slips one through, and add a fixture.
- The numeral check fires only for units in `NUMERAL_RE`. A claim carrying an unlisted
  unit passes Tier 1 and is left to the reviewer.
- The checker cannot tell "I have not used X" from "I used X". Honest-gap sentences are
  reworded rather than the guard loosened.

## Self-test

The checker's own fixtures live in `tests_harness/` (never in upstream's `tests/`):

```
python -m unittest tests_harness.test_fact_check
```

`fixture_bad.txt` must be caught with every planted class named; `fixture_clean.txt`
must pass with exit 0. Run this after any change to the checker, its config, or the
register.
