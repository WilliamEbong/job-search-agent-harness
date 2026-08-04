# G — Implementation Phases (P0–P10)

Each phase: objective · inspect/create/modify · dependencies · tests ·
acceptance (mechanical gate; green = auto-continue) · rollback. 👤 marks owner
moments (the only ones allowed, per handoff §3). "Snapshot" = a fresh
read-only `git clone --local ../job-search ../job-search-ref` made at P2 start
and deleted at P9 end; Opus ports mechanisms from it, never personal content.

## P0 — Bootstrap (repo + build machine)
- **Objective:** working skeleton on the pinned upstream; build machine able to compile and test everything.
- **Create/modify:** clone `MadsLorentzen/ai-job-search` at tag **v1.3.0** into this repo's git history (upstream remote added with push URL `DISABLED-never-push-to-upstream`); private GitHub repo `job-search-agent-harness` (👤 none — `gh repo create --private`); hardened `.gitignore` (upstream model + harness families); baseline CI run; installs: **TeX (MiKTeX: lualatex+xelatex), poppler, Bun, pandoc; Caveman on both runtimes (owner directive)** 👤 Windows permission clicks.
- **Deps:** gh authenticated; network.
- **Tests:** upstream `tests/` green locally; portal CLI `bun test` green; `lualatex --version`, `xelatex --version`, `pdftotext -v`, `bun --version`, `pandoc --version` all resolve; `claude plugin list` + `codex plugin list` show caveman.
- **Acceptance:** CI green on the private repo; doctor-style check script passes.
- **Rollback:** delete repo, re-clone; installs are idempotent.

## P1 — setup.py installer + doctor
- **Objective:** doc 01 §2 one-command setup: detect runtimes on PATH, check/guide prerequisites (Python, Bun, TeX, poppler, Node; pandoc soft), offer per-runtime installs (Ponytail, Caveman, optional Playwright MCP, optional Firecrawl MCP), install portal CLI deps (`bun install` per dir), verify every step (list plugins after install, compile a test PDF, never assume), end with doctor table.
- **Create:** `setup.py` (stdlib only), doctor output.
- **Tests:** `tests_harness/test_setup_doctor.py` (mocked PATH probes); live run on this machine.
- **Acceptance:** fresh-clone → `python setup.py` completes with an honest doctor table on this machine (all green after P0).
- **Rollback:** setup is additive/idempotent; failed step reports and continues where safe.

## P2 — Evidence layer (truth tier)
- **Objective:** doc 01 §6 deterministic tier, candidate-agnostic.
- **Create:** `evidence/register.example.yaml` (schema from snapshot, demo-candidate entries); `harness/fact_check.py` (port; TECH_LEXICON + constraint/marker patterns moved to `harness/fact_check_config.yaml`); commands `fact.md`, `verify-facts.md` (port, path updates only); `tests_harness/test_fact_check.py` (port the 6 tests + fixtures, demo-candidate versions, incl. the two regression cases).
- **Deps:** P0 (poppler for the pdftotext input path).
- **Tests:** planted fake credential blocked; planted unregistered metric blocked; clean fixture passes; in-progress credential without qualifier blocked; writeback round-trip works with backup.
- **Acceptance:** `python harness/fact_check.py` exit codes correct on fixtures; gate wired into apply path doc; **no failure resolvable by weakening a check (bounded repair rule active from here on).**
- **Rollback:** layer is additive; revert commit.

## P3 — Onboarding (evidence bank + preference engine + templates)
- **Objective:** doc 01 §3 complete.
- **Create/modify:** extend `/setup` via a harness wrapper command (upstream setup.md untouched): documents→register build with `source:` tags, preference interview (question set harvested from snapshot, sanitized: compensation incl. missing-comp rule, location/commute/relocation, driving-only-if-plausible, exclusions free-text→structured, remote trade-offs asked never assumed, hard skill-skips with mandatory-vs-preferred preserved, role families/seniority/type/authorization/industries/direction; skip questions documents already answer) → `preferences.yaml` + `preferences.example.yaml`; template choice: stock · prior-resume→**template-inference** (bounded: reconstruct maintainable LaTeX structure — sections/hierarchy/spacing/bullets/length — then feed upstream `/add-template` which test-compiles; no pixel-perfect promise) · user-supplied→`/add-template`.
- **Tests:** demo-candidate onboarding produces valid register+preferences (YAML parse + schema check); template-inference on a demo PDF produces a compiling template.
- **Acceptance:** demo onboarding end-to-end on Claude lane; register entries all carry `source:`.
- **Rollback:** revert; user files gitignored anyway.

