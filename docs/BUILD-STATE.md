# BUILD-STATE — Stage 3 (Opus builds)

**How to resume:** re-paste `docs/OPUS-KICKOFF.txt`. Read this file first, redo
nothing marked `[x]`, continue at the first `[~]` or `[ ]`. Contract:
`docs/IMPLEMENTATION-PLAN.md`. Phase specs: `docs/plan-G-phases.md`.

Legend: `[ ]` not started · `[~]` in progress · `[x]` done (+ commit) ·
`[!]` blocked/waived (reason in session notes).

---

## Phase checklist

### P0 — Bootstrap (repo + build machine)
- [x] P0.1 Upstream `MadsLorentzen/ai-job-search` @ tag v1.3.0 merged into this git history; `upstream` remote added with push URL `DISABLED-never-push-to-upstream` — commit `7dff125`
- [x] P0.2 Hardened `.gitignore` (upstream model + harness families) — commit `8d9c107`
- [x] P0.3 Private GitHub repo `WilliamEbong/job-search-agent-harness` created and pushed — commit `1319828`
- [x] P0.4 Prereq installs: MiKTeX (lualatex+xelatex), poppler (pdftotext+pdfinfo), Bun, pandoc — all verified running (versions in session notes)
- [x] P0.5 Caveman installed on both runtimes; LICENCE verified **MIT** (plan-J J.1 UNVERIFIED resolved)
- [x] P0.6 `requirements.txt` pinned (pyyaml, openpyxl, pypdf) — commit `8d9c107`
- [x] **P0.7 GATE GREEN** — upstream `tests/` 155 pass · portal CLI 157 Bun tests pass across 6 CLIs, typecheck clean · all engine probes resolve · `claude plugin list` + `codex plugin list` both show caveman · CI green on the private repo (run 30879303030, 2m17s)

**P0 COMPLETE.**

### P1 — setup.py installer + doctor
- [x] P1.1 `setup.py` (stdlib only): runtime detection, prereq checks, per-runtime plugin installs (Ponytail; Caveman optional w/ lite recommendation; optional Playwright + Firecrawl MCP), portal CLI deps, verify-every-step, doctor table — commit `3c6b5a7`
- [x] P1.2 `tests_harness/test_setup_doctor.py` (mocked PATH probes) — 26 tests — commit `3c6b5a7`
- [x] **P1.3 GATE GREEN** — `python setup.py --doctor` all-green on this machine incl. both stock-template compiles; full `--yes` run idempotent

**P1 COMPLETE.**

### P2 — Evidence layer (truth tier)
- [x] P2.1 Read-only snapshot `../job-search-ref` created (`git clone --local --branch personal`)
- [x] P2.2 `evidence/register.example.yaml` (schema + demo-candidate entries) — commit `84c8311`
- [x] P2.3 `harness/fact_check.py` + `harness/fact_check_config.yaml` — commit `84c8311`
- [x] P2.4 Commands `fact.md`, `verify-facts.md` — commit `84c8311`
- [x] P2.5 `tests_harness/test_fact_check.py` — 22 tests (6 check classes + 3 regressions) — commit `84c8311`
- [x] **P2.6 GATE GREEN** — bad fixture → 11 red lines with every planted class named; clean fixture → exit 0; M-tests 16 and 17 pass

**P2 COMPLETE.**

### P3 — Onboarding (evidence bank + preferences + templates + career review)
- [ ] P3.1 `.claude/commands/setup-harness.md` (CV-first → interview w/ speed-up/end/revisit → register build → preference interview → template choice → companies offer)
- [ ] P3.2 `preferences.example.yaml`
- [ ] P3.3 `.claude/commands/career-review.md`
- [ ] P3.4 `.claude/commands/companies.md` + `companies.example.yaml`
- [ ] P3.5 Gate: demo onboarding E2E; M-tests 1, 2, 3, 4, 34, 35, 36

### P4 — Intake + apply overlay
- [ ] P4.1 `.claude/skills/posting-intake/SKILL.md` (6-rung ladder)
- [ ] P4.2 `.claude/skills/humanizer/` vendored (SKILL.md + LICENSE + provenance)
- [ ] P4.3 `.claude/commands/apply-any.md` (+ hard-constraint gate, autonomy ladder, post-humanize re-ground)
- [ ] P4.4 `harness/tex_to_md.py` + quad-format packaging + archive layout
- [ ] P4.5 `docs/latex-gotchas.md`
- [ ] P4.6 Gate: demo `apply <fixture>` full package; M-tests 10–14, 18–22

