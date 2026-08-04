# Review & Remediation — Handoff

**Written:** 2026-08-04 · **Repo state:** clean, pushed, CI green at `7136225`
**Repository:** https://github.com/WilliamEbong/job-search-agent-harness (public)

This picks up after a critical review of the completed Stage-3 build. Read this
file, then `## Outstanding work`. Everything above that line is context.

---

## 1. What happened before this session

The harness was built in Stage 3 (phases P0–P10, recorded in
`docs/build-history/BUILD-STATE.md`) and made public. The owner then asked for a
critical review — issues, inefficiencies, UI/workflow assessment against a real
job searcher's needs — plus a decluttering pass, and later added an explicit
"more ease-of-use" directive.

Three parallel review agents (UX/command surface, code quality, lifecycle gaps)
produced findings. **The highest-severity claims were verified by direct read or
live execution before any plan was built on them** — several agent claims were
adjusted or corrected in the process.

The resulting plan lives at
`~/.claude/plans/review-this-system-find-crystalline-island.md` and was approved
with three locked decisions:

1. **Scope: all four waves** (bugs → determinism → UX/declutter → new features).
2. **Upstream `[U]` files stay byte-identical.** Every fix is harness-side. No
   `[U]→[P]` promotions. This is why several fixes look indirect — see §4.
3. **Declutter:** build-history docs and example YAMLs move; generated data
   files stay at repo root (paths baked into 5 scripts, both guards, gitignore).

All four waves are **complete, committed and pushed**. CI green.

---

## 2. What was fixed (all four waves shipped)

### Wave 1 — data loss and silent corruption (`f1217d0`)

| Defect | Was | Now |
|---|---|---|
| `Path.with_suffix(".zip")` on dotted folder names | `Acme_Inc._Data_Analyst` checked `Acme_Inc.zip`, wrote the full name → collision counter never fired → **re-archive overwrote the previous zip after `rmtree`** | `_archive_stem()` builds the path by string concat; `with_suffix` is never used |
| Folder age | min mtime of *contents* → a `copy2`-preserved old CV made a new folder instantly "8 weeks old" → zipped and deleted | `.created` marker written by `apply_package.py`, falling back to folder ctime only |
| Archiver ran unattended and status-blind | deleted folders **mid-interview** from routine `/apply-any` and `/tracker` runs | skips open applications; archiving requires `--archive`; default only reports |
| `/outcome`-created tracker (13 cols, no `submitted_date`) | **applied/ move silently never fired, forever** | `tracker_row.append()` heals the header on first write |
| Status vocabulary split three ways | rows written as `applied` matched none of the workbook's six values → counted as neither Open nor Closed → **vanished from the funnel** | `harness/status.py` owns normalisation *and* classification |
| `privacy_sweep` allow-regex | `\btest\b\|\bexample\b` excused **every** match on the line → a real email in a "tested with…" line shipped | line context excuses only shape-based categories (addresses); contact categories need the marker inside the match |
| `privacy_sweep` exit code | uncapped → exactly 256 hits exits 0 | capped at 100 |
| fact_check: date spans | matched **any** registered span → "Acme Corp, 2015–2016" passed on a university course | entity-bound when a name is within ±200 chars |
| fact_check: open-ended ranges | "2015 – present" passed if any span merely *started* in 2015 | the containing span must itself be open |
| fact_check: `5+ years` | never matched a registered `5 years` (unit group swallows the `+`) → a true claim read as fabrication | `canon_plus()` folds both forms |
| fact_check: employment years in the metric whitelist | "2,020 participants" cleared because someone started a job in 2020 | years no longer injected; date ranges are check 2's job |
| fact_check: in-progress credentials | checked at the **first** occurrence only → qualified in the summary, bare in the skills list, passed | all occurrences via `re.finditer` |

### Wave 2 — determinism + discovery unification (`569e016`, `97ec275`)

- **`harness/apply_package.py`** replaces ~40 lines of prose that the model
  re-derived every run. One command: folder + `.created`, friendly-name copies,
  `.md` mirrors, `.docx`, the combined document **in all three formats** with a
  real Word page break, and the tracker row.
  - It also writes `cv_draft.tex` / `cover_letter.tex` — the names upstream's
    `/interview` and `/outcome` look for. The harness only wrote friendly names,
    so interview prep could not find the documents it prepares from. **This is
    the filename bridge; upstream needed no edit.**
  - Pinned by `test_combined_document_exists_in_all_three_formats` — the
    combined doc shipped as PDF-only for the entire original build.
- **`harness/tracker_row.py`** — the only tracker writer. DictWriter quoting,
  header healing, atomic rewrite.
- **`harness/rotate_backup.py`** — the keep-5 rule two commands described and
  nothing implemented, plus `--list` / `--restore` so a person can reach it.
