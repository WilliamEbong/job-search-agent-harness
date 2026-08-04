# BUILD-STATE — Stage 3 (Opus builds)

**How to resume:** re-paste `docs/OPUS-KICKOFF.txt`. Read this file first, redo
nothing marked `[x]`, continue at the first `[~]` or `[ ]`. Contract:
`docs/IMPLEMENTATION-PLAN.md`. Phase specs: `docs/plan-G-phases.md`.

Legend: `[ ]` not started · `[~]` in progress · `[x]` done (+ commit) ·
`[!]` blocked/waived (reason in session notes).

---

## Phase checklist

### P0 — Bootstrap (repo + build machine)
- [ ] P0.1 Upstream `MadsLorentzen/ai-job-search` @ tag v1.3.0 merged into this git history; `upstream` remote added with push URL `DISABLED-never-push-to-upstream`
- [ ] P0.2 Hardened `.gitignore` (upstream model + harness families)
- [ ] P0.3 Private GitHub repo `job-search-agent-harness` created and pushed
- [ ] P0.4 Prereq installs: MiKTeX (lualatex+xelatex), poppler (pdftotext+pdfinfo), Bun, pandoc 👤
- [ ] P0.5 Caveman installed on both runtimes (build machine, owner directive); LICENCE verified MIT (plan-J J.1 row)
- [ ] P0.6 `requirements.txt` pinned (pyyaml, openpyxl, pypdf)
- [ ] P0.7 Gate: upstream `tests/` green; portal CLI `bun test` green; all engine `--version` probes resolve; `claude plugin list` + `codex plugin list` show caveman; CI green on private repo

### P1 — setup.py installer + doctor
- [ ] P1.1 `setup.py` (stdlib only): runtime detection, prereq checks, per-runtime plugin installs (Ponytail; Caveman optional w/ lite recommendation; optional Playwright + Firecrawl MCP), portal CLI deps, verify-every-step, doctor table
- [ ] P1.2 `tests_harness/test_setup_doctor.py` (mocked PATH probes)
- [ ] P1.3 Gate: fresh-clone `python setup.py` completes with honest doctor table on this machine

### P2 — Evidence layer (truth tier)
- [ ] P2.1 Read-only snapshot `../job-search-ref` created (`git clone --local`)
- [ ] P2.2 `evidence/register.example.yaml` (schema + demo-candidate entries)
- [ ] P2.3 `harness/fact_check.py` + `harness/fact_check_config.yaml`
- [ ] P2.4 Commands `fact.md`, `verify-facts.md`
- [ ] P2.5 `tests_harness/test_fact_check.py` (6 checks + 2 regression cases)
- [ ] P2.6 Gate: exit codes correct on fixtures; M-tests 16, 17 green

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
| 1–40 | see `docs/plan-M-e2e-tests.md` | not yet run | — |

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