### P5 — Discovery (modes + boards + scopes + company search)
- [ ] P5.1 Usage modes + caps + cost posture in `preferences.yaml` schema
- [ ] P5.2 `.claude/commands/scrape.md` (one wrapper: modes, overrides, five scopes, company-of-interest search)
- [ ] P5.3 `.agents/skills/jobbank-ca-search/` ported + sanitized
- [ ] P5.4 `harness/run_log.py`; open-job validation; shortlist verdicts
- [ ] P5.5 `docs/board-intelligence.md`
- [ ] P5.6 Gate: focused-mode board run + company scope run; M-tests 5–9, 15, 37, 38

### P6 — Tracking
- [ ] P6.1 `harness/tracker_xlsx.py` (4 tabs)
- [ ] P6.2 `harness/archive_applications.py` + shared folder matcher
- [ ] P6.3 `.claude/commands/tracker.md` (stale "three tabs" text fixed)
- [ ] P6.4 Gate: ported suites green; regenerate-twice idempotent; M-tests 23, 24

### P7 — Continuity engine
- [ ] P7.1 `state/` writers + milestone ritual in command docs
- [ ] P7.2 `.claude/commands/continue.md`
- [ ] P7.3 `harness/telemetry_statusline.py` + statusline registration in setup
- [ ] P7.4 Gate: kill-and-resume drill; M-tests 25, 26, 29

### P8 — Runtime adapters + live Codex lane
- [ ] P8.1 `RUNTIME-MAP.md` final
- [ ] P8.2 `.codex/prompts/` stubs + `AGENTS.md` harness block + `CLAUDE.md` block
- [ ] P8.3 Gate (live Codex): continue ritual, apply pipeline, humanizer `@`-invocation, plugin installs; M-tests 27, 28

### P9 — Demo candidate, E2E matrix, privacy guard
- [ ] P9.1 `documents/demo/` fictional candidate + `examples/` posting fixture
- [ ] P9.2 `tools/harness_guards.py` + `harness/privacy_sweep.py` + CI jobs
- [ ] P9.3 Full plan-M matrix (tests 1–40) run
- [ ] P9.4 Fresh-install test (plan-L, 10 steps)
- [ ] P9.5 `../job-search-ref` deleted
- [ ] P9.6 Gate: all M tests green or waived w/ reason; privacy sweep zero hits; CI green; M-tests 30, 31, 33

### P10 — Docs + release gate
- [ ] P10.1 `README.md` (attribution front-and-center)
- [ ] P10.2 `USER-GUIDE.md` (repo root, all features)
- [ ] P10.3 `NOTICE.md` (plan-J J.2 text)
- [ ] P10.4 Owner guide update
- [ ] P10.5 👤 Demo-candidate package eyeball
- [ ] P10.6 👤 Release gate: privacy sweep shown, "flip public?" (default: stay private)
- [ ] P10.7 Gate: doc 03 "How you know it's done" satisfied; M-tests 32, 40

---

## plan-M test results

Filled in as tests run. Status: `pass` / `fail→fixed` / `waived (reason)`.

| # | Test | Status | Evidence |
|---|---|---|---|
| 16 | Unsupported metric rejection | **pass** | `fixture_bad.txt` red line 1; `UnsupportedMetric` tests |
| 17 | Unsupported credential rejection | **pass** | red lines 6–7; in-progress credential blocked without qualifier, passes with it |
| 39 | Caveman optional prompt | **pass** (P1 half) | `CavemanOffer` tests: explanation names lite + protects letters; decline leaves it uninstalled; accept verifies via `plugin list`. Live both-runtime half re-run at P9. |
| others | see `docs/plan-M-e2e-tests.md` | not yet run | — |

---

## Session notes (append-only)

### Session 1 — 2026-08-03 (Opus, Stage 3 start)

- Read the full plan set in the order IMPLEMENTATION-PLAN §1.1 requires:
  O → G → D, E, F, H, I, J, K, L, M, N → A, B, C → docs 01, 02, 03.
- No prior BUILD-STATE existed → fresh Stage-3 start, nothing to resume.
- Machine probe (Windows PowerShell PATH — the PATH `setup.py` will see):
  present — git 2.48.1, gh 2.93.0, python 3.14, node/npm, uv, claude, codex,
  winget, choco; missing — `bun`, `pandoc`, `lualatex`, `xelatex`, `pdfinfo`.