- **Discovery unified:** `scrape.md` now delegates fetch+dedup to the
  `job-scraper` skill, which owns `job_scraper/seen_jobs.json`. Upstream `/rank`
  reads *only* that file and stopped with "run /scrape first" immediately after
  a `/scrape` run; `/upskill` aggregate mode was equally starved; and it is the
  only cross-run dedup store. Company-scope results join the same memory with a
  `source: company:<name>` tag. Shortlist verdicts mapped to `/rank`'s bands.
- Hardening: `tracker_xlsx` column indices derived from the header, non-integer
  score tolerated, aux paths parameterised; `tex_to_md` asserts → `SystemExit`
  (asserts vanish under `-O`); telemetry numeric guard + ASCII fallback
  separator; `setup.py` IndexError guards + atomic settings write.

### Wave 3 — ease of use, docs, declutter (`2bdac2c`, `dcdb803`)

- **`/today`** (`harness/today.py` + `today.md`) — the daily driver. Reads
  tracker, run log, outcome files, shortlist; ends with **numbered actions** the
  user picks by number. Regenerates the workbook when stale, which removed the
  `/tracker` ritual from the daily loop. Adopts `/outcome`'s days-quiet formula
  (date **or latest dated note**) as the one formula.
- **Plain-language routing** — fenced table in `CLAUDE.md` and `AGENTS.md`
  mapping "find me jobs", "I got rejected by X" etc. to workflows. Same block
  states the canonical status vocabulary and redirects bare `/apply` (which
  silently skips all seven harness additions).
- **First-run guards** in `scrape`, `apply-any`, `companies` — offer onboarding
  instead of failing into undefined behaviour.
- **Quick-start onboarding** (~5 min) alongside full (~15–20); `/setup-harness`
  now tells upstream `/setup` to skip its own welcome and path menu (the nesting
  produced a second "Welcome!" and re-asked identity/education/salary).
- **Express setup** — ~2 prompts instead of 7–13; **permission seeding** into
  `settings.local.json` removes the 6–8 dialogs per application run; progress
  lines before every multi-minute step; MiKTeX failures print the exact command.
- **Fact-gate wording** — `FABRICATION-RISK` → `UNSUPPORTED`, leading with
  "usually means it is not recorded yet — confirm with `/fact`". Strictness
  unchanged, asserted by tests.