## P4 — Intake + apply overlay
- **Objective:** doc 01 §5 pipeline complete.
- **Create:** `posting-intake` skill (port; MCP names via RUNTIME-MAP); `apply-any.md` (port); humanizer vendored skill + voice-calibration note from writing samples; quad-format package (`tex_to_md.py` port, pandoc soft, pypdf combine); archive layout (posting_source/, provenance.md, job_posting.md); hard-constraint gate + autonomy ladder generalized to read `preferences.yaml`; **post-humanize re-ground rule** (any wording change → recompile + `/verify-facts`).
- **Deps:** P2 (gate), P3 (preferences).
- **Tests:** URL/paste/PDF/screenshot fixtures resolve with correct provenance; expired posting → `unverified`; humanize-then-reground test (humanizer output altered → gate re-runs); package contains all formats; ATS text-layer check passes on demo output.
- **Acceptance:** demo candidate `apply <fixture>` produces a complete, fact-gated, humanized package on Claude lane.
- **Rollback:** revert; upstream `/apply` untouched throughout.

## P5 — Discovery (modes + boards)
- **Objective:** doc 01 §4 + §7.
- **Create:** usage modes in `preferences.yaml` (`focused` default / `balanced` / `full` with `max_evaluations`, `max_packages_per_run`) + per-run overrides `--board/--limit/--mode` + **cost-posture line printed before every run** (qualitative, no fabricated token math); port `jobbank-ca-search`; location-aware step: user location → research ≤3 reputable local boards → propose → upstream `/add-portal` (which handles robots/ToS, scaffold, live-test); open-job validation (live fetch/closure text/expiry; unverifiable → `unverified`, archived at apply time); wire shortlist verdicts + run_log.
- **Tests:** mode caps respected (fixture run); cost-posture line present; jobbank-ca CLI tests green (ported suite); closed-job fixture rejected.
- **Acceptance:** `/scrape` in focused mode on one board yields ranked jobs + run-log row on Claude lane.
- **Rollback:** revert; board CLIs independent.

## P6 — Tracking
- **Objective:** doc 01 §8.
- **Create:** port `tracker_xlsx.py` (4 tabs), `archive_applications.py` (+ shared matcher), `run_log.py`, `tracker.md` command (fix the stale "three tabs" self-test text found in the snapshot); backup-before-rewrite rule.
- **Tests:** ported test suites (21 tests) green with demo fixtures; regenerate-twice idempotence; note-preservation (regenerate cannot lose CSV notes).
- **Acceptance:** demo tracker CSV → workbook with 4 correct tabs, hyperlinks, splits.
- **Rollback:** views regenerate-only; zero data-loss surface.

## P7 — Continuity engine
- **Objective:** doc 01 §10 first-class.
- **Create:** `state/session-log.md` + `state/HANDOFF.md` writers (milestone ritual in command docs), `/continue` command + `.codex/prompts/continue.md`; `harness/telemetry_statusline.py` + statusline registration in setup (Claude lane; caveats documented); Codex fallback cadence per RUNTIME-MAP §5.
- **Tests:** kill-and-resume drill: interrupt mid-apply, `continue` in fresh session resumes at exact next step redoing nothing; cross-runtime drill deferred to P8.
- **Acceptance:** interrupted-session recovery passes on Claude lane.
- **Rollback:** state files additive.

## P8 — Runtime adapters + live Codex lane
- **Objective:** doc 01 §9 complete; Codex verified live (R5).
- **Create/modify:** final `RUNTIME-MAP.md`; `.codex/prompts/` stubs; AGENTS.md harness pointers (managed block); Codex MCP config guidance.
- **Tests (live, Codex 0.144.6):** `continue` ritual; `apply <fixture>` full pipeline with sequential-fresh-pass reviewer; humanizer `@`-invocation (fallback checklist if it fails — resolves the UNVERIFIED); plugin installs verified; Claude→Codex and Codex→Claude continuation drills.
- **Acceptance:** demo package produced on Codex lane; both cross-runtime drills pass.
- **Rollback:** adapters are additive files.

## P9 — Demo candidate, E2E matrix, privacy guard
- **Objective:** everything provable; repo shippable.
- **Create:** `documents/demo/` fictional inputs; `examples/`; `tools/harness_guards.py` (extends security_guards model to harness families) + `harness/privacy_sweep.py`; CI jobs; run full **deliverable M** test list; fresh-install test (deliverable L). Delete `../job-search-ref` at phase end.
- **Acceptance:** all M tests green or explicitly waived with reason; privacy sweep zero hits; CI green.
- **Rollback:** n/a (tests).

## P10 — Docs + release gate
- **Objective:** README-quality manual, attribution, ship decision.
- **Create:** README (attribution front-and-center), NOTICE.md (deliverable J text), owner guide update, board-intelligence + latex-gotchas docs.
- 👤 **Owner moments:** demo-candidate package eyeball ("package looks right"); release gate — privacy-sweep results shown, "flip public?" (default: stay private until yes).
- **Acceptance:** doc 03 "How you know it's done" list satisfied; repo public (or private by choice).
- **Rollback:** repo stays private.

**Standing rules for every phase:** BUILD-STATE.md ritual (`[~]` start, `[x]`+commit end, append-only session blocks); bounded repair rule (a failing check is fixed in code or content, never by weakening the check); stopping conditions = handoff §4 list; `../job-search` is never opened for write; ponytail ladder on all new code; ecc hooks (GateGuard) will fire on file creation — present facts and retry, never disable guards to save time.