- **Deviation from plan-B §B.1, recorded not silently absorbed:** B.1 lists
  poppler as entirely absent. Reality is partial — `pdftotext.exe` ships with
  Git for Windows at `C:\Program Files\Git\mingw64\bin\`, but `pdfinfo` does
  not. Consequence carried into P0/P1: the doctor probes **both** binaries;
  treating `pdftotext` alone as proof of poppler would give a false green to
  any user who has only Git for Windows.

**P0.4 installs — done, and no owner clicks were needed.** `winget install`
for Bun succeeded; pandoc, poppler, and MiKTeX reported *already installed*
(winget exit `-1978335189` = no upgrade applicable). They were missing from
the shell only because this session inherited a stale PATH — all four sit on
the persistent user PATH. Verified by running each binary with a refreshed
PATH:

| Tool | Result |
|---|---|
| lualatex | LuaHBTeX 1.24.0 (MiKTeX 25.12) |
| xelatex | MiKTeX-XeTeX 4.16 (MiKTeX 25.12) |
| pdftotext / pdfinfo | poppler 25.07.0 (winget) + MiKTeX copies — both resolve |
| bun | 1.3.14 (newly installed) |
| pandoc | 3.10 |

Note carried to P1: a freshly installed tool is on the *persistent* PATH but
not in an already-running shell. The doctor must report "installed — restart
your shell" rather than "missing", or it lies to every user who installs and
re-runs in the same terminal.

**P0.1 upstream merge.** `git merge v1.3.0 --allow-unrelated-histories`, clean,
zero conflicts — our tree held only `docs/`, upstream's tree has no `docs/`.
Upstream history is retained so the plan-I tag-merge ritual works. The push URL
for `upstream` is the literal `DISABLED-never-push-to-upstream`.

**P0.2 gitignore — a design constraint found while writing it.**
`tools/security_guards.py` is upstream-owned `[U]` (never edited; plan-D:59-60
routes our extension to a new `tools/harness_guards.py`). Its
`check_gitignore()` fails **any** `!negation` outside its own hardcoded
allowlist. So the harness block cannot use negations to carve out exceptions.
Resolution: enumerate the ignore families positively and *name every shipped
file so it never matches* — `*.example.yaml` for the register/preferences/
companies schemas, `documents/demo/` for the fictional candidate. No check was
weakened; the constraint shaped the naming instead.

**Consequence to honour at P3 and P9 (decided now, logged so it is not
re-litigated later):** the demo candidate must NOT be onboarded *inside this
repo*. Upstream's profile files
(`.claude/skills/job-application-assistant/0*.md`) are `[U]` and ship with
placeholder tokens; a real onboarding run writes candidate content into them,
which would both edit `[U]` files and put candidate-shaped content outside the
three sanctioned locations (plan-D:75-76). The demo E2E therefore runs in a
throwaway clone outside the repo — exactly as the plan-L fresh-install test
already specifies.

**Verification run after P0.2/P0.6, on the merged tree:**
`python tools/security_guards.py` → OK · `python tools/lint_skills.py` → OK
(9 skills, 12 commands, settings.json) · `python -m unittest discover -s tests`
→ **155 tests, OK**.

**P0.3 repo.** `gh repo create job-search-agent-harness --private` →
`https://github.com/WilliamEbong/job-search-agent-harness`, pushed. Upstream's
CI triggers on `master` only, so a one-line `[P]` personalization adds `main`
to `on.push.branches`; without it no CI run fires on this fork and the P0.7
"CI green" gate could not be evidenced. Both branch names are listed so
upstream tag merges never fight the edit. Also ran `gh repo set-default` —
with two remotes, `gh run list` was resolving to **upstream's** runs and
showing green results that were not ours. Worth knowing: any later `gh` call
in this repo must be read as ours only because of that pin.

**P0.4 bounded repair — Bun crashed, and this changes what the doctor must
do.** `winget install Oven-sh.Bun` (the default build) installed cleanly and
then panicked on every invocation:

```
Features: no_avx2
panic: Illegal instruction at address 0x7FF7EC26F82C
```

This machine's CPU has no AVX2, and the stock Bun build requires it. Repair:
uninstalled it and installed `Oven-sh.Bun.Baseline` instead — same version
1.3.14, works. **Carried into P1 as a real requirement:** a doctor that only
checks "is `bun` on PATH" reports green on a machine where every portal CLI
crashes. The doctor must *execute* `bun --version` and, on an illegal-
instruction/panic exit, tell the user to install the Baseline build. This is a
check being strengthened, not weakened.

