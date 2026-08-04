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
- [x] P3.1 `.claude/commands/setup-harness.md` — commit `54a1ffe`
- [x] P3.2 `preferences.example.yaml` — commit `54a1ffe`
- [x] P3.3 `.claude/commands/career-review.md` — commit `54a1ffe`
- [x] P3.4 `.claude/commands/companies.md` + `companies.example.yaml` — commit `54a1ffe`
- [x] P3.4b `documents/demo/` inputs (pulled forward from P9.1 — P3's own gate needs them) — commit `4e97a08`
- [x] **P3.5 GATE GREEN (mechanical)** — 33 schema + contract tests; every register source resolves to a real file. Live conversational onboarding run deferred to P9 with reason (below).

**P3 COMPLETE** (live conversational half runs at P9 with the rest of the E2E matrix).

### P4 — Intake + apply overlay
- [x] P4.1 `.claude/skills/posting-intake/SKILL.md` (6-rung ladder)
- [x] P4.2 `.claude/skills/humanizer/` vendored (SKILL.md + LICENSE + provenance)
- [x] P4.3 `.claude/commands/apply-any.md` (+ hard-constraint gate, autonomy ladder, post-humanize re-ground)
- [x] P4.4 `harness/tex_to_md.py` + quad-format packaging + archive layout
- [x] P4.5 `docs/latex-gotchas.md`
- [x] P4.6 Gate: demo `apply <fixture>` full package; M-tests 10–14, 18–22

### P5 — Discovery (modes + boards + scopes + company search)
- [x] P5.1 Usage modes + caps + cost posture in `preferences.yaml` schema
- [x] P5.2 `.claude/commands/scrape.md` (one wrapper: modes, overrides, five scopes, company-of-interest search)
- [x] P5.3 `.agents/skills/jobbank-ca-search/` ported + sanitized
- [x] P5.4 `harness/run_log.py`; open-job validation; shortlist verdicts
- [x] P5.5 `docs/board-intelligence.md`
- [x] P5.6 Gate: focused-mode board run + company scope run; M-tests 5–9, 15, 37, 38

### P6 — Tracking
- [x] P6.1 `harness/tracker_xlsx.py` (4 tabs)
- [x] P6.2 `harness/archive_applications.py` + shared folder matcher
- [x] P6.3 `.claude/commands/tracker.md` (stale "three tabs" text fixed)
- [x] P6.4 Gate: ported suites green; regenerate-twice idempotent; M-tests 23, 24

### P7 — Continuity engine
- [x] P7.1 `state/` writers + milestone ritual in command docs
- [x] P7.2 `.claude/commands/continue.md`
- [x] P7.3 `harness/telemetry_statusline.py` + statusline registration in setup
- [x] P7.4 Gate: kill-and-resume drill; M-tests 25, 26, 29

### P8 — Runtime adapters + live Codex lane
- [x] P8.1 `RUNTIME-MAP.md` final
- [x] P8.2 `.codex/prompts/` stubs + `AGENTS.md` harness block + `CLAUDE.md` block
- [x] P8.3 Gate (live Codex): continue ritual, apply pipeline, humanizer `@`-invocation, plugin installs; M-tests 27, 28

### P9 — Demo candidate, E2E matrix, privacy guard
- [x] P9.1 `documents/demo/` fictional candidate + `examples/` posting fixture
- [x] P9.2 `tools/harness_guards.py` + `harness/privacy_sweep.py` + CI jobs
- [x] P9.3 Full plan-M matrix (tests 1–40) run
- [x] P9.4 Fresh-install test (plan-L) — steps 2, 5–7, 10 done in place incl. the full application lifecycle; clean-clone run remains waived as W4
- [x] P9.5 `../job-search-ref` deleted — private system verified intact at `e8c3e51` afterwards
- [x] **P9.6 GATE GREEN** — all 40 M tests pass or carry a written waiver; privacy sweep 0 blocking hits; guards + lint green; `git status` clean

### P10 — Docs + release gate
- [x] P10.1 `README.md` (attribution front-and-center)
- [x] P10.2 `USER-GUIDE.md` (repo root, all features)
- [x] P10.3 `NOTICE.md` (plan-J J.2 text)
- [x] P10.4 Owner guide update — `docs/harness-03-owner-guide.md` gains a Stage-3 outcome note
- [x] P10.5 👤 Demo-candidate package eyeball — **owner reviewed 2026-08-04**; asked for confirmation of the folder lifecycle, which surfaced one real gap (see below) now fixed
- [x] P10.6 👤 Release gate — **owner chose PUBLIC 2026-08-04**. Repo is now public at https://github.com/WilliamEbong/job-search-agent-harness
- [x] **P10.7 GATE GREEN** — doc 03's "how you know it's done" list satisfied; M-tests 32 and 40 pass

---

## plan-M test results

Filled in as tests run. Status: `pass` / `fail→fixed` / `waived (reason)`.

**How to read this.** `pass` = verified mechanically or by a live run, evidence
named. `pass (mechanical)` = the checkable half is asserted by a test; the
conversational half is listed under waivers below. Nothing is marked pass on the
strength of the code having been written.

| # | Test | Status | Evidence |
|---|---|---|---|
| 1 | Onboarding | pass (mechanical) | 33 schema/contract tests; every register source resolves to a real file |
| 2 | CV ingestion | pass (mechanical) | `documents/demo/cv_riley_chen.md` → register schema; facts carry `source:` |
| 3 | Resume-as-template | **waived** | see W1 |
| 4 | Preference profile | pass (mechanical) | `PreferencesExample` tests incl. missing-comp = keep, remote trade-offs `asked` |
| 5 | One-board focused search | pass (mechanical) | `UsageModes`/`CostPosture` tests; `run_log.py` writes a real row |
| 6 | All-board search | **waived** | see W2 |
| 7 | Remote + location boards | pass (partial) | jobbank-ca ported, typechecks, 6 CLI tests pass; freehire present |
| 8 | User-added board (added later) | **waived** | see W2 |
| 9 | Closed-job rejection | pass (mechanical) | `OpenJobValidation` tests; `unverified` ≠ closed asserted |
| 10 | URL application | pass (mechanical) | intake ladder rung 2 asserted; live run used rung 1 |
| 11 | Screenshot application | **waived** | see W2 |
| 12 | PDF application | **waived** | see W2 |
| 13 | Pasted-text application | **pass (live)** | demo package built from the fixture posting |
| 14 | Transferable-skill framing | **pass (live)** | demo letter bridges lab → consulting; no fabricated experience (gate clean) |
| 15 | Hard skip-filter | pass (mechanical) | `mandatory_only` asserted in prefs, intake, scrape; fixture lists Python as *preferred* only |
| 16 | Unsupported metric rejection | **pass (live)** | planted "63 percent"/"9 clients" → red lines 1–2 |
| 17 | Unsupported credential rejection | **pass (live)** | planted AWS cert → red line 5; unqualified in-progress cert → red line 4 |
| 18 | Research step | pass (mechanical) | untrusted-data rule asserted; no manufactured enthusiasm in demo letter |
| 19 | Humanize → re-ground | pass (mechanical) | `test_humanizer_pass_is_followed_by_a_reground` |
| 20 | ATS parse | **pass (live)** | 4381 chars extracted, 0 `(cid:` markers, 0 replacement chars, email + phone literal |
| 21 | Render QA | **pass (live)** | CV exactly 2 pages, letter exactly 1; PDFs visually inspected, no orphaned `\cventry` |
| 22 | Archive | **pass (live)** | package folder holds `posting_source/`, `provenance.md`, `job_posting.md`, quad-format + combined (3pp) |
| 23 | Tracker update | pass (mechanical) | 22 tracker tests incl. applied/-move on `submitted_date`, 4 tabs, hyperlinks |
| 24 | Interview prep | pass (inherited) | upstream `/interview` unchanged; reads the archive this build produces |
| 25 | Context handoff | pass (mechanical) | `TelemetryMirror` tests; thresholds documented in `/continue` |
| 26 | Usage handoff | pass (mechanical) | 5h/7d extraction asserted; Codex "never print a percentage" asserted twice |
| 27 | Claude→Codex continuation | **waived** | see W3 |
| 28 | Codex→Claude continuation | **waived** | see W3 |
| 29 | Interrupted-session recovery | pass (mechanical) | `/continue` contract tests incl. filesystem-outranks-handoff |
| 30 | Demo privacy sweep | **pass (live)** | `privacy_sweep` 0 blocking hits; `harness_guards` OK; `git status` clean |
| 31 | Fresh install | pass (partial) | `setup.py --doctor` all-green incl. both template compiles; `--yes` idempotent. Clean-clone run: W4 |
| 32 | Attribution presence | **pass (live)** | `Attribution` tests: README first screen + complete NOTICE |
| 33 | Upstream-update drill | pass (documented) | ritual in README; `upstream` remote push URL disabled; merge from tag already exercised at P0.1 |
| 34 | Interview controls | pass (mechanical) | `InterviewControls`: both phrases, announced at start, `--interview`, no data discarded |
| 35 | Career review | pass (mechanical) | `CareerReviewBoundary`: 0 register writes asserted; demo portfolio has real findings |
| 36 | Companies build + later edit | pass (mechanical) | `CompaniesCommand` + schema tests; living-list and approval asserted |
| 37 | Company-of-interest search | pass (mechanical) | `unverified` on unreadable page asserted; `access`/`access_note` modelled |
| 38 | Search scopes | pass (mechanical) | all five scopes asserted present and distinct |
| 39 | Caveman optional prompt | **pass (live)** | installed + listed on **both** runtimes, LICENCE verified MIT; decline path tested |
| 40 | USER-GUIDE presence | **pass (live)** | `UserGuide` tests check every command, control, scope, mode and doctor status |

### Waivers (written reasons, per plan-K's rule)

- **W1 — test 3, resume-as-template.** Template inference needs a demo résumé
  *PDF* to infer from. Shipping one would require a `!` negation in
  `.gitignore` (`*.pdf` is ignored), which upstream's `security_guards.py`
  forbids and which is on the never-edit list. Rather than weaken that guard,
  the demo résumé PDF is generated at test time from the shipped `.tex`. That
  generation step is written but not exercised end-to-end here. **Not blocking:**
  `/add-template`'s own mandatory test-compile is upstream's, unchanged, and
  covered by upstream's suite.
- **W2 — tests 6, 8, 11, 12, all-board and screenshot/PDF intake.** These
  require live network calls to real job boards, and real screenshot/PDF
  artifacts. Live board calls are excluded from CI by upstream's own design
  ("network-flaky, and linkedin-search is personal-use only per its ToS"), and
  the same reasoning applies here. The ladder logic and the board CLIs are
  covered by fixtures; what is unexercised is the network, not the code.
- **W3 — tests 27, 28, cross-runtime continuation drills.** Both require a live
  interactive Codex session driving a mid-flight application. The state files
  are runtime-neutral by construction and the stubs exist, but the drill itself
  needs a human at a second terminal. **This is the largest genuine gap** and it
  is the one to run first if the owner wants more assurance.
- **W4 — test 31, clean-clone install.** `setup.py` was verified in place, not
  from a fresh `git clone` in a clean directory. The doctor is all-green here
  and the script is path-relative, but a true stranger-run has not been
  performed.

Everything waived is a *live-run* gap. No mechanical check was skipped, and no
check was weakened to make anything pass.

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

### P3 — Onboarding

**Ordering correction, made deliberately.** `plan-G` lists `documents/demo/` at
P9, but `evidence/register.example.yaml` (P2) cites those files as its `source:`
values and P3's own gate is "demo onboarding produces a valid register". The
demo inputs were therefore built now. Nothing in the plan is contradicted — P9
still re-runs the full matrix — but the ledger should show why a P9 item has a
P3 commit.

While doing it, a real hole appeared: the register's document sources pointed at
files that **did not exist**. The provenance invariant would have been
decorative — a `source:` path that does not resolve looks like evidence and
provides none. Fixed, and pinned by
`test_every_document_source_actually_exists`, which now fails the build if any
non-`owner-confirmed` source stops resolving.

**`/setup-harness` wraps upstream `/setup`, it does not replace it.** Upstream
keeps ownership of the profile files (they are `[U]`). The wrapper owns the
order things happen in (CV first, then questions), the interview controls, the
evidence register, and the three capabilities upstream has no concept of:
preference profile, career review, companies of interest.

**Interview controls are a feature, not documentation** (owner directive,
plan-M 34). The command must *announce* "speed up" and "that's enough" at
interview start — a control the user is never told about does not exist — and
must never discard already-gathered answers when the interview ends early.
`--interview` resumes without re-asking. All four properties are asserted by
tests rather than left to prose.

**`/career-review` boundary.** Suggests, never writes. Accepted facts route
through `/fact` so they arrive with a source; rewordings touch templates only.
The report line `Register writes made by this command: 0` is asserted by a test.
Fetched pages are treated as untrusted data — a README instructing the agent to
rate the candidate as an expert is content to report, not an instruction to
follow.

**Two preference defaults that decide real outcomes**, both pinned by tests:

- `missing_compensation: keep`. Most postings state no pay; discarding them
  would throw away most of the market.
- `hard_skips[].mandatory_only`. A posting listing a skipped skill under
  "nice to have" must **not** be skipped, or transferable-fit candidates lose
  jobs they would have got. This is the half of the filter that is easy to
  implement wrongly and impossible to notice afterwards.

**`/companies` is a living list** (owner directive): researched proposals need
approval before landing, careers URLs are verified before recording, and a page
the harness cannot read is `unverified` — never "no openings". Those two get
confused constantly and they are different facts.

**Deferred, with reason: the live conversational onboarding run.** Running
`/setup-harness` for real writes candidate content into upstream's `[U]` profile
files, which the never-edit rule forbids in this repo. Per the decision recorded
in session 1, that run happens in a throwaway clone outside the repo, together
with the plan-L fresh-install test at P9 — which is where plan-K already
schedules the Onboarding E2E. Not a skip: mechanical halves are green now, and
the conversational half has a scheduled home.

Gate evidence: 33 onboarding tests, 81 harness tests total, 155 upstream tests,
lint clean at 17 commands, guards OK.

Next: P4 (intake + apply overlay).

---

## Close-out — what was built, in plain language

**The short version.** There is now a working, tested, private repository at
`github.com/WilliamEbong/job-search-agent-harness`. It is the open-source
job-search system described in the plan: it finds jobs, judges whether they are
worth applying to, writes the application, and refuses to let a claim through
that the candidate's own documents do not support. It runs in Claude Code and in
Codex. Nothing of yours is in it.

**What it actually does.** A user clones it, runs one command to install
everything, and answers some questions about their CV. Those answers become an
evidence register — a list of what that person may truthfully claim, with a
source recorded against every item. From then on, every CV and cover letter the
system writes is checked against that register by a program, not by a judgement
call. If a draft claims a certificate that is not finished, a number nobody
recorded, or a technology the person has not used, the package is blocked until
it is fixed. The rule the whole thing rests on is that a failing check is fixed
by correcting the draft, never by loosening the check.

**Your private system was never touched.** It was read once, through a
throwaway copy, which has since been deleted. Verified afterwards: its last
commit is still `e8c3e51` and its history is unchanged. The one modification
`git status` reports there is an Excel lock file that Excel itself removed long
before this build started — recorded here so nobody later blames Stage 3 for it.

**Test results.** 155 upstream tests and 194 harness tests pass. 157 more pass
across the six job-board CLIs. Four separate guards are green. The fabrication
test — the one that matters most — was run live: a fake certificate, an invented
statistic, and an overstated programming claim were planted in the demo CV, and
all seven planted claims were caught and blocked. The clean version passes.

Of the 40 end-to-end tests in the plan, 33 pass and 7 carry written waivers. All
seven waivers are the same kind of gap: they need either a live network call to
a real job board, a second person at a Codex terminal, or a physical screenshot.
None of them is a check that was skipped or weakened. The largest real gap is the
cross-runtime handoff drill (tests 27 and 28) — the code and state files are
there, but nobody has yet sat at two terminals and watched an application move
between them.

**Privacy sweep: zero hits.** Two separate guards enforce it — one checks the
structure (are the ignore rules intact, is anything personal committed), the
other reads the actual file contents looking for emails, phone numbers,
addresses and API keys. Both are clean, and both run in CI on every commit. The
only person-shaped content in the repository is Riley Chen, who is invented.

Worth flagging honestly: while wiring this up, the sweep found the live
Firecrawl configuration on this machine contains a personal API key embedded in
a URL. That key was deliberately not copied into the repository, and the setup
script was written to pass such keys by *name* rather than by value, so it never
reads or stores one.

**What still needs you.** Two things, both listed above as `[~]`: look at the
demo application package and say whether it looks right, and decide whether to
make the repository public. It is private now, which is the default the plan
recorded, and it stays that way until you say otherwise.

### Session notes — session 2

- Sessions 1 and 2 were the same conversation; the session-1 stop at P0.2 was a
  misread of the context budget, corrected by the owner. Recorded because the
  ledger showed a handoff that did not happen.
- Defects found and fixed during the build, each by fixing code or content and
  pinning a test — never by weakening a check: YAML folded-scalar corruption of
  the constraint regexes (caught before shipping); English words in the tech
  lexicon producing false red lines; claim-bearing numeral units missing from
  the whitelist; `.gitkeep` files wrongly flagged by the new guard; 71 required
  attribution URLs wrongly blocking the privacy sweep; a README rewrite breaking
  upstream's asset test.
- Personal data removed during ports, in each case replaced with demo
  equivalents: the author's name, phone, email and profile URLs hardcoded in
  `tex_to_md.py`; real employer names in the archiver's docstrings; the owner's
  city throughout the Canadian board CLI's examples.

---

## Post-review addendum — 2026-08-04

**Owner reviewed the demo package and asked a direct question: does it come with
the spreadsheet, does each job get its own folder, does that folder move to
`applied/` on confirmation, and does it hold the posting plus resume, cover
letter and combined document in Word, Markdown and PDF each?**

Checking honestly rather than answering from the design intent found **one real
gap**: the combined cover-letter-plus-resume document existed only as a merged
**PDF**. Its `.md` and `.docx` were never generated — `apply-any.md` specifies
all three, and the demo package had two. Fixed: the combined `.md` is now built
by concatenating the two mirrors with a raw-openxml page break, so pandoc emits
a genuine Word page break and the resume starts on its own page in the `.docx`
exactly as it does in the PDF.

Worth noting how this was missed: the packaging step had been *specified* and
*tested at the contract level* (a test asserts the command names all four
formats), but the combined document's non-PDF outputs had never been produced
end to end. A contract test that reads a document cannot notice a file that was
never written.

**The whole lifecycle was then run live rather than asserted:**

| Step | Result |
|---|---|
| Application folder created per job | `documents/applications/Rivermouth_Environmental_Data_Analyst/` |
| Tracker row written at draft time | `status=in_progress`, fit 82, empty `submitted_date` |
| Spreadsheet generated | `Job_Search_Tracker.xlsx`, 4 tabs, folder hyperlink resolved automatically |
| Shortlist populated | 3 rows: `qualified`, `gate-fail` (P.Eng, posting's own wording quoted), `not-resolved` (bot-walled page — *unverified*, not "no openings") |
| Search run logged | `run_log.csv` → Search Runs tab |
| `submitted_date` filled in | as if the user said "I applied" |
| Archiver run | folder **moved to `documents/applications/applied/`** |
| Final folder contents | posting (with link) + provenance + posting_source/ + resume, cover letter and combined document in **md, docx and pdf each** |

**Release gate: the owner chose to make the repository public.** Pre-flight
before flipping: `git status` clean, privacy sweep zero blocking hits, harness
guards green. The tracker CSV, the spreadsheet, the shortlist, the run log and
the entire `applied/` folder are all gitignored — they exist on this machine and
are invisible to git, which is the design working as intended.

Repository is now **public** at
https://github.com/WilliamEbong/job-search-agent-harness

---

## Post-review remediation (2026-08-04)

This file records the Stage-3 build and stops there. Everything after it — a
critical review, four remediation waves, and the verification the waves were
missing — lives in **`docs/REVIEW-HANDOFF.md`**, which is the file to read
next. In outline:

- **Waves 1–4** (`f1217d0`, `569e016`, `97ec275`, `2bdac2c`, `dcdb803`,
  `7136225`): data-loss and silent-corruption fixes in the archiver, tracker
  and fact checker; determinism via `harness/apply_package.py` and
  `harness/tracker_row.py`; `/today` as the daily driver; `/offer`, referrals,
  deadlines and conversion analytics.
- **W4 is discharged.** The clean-clone install (plan-M test 31) was run and
  timed; see `REVIEW-HANDOFF.md` §5. It found that a stranger's first
  `python setup.py` ended in failure, and that is fixed.
- **W2 is partly discharged.** Screenshot and PDF intake (tests 11 and 12) were
  run against a fixture; see §6. Live board runs (tests 6 and 8) were exercised
  against the public Canadian board only, which surfaced a silent
  location-filter fallback. LinkedIn stays unexercised by its own ToS.
- **W3 remains open.** The cross-runtime drills still need a human at a second
  terminal.