- **Docs truth-up** — tiered command table (daily/now-and-then/occasional/rare);
  the six undocumented commands documented; volume stated honestly ("1–3 strong
  applications per session, not twenty"); README stops claiming setup installs
  Node/Bun/TeX/poppler; RUNTIME-MAP corrected (`.claude/skills` is **not**
  auto-discovered on Codex, and `posting-intake`/`humanizer` are mandatory);
  Codex stubs added for `/today`, `/outcome`, `/interview`, `/offer`.
- **Declutter** — 18 build-history files → `docs/build-history/` with an index
  (`docs/` went 24 → 6 entries); example YAMLs → `examples/` with all four
  referencing files updated.

### Wave 4 — new capability (`7136225`)

- **`/offer`** — the highest-leverage moment had no support. Compares against
  stated minimum/target, asks whether they want to negotiate at all, drafts one
  message, **never invents a competing offer**, routes the draft through the
  fact gate, disclaims financial/legal advice and invented market data.
- **Referrals** — optional `contacts:` per employer in `companies.yaml`,
  surfaced by `/apply-any` *before* drafting. A prompt, not a gate. No CRM.
- **Deadlines** — `deadline` column on `shortlist.csv` (additive,
  DictReader-safe), shown in the workbook, surfaced by `/today`.
- **Conversion analytics** — Summary tab gains **response rate by channel** and
  the shortlist verdict distribution.
- **Batch close-out** — `/today` can mark long-dead applications `no_response`
  in one pass, on explicit consent, never touching `interview_only`.

---

## 3. Current state

```
HEAD         7136225  Wave 4
git status   clean, pushed, CI green
tests        281 harness + 155 upstream + 157 Bun (portal CLIs)
guards       security_guards, harness_guards, lint_skills, privacy_sweep — all green
harness/     12 scripts   .claude/commands/  23   tests_harness/  10 files
```

**New files this session:** `harness/{status,tracker_row,rotate_backup,apply_package,today}.py`,
`.claude/commands/{today,offer}.md`, `.codex/prompts/{today,offer,outcome,interview}.md`,
`tests_harness/{test_status_and_rows,test_apply_package,test_today}.py`,
`docs/build-history/README.md`.

---

## 4. Conventions a successor must not break

1. **Upstream `[U]` files stay byte-identical.** Never edit
   `.claude/commands/{setup,apply,rank,outcome,interview,expand,add-portal,add-template,gmail-sync,html-report,notion-sync,reset}.md`,
   `.claude/skills/{job-application-assistant,job-scraper,upskill}/`,
   `tools/{security_guards,lint_skills,verify_pdf,check_*}.py`, `tests/`,
   `SETUP.md`, `LICENSE`, `CHANGELOG.md`, `SECURITY.md`, `CONTRIBUTING.md`.
   **The 155 upstream tests passing is the proof.** Ownership map:
   `docs/build-history/plan-D-repo-structure.md`.
   *This is why fixes look indirect*: the filename bridge writes what
   `interview.md` expects rather than teaching it new names; the status helper
   normalises on read rather than correcting `outcome.md`.
2. **`.gitignore` harness block must stay negation-free** — upstream's
   `security_guards.py` fails any `!` outside its own allowlist. Name shipped
   files so they never match instead (`*.example.yaml`, `documents/demo/`).
3. **`.claude/settings.json` is frozen.** Local permissions go in
   `settings.local.json`.
4. **Never weaken a check to make something pass.** Fix the code or content; if
   the check is provably wrong, fix it *and* pin a regression fixture.
5. **Contract tests over markdown prose are weak.** A large share of the
   harness suite asserts sentences exist in command files. They pass while a
   bug is live — the combined-document gap proved it. Prefer tests that read
   the real output directory.
6. **Only the fictional demo candidate (Riley Chen) may be candidate-shaped
   content**, and only in `evidence/register.example.yaml`, `documents/demo/`,
   `examples/`.

---

## Outstanding work

Nothing is broken or half-finished. These are the honest gaps.

### A. Verification debt (highest value, do first)

1. ~~**Timed stranger-run from a clean clone.**~~ **DONE — measured, see §5.**
2. **Screenshot / PDF intake has never run live** (waivers W2, plan-M tests 11
   and 12). It is a headline capability; a silent OCR misread of a company name
   or date propagates into a submitted document. **Highest real user risk in
   the system.**
3. **Cross-runtime drills** (plan-M 27, 28) — Claude→Codex and back, mid-flight.
   Needs a second terminal. Only affects dual-runtime users.
4. **Live board runs** — `/add-portal` → new board → next `--scope boards` run
   (plan-M 6, 8). Excluded from CI by upstream's own design.

### B. Known-but-unfixed (deliberate, recorded)

- **`match_folder` has no abbreviation handling** — `Lab` vs `Laboratory`
  scores 0.5 and misses; `test_threshold_still_rejects_a_half_match` pins the
  current behaviour. Now less critical: `apply_package.slugify()` is the forward
  function, so new folders are deterministic and the fuzzy matcher only serves
  legacy folders.
- **`_company_key` is the first word only** — "Canadian Tire" and "Canadian
  Nuclear Laboratories" share a key. Two similarly-named rows could resolve to
  one folder.
- **No concurrency control anywhere.** Two overlapping `/tracker` runs race in
  `shutil.move`. Single-user tool; not worth a lockfile yet.
- **`setup.py` is named `setup.py` at repo root**, so `pip install .` would run
  an interactive installer. Rename to `harness_setup.py` was flagged for owner
  sign-off and **not done** — it touches README, SETUP.md, USER-GUIDE and the
  owner's muscle memory.
- **Compensation has no weight in scoring** (upstream's five dimensions are
  30/25/15/30). `/offer` and `/scrape` now *surface* pay against
  minimum/target, but ranking still ignores it. Changing upstream's weights
  needs an owner decision.
- **`salary_lookup.py`** needs a `salary_data.json` the user must build; it is
  documented as optional and remains effectively dormant.

### C. Not started (proposed, never approved)

- `/html-report` regenerates a hand-written SVG dashboard by LLM every run —
  the most expensive routine operation in the repo, with no cost warning. It is
  `[U]`, so a fix means a harness-side wrapper or a note in USER-GUIDE.
- Interview **scheduling** — dates are asked conversationally and never
  persisted; no upcoming-interviews view. The Calendar MCP is available and
  unused.
- Multi-round interview tracking beyond upstream's five fixed checkboxes.
- Rejection-reason taxonomy / per-stage drop-off analysis.

### D. Housekeeping

- One Wave 4 commit message lost a backticked phrase to shell expansion
  (`channel: referral` renders as a blank). Cosmetic; the commit is pushed, so
  leave it.
- `docs/build-history/BUILD-STATE.md` still describes the Stage-3 build and has
  **not** been updated with the four review waves. Consider appending a short
  "post-review remediation" section pointing at this file.

---

## 5. The stranger-run (measured 2026-08-04, outstanding item A1)

`git clone` of the public repo at `2a4772b` into a fresh directory outside the
working tree, then `python setup.py` driven exactly as a new user would drive
it. Every number below is a stopwatch or a count from the captured transcript,
not an estimate. Host: Windows 10, Python 3.14.3, Bun 1.3.14, MiKTeX 25.12,
both `claude` and `codex` present.

Two things had to be simulated rather than run, and both are stated as such:

- **The agent CLIs were replaced with a shim** that answers `plugin list` /
  `mcp list` from its own empty state file. Running the real ones would have
  reported the owner's already-installed plugins (hiding four prompts) and
  would have mutated the owner's machine. The shim changes *nothing* about
  which questions setup asks or how long its own work takes.
- **Permission dialogs cannot be counted without a live agent session.** They
  were derived instead: every shell command the apply path issues, checked
  against the seeded allowlist. That is stated as a structural count, not a
  measurement.

### Measured against the Wave 3 acceptance criteria

| Criterion | Asserted | Measured | Verdict |
|---|---|---|---|
| Setup prompts | ≤2 | **1** (express) · 12 (custom, both runtimes) | **pass** |
| Minutes to onboarded | ≤5 | **6.0 min** installer alone, before onboarding starts | **fail** |
| Permission dialogs per apply | ≤2 | **1** un-seeded command, now 0 | pass (was one short of the seed list) |
| Nothing typed beyond `/today` + a number | — | holds; first-run `/today` correctly offers onboarding | pass |

Raw timings: clone 10.0 s · `--doctor` 2.5 s · express install **358.4 s** ·
custom install 205.3 s. Roughly 280 s of the express run is seven sequential
`bun install`s at ~40 s each; the two MiKTeX test compiles are most of the
rest. `--quick` skips the compiles and is the only lever that exists.

### What the run found

1. **4 of the 7 job-board CLIs failed to install on a clean clone**, and setup
   exited 1 with *"The harness will not work correctly until these are
   resolved"* — a dead end, since the printed fix ("Fix the Bun row above") did
   not apply: Bun was fine. Root cause is `@types/bun` pulling in the `bun` npm
   package, whose postinstall downloads a platform binary and fails on Windows
   with `Failed to find package "@oven/bun-windows-x64-baseline"`. The packages
   are already extracted by then, so a second `bun install` completes — a plain
   re-run cleared all 7 without any other change (415.7 s over two runs, two
   prompts). **Fixed:** `install_portal_deps` retries once. Single pass now
   exits 0 with 7/7 in 358.4 s. Pinned by `PortalInstallRetry`. The failing
   package.json files are upstream `[U]`; the retry is harness-side.
2. **`pdftotext` was missing from the seeded permissions.** The ATS text-layer
   check is a mandatory step of the Verification Checklist, so it fires on
   every application — the only un-seeded command left in the apply path.
   **Fixed:** added to `HARNESS_PERMISSIONS`, pinned by `SeededPermissions`.
3. **Express described itself wrongly.** It claimed to offer "Caveman, the
   browser tools and the statusline but does not assume them". Express sets
   `AUTO_YES`, so every `confirm()` takes its default — and Playwright,
   Firecrawl and the statusline all default to yes. Only Caveman defaults to
   no. **Fixed:** the blurb now says what it does, with the counts corrected to
   the measured 1 / 8 / 12. (README and USER-GUIDE were already accurate: "one
   confirmation instead of a dozen questions" is exactly 1 vs 12.)
4. **The doctor's all-clear contradicted its own notes.** With Bun, both TeX
   engines and pandoc on the persistent PATH but not the running shell, the
   table printed four `RESTART SHELL` rows, told the user to reopen the
   terminal — and then closed with "All required prerequisites are in place".
   The next real run fails portal install on exactly that state. **Fixed:** the
   all-clear is now withheld when any row is `RESTART SHELL`.

### Honest shortfalls left standing

- **≤5 minutes is not achievable as specified.** The installer alone is 6
  minutes on a warm network, and that is *before* `/setup-harness`, whose
  quick-start path advertises another ~5. A truthful figure for clone-to-first-
  search is **10–12 minutes**. Either the criterion or the claim should move;
  the code cannot close a 280-second dependency install.
- **The onboarding half was not measured.** `/setup-harness` deliberately has
  no fixed question list ("the gaps you actually found — never a fixed list"),
  so its cost is not machine-countable. Measuring it needs a live agent session
  with a real CV, which is the natural companion to outstanding item A2.
- **`Bash(python harness/*.py:*)` patterns assume the literal command `python`.**
  An agent that reaches for `python3` or `py` matches none of them and every
  seeded permission silently stops working. Not hit on Windows; would be worth
  a second pattern per entry if anyone runs this on Linux.