**P0.5 Caveman — installed both runtimes, licence verified.**
Claude: `claude plugin marketplace add JuliusBrussee/caveman` +
`claude plugin install caveman@caveman` → shows in `claude plugin list`
(version `7066cc815414`, enabled).
Codex: **`codex plugin marketplace add JuliusBrussee/caveman` +
`codex plugin add caveman@caveman` both succeed** and Caveman shows in
`codex plugin list`.
Licence: `LICENSE` in the plugin cache reads "MIT License / Copyright (c) 2026
Julius Brussee" with the standard grant clause. plan-J J.1's
"verify at P0, stop if not MIT-compatible" is **resolved: MIT, no conflict**.

*Finding that simplifies plan-F §6:* that table routes Codex Caveman through
`npx skills add JuliusBrussee/caveman -a codex` (a per-session `/caveman`
skill) and flags `codex plugin marketplace add` as UNVERIFIED-thin. The plugin
route is now verified working on codex-cli 0.144.6, so `setup.py` will use the
**same two-command marketplace mechanism for both Ponytail and Caveman on both
runtimes** — one mechanism instead of two, and it is the one whose result
`plugin list` can actually confirm. The `npx skills add` path stays documented
in RUNTIME-MAP as the fallback if a future Codex drops plugin support.

**P0.7 gate — GREEN, every item evidenced:**

| Gate item | Result |
|---|---|
| upstream `tests/` | 155 tests, OK |
| portal CLI `bun test` | 6 CLIs, typecheck clean, **157 tests, 0 fail** |
| engine `--version` probes | lualatex, xelatex, pdftotext, pdfinfo, bun, pandoc all resolve |
| `claude plugin list` shows caveman | yes |
| `codex plugin list` shows caveman | yes |
| CI green on private repo | run `30879303030`, success, 2m17s |

Next: P1 (`setup.py` + doctor).

### P1 — setup.py + doctor

**Verified endpoints before writing any install code.** The owner's live
Firecrawl MCP entry is a URL with a **personal API key embedded in the path**.
That key was deliberately NOT copied into the repo, and no part of it is
recorded here. Instead the documented endpoint was fetched from Firecrawl's
own docs: `https://mcp.firecrawl.dev/v2/mcp`, which works keyless
(rate-limited search/scrape/parse) and takes a key via an
`Authorization: Bearer` header when one exists. `setup.py` therefore passes the
key **by env-var name** (`FIRECRAWL_API_KEY`) to each runtime's own config and
never reads, stores, or echoes the value. Two tests pin this: one asserts a
keyless add sends no `Authorization`, the other plants a fake secret in the
environment and asserts the secret string never appears in any command.

Both runtimes' MCP syntaxes were read from `--help` rather than assumed:
Claude `claude mcp add --transport http <name> <url> [--header ...]`;
Codex `codex mcp add <name> --url <url> [--bearer-token-env-var VAR]`.

**Three honesty rules are enforced in code, not documented as intentions:**

1. **Bun is executed, not located.** From the P0 finding — the stock build
   installs cleanly on a no-AVX2 CPU and panics on every call. `check_bun()`
   runs `bun --version` and maps a panic to DEGRADED with the Baseline install
   command as the fix.
2. **poppler requires both binaries.** From the session-1 deviation —
   `check_poppler()` fails if `pdfinfo` is absent even when `pdftotext` is
   present, and says why ("Git for Windows ships it").
3. **Stale PATH is its own status.** A tool found only on the registry PATH
   reports `RESTART SHELL`, never `MISSING`, so a user who just installed
   something is not told to install it again.

**TeX is verified by compiling the real stock templates** (`cv/main_example.tex`
with lualatex, `cover_letters/cover_example.tex` with xelatex), each from
inside its own directory because `cover.cls` resolves its bundled Raleway
fonts relative to the working directory. `--version` succeeding is not
evidence a CV will build. `--quick` skips the compiles and reports them
`UNVERIFIED` — never `OK`.

**Plugin installs are proved by re-listing.** `install_plugin()` treats "exit 0
but absent from `plugin list`" as UNVERIFIED, not success.

**P1.3 gate — live on this machine:**

```
Python OK 3.14.3 · Node OK v24.14.1 · Bun OK 1.3.14
lualatex OK (LuaHBTeX 1.24.0) · lualatex compile OK — CV template built (45 KB)
xelatex  OK (MiKTeX-XeTeX 4.16) · xelatex compile  OK — cover letter built (12 KB)
poppler OK (pdftotext + pdfinfo) · pandoc OK 3.10
Python packages OK · Portal CLIs OK (6 CLIs) · runtimes: claude, codex
ponytail/caveman/playwright/firecrawl: OK on both runtimes
→ All required prerequisites are in place.
```

Full `--yes` run re-ran cleanly with everything already present (idempotent).
26 harness tests + 155 upstream tests + guards + lint all green.

Next: P2 (evidence layer / truth tier). P2.1 creates the read-only snapshot
`../job-search-ref` — the first and only time the private system is touched,
and it is a `git clone --local` read, never a write.

### P2 — Evidence layer (truth tier)

**Snapshot, and a pre-existing condition in the private system.**
`git clone --local --branch personal ../job-search ../job-search-ref`. Verified
immediately afterwards that the private system is untouched: HEAD still
`e8c3e51`, reflog's newest entry is still the pre-existing commit (a clone
writes nothing to its source).

Its `git status` does show one modification: ` D ~$Job_Search_Tracker.xlsx`.
**This predates this build and was not caused by the clone.** It is the Excel
lock file that plan-A §hygiene already flagged as committed by mistake; Excel
deletes it when the workbook closes, leaving a tracked-but-absent file. Per the
never-edit rule the private system was left exactly as found — not tidied, not
committed. Recorded here only so a future reader does not attribute it to
Stage 3.

**What was ported, and what deliberately was not.** Only mechanisms: the
checker's six check classes, the register's 14-section schema, and the
resolution protocol from the two commands. No career fact, employer, metric or
document from the private register was read into this repo — the schema was
extracted programmatically as *key names and value types only*.

**The generalization that makes the checker candidate-agnostic.** The private
checker hardcoded a `TECH_LEXICON` and a `CODER_PATTERNS` list encoding one
person's "not-a-coder" rule. Both now live in
`harness/fact_check_config.yaml`, and a constraint family runs **only when the
user's own register declares a `positioning_constraint` with that id**. A
candidate who genuinely is a software engineer has no `programming_claims`
entry, so none of those patterns can fire for them. Pinned by
`test_constraint_patterns_do_not_fire_without_a_declared_constraint`.

Noted, not a defect: the demo register also declares a `management_claims`
constraint that has no regex family in the config. It is therefore Tier-2 only
(the reviewer enforces it in prose). A declared constraint without patterns is
a legitimate state, not a silent failure.

**Three defects found and fixed during the port — each by fixing the check and
pinning a fixture, never by loosening anything:**

1. *Caught before shipping.* The config's constraint regexes were first written
   as YAML folded scalars (`>-`), which replace each line break with a space.
   That turned `(python|typescript|\n javascript)` into an alternative matching
   only `" javascript"` with a leading space — a pattern that still compiles,
   still reads correctly, and no longer catches what it was written to catch.
   Every regex is now a single-line quoted scalar, with a comment saying why.
2. *False positives.* The lexicon contains ordinary English words — `Go`,
   `Spring`, `React`, `Rust`, `Oracle`, `Spark`, `Ruby`. Matched against
   lowercased text, "the spring sampling programme" and "volunteers go further"
   became technology claims. Fixed with a `case_sensitive_lexicon` matched
   against the original text. This does **not** weaken detection: real keyword
   stuffing capitalises the name ("experience with Go and Rust"), and a test
   asserts that case is still caught.
3. *Silent gap.* The numeral check fires only for units in a whitelist, which
   omitted `records`, `sites`, `volunteers`, `households`, `participants`,
   `reports`, `applications` — so those claims were never checked at all.
   Whitelist broadened (a strengthening). The remaining ceiling is now asserted
   by an explicit test, `test_numeral_with_an_unlisted_unit_is_a_known_ceiling`,
   so the limit is visible rather than implied away.

Both inherited regressions carried over intact and still pinned: percentage
spellings folding onto `%`, and the posting whitelist requiring a whole-number
token (the one that had let a package pass spuriously).

**P2.6 gate:**

| Evidence | Result |
|---|---|
| `fixture_bad.txt` | **11 red lines**, exit 11 — every planted class named |
| `fixture_clean.txt` | exit 0 |
| plan-M 16 (unsupported metric) | pass |
| plan-M 17 (credential, both halves) | pass |
| harness tests | 48 pass |
| upstream tests | 155 pass |
| lint / security guards | OK (9 skills, 14 commands) |

Next: P3 (onboarding — CV-first interview, preferences, templates, career
review, companies of interest).
