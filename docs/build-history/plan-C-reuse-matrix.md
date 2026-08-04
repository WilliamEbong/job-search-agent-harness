# C — Reuse Matrix

One line of justification per capability. Decisions: **reuse-upstream** (as
shipped, pinned v1.3.0) · **port-private** (sanitized mechanism from the scout
layer) · **install-dep** · **adapt** (upstream file + thin runtime shim) ·
**build-minimal** (new, smallest working) · **omit**.

| Capability | Decision | Justification |
|---|---|---|
| Apply pipeline (drafter→reviewer→compile→ATS) | reuse-upstream | Proven at 29.5k★ + live in private system; rebuilding is the anti-goal |
| PDF compile + inspect + verify_pdf | reuse-upstream | Works; poppler is the only extra prerequisite |
| `/add-portal`, `/add-template`, `/expand`, `/setup`, `/rank`, `/outcome`, `/interview`, `/reset`, `/html-report` | reuse-upstream | Complete, tested, licence-clean |
| `/gmail-sync`, `/notion-sync` | reuse-upstream (optional) | Ship as upstream does; MCP-dependent features stay opt-in |
| Upstream tests + CI + lint_skills + check_framework_version | reuse-upstream | Never touched privately either; keep green |
| security_guards.py | adapt | Extend allowlist/gitignore guard to harness paths (evidence/, preferences, state/, shortlist) — CI privacy guard per doc 01 §12 |
| check_upstream_updates.py | reuse-upstream + document | Not tag-aware (R1); harness documents the drilled tag-merge ritual around it |
| Evidence register schema | port-private | 14-section schema with `source:` invariant is the deterministic tier's foundation; personal entries excluded, demo candidate entries substituted |
| fact_check.py (6 check classes) | port-private + generalize | Proven incl. two root-fixed defects; TECH_LEXICON + constraint patterns move to config so they're candidate-agnostic |
| `/fact` writeback, `/verify-facts`, `/tracker`, `/apply-any` | port-private | Already runtime-neutral markdown; smallest possible port |
| posting-intake skill (6-rung ladder) | port-private | Doc 01 §5's intake ladder exists, built and refined; only MCP names go through RUNTIME-MAP |
| Hard-constraint gate + autonomy ladder | port-private + generalize | Becomes the preference engine's enforcement half (exclusions, hard skill-skips, modes thresholds) |
| tracker_xlsx.py (4 tabs) | port-private | Doc 01 §8's owner view, already built incl. Summary funnel + Search Runs; regenerate-only model preserved |
| archive_applications.py + shared folder-matcher | port-private | applied/-move + 8-week zip proven; single matcher prevents link drift |
| run_log.py | port-private | 14 lines; feeds Search Runs tab |
| tex_to_md.py + quad-format package | port-private | Drift-proof .md mirror + .docx via pandoc (soft dep, R4) |
| BUILD-STATE/handoff ritual | port-private + formalize | Becomes state/session-log.md + state/HANDOFF.md + `/continue` (doc 01 §10); paste-ready continuation prompt pattern kept |
| jobbank-ca-search CLI | port-private | ToS-clean (robots verified, 5s crawl-delay enforced); becomes the shipped local-board example |
| Danish portal CLIs | reuse-upstream | Stay as pattern examples per doc 01 §4 |
| Board intelligence + LaTeX gotchas | port-private (as docs) | Hard-won operational knowledge; zero code |
| Preference engine (preferences.yaml + conversational collection) | build-minimal | Doc 01 §3D; reuses private question set (sanitized) + upstream setup's interview pattern; no form framework |
| Usage modes (focused/balanced/full + cost posture) | build-minimal | Doc 01 §7; nothing upstream; config + command prose, no scheduler |
| Location-aware board research step | build-minimal | Doc 01 §4; thin research step feeding upstream `/add-portal` |
| Template inference (prior resume → LaTeX template) | build-minimal | Doc 01 §3C; bounded step feeding upstream `/add-template`; pixel-perfect cloning explicitly not promised |
| Open-job validation | build-minimal | Best-available signals + `unverified` marking; posting archived at apply-time (already in intake) |
| setup.py installer + doctor | build-minimal | Doc 01 §2; upstream has only manual SETUP.md |
| Continuity telemetry (statusline mirror script) | build-minimal | Only mechanism that exists (B.4); hooks can't, Codex can't |
| Demo candidate + fixtures | build-minimal | Powers install test, CI, screenshots; privacy prerequisite for a public repo |
| RUNTIME-MAP.md + .codex stubs + AGENTS.md completion | build-minimal | Completes upstream's existing portability seam; differences only (deliverable F) |
| Humanizer | install-dep (vendored skill) | MIT; vendor SKILL.md + voice calibration; Codex fallback inline checklist |
| Ponytail | install-dep (per-runtime at setup) | Verified install commands both runtimes |
| Caveman | install-dep (OPTIONAL for users: setup explains + recommends lite; P0 on build machine per owner directive) | Verified install commands both runtimes; one flag disables |
| Onboarding interview controls (speed-up / end / revisit) | build-minimal | Owner directive: built-in feature of the CV interview, not documentation; revisit via `setup --interview` |
| Career review (portfolio/website/GitHub → CV improvement suggestions) | build-minimal (extends upstream `/expand`) | Owner directive; `/expand` already mines public presence with provenance — the review adds suggest-changes output, never auto-edits the CV or register |
| Companies-of-interest engine (list build + company search) | build-minimal | Owner directive; list = user input + researched proposals (CV + location driven); search via WebSearch/Firecrawl per RUNTIME-MAP, no custom scrapers |
| Search scopes (specific boards / specific company / all companies / all boards / everything) | build-minimal | Owner directive; extends the usage-mode wrapper's board selection |
| USER-GUIDE.md (root) | build-minimal (docs) | Owner directive: top-level guide to all features and usage |
| Playwright MCP | install-dep (optional) | Both runtimes support MCP; degrade to plain fetch + `unverified` |
| Firecrawl MCP | install-dep (optional; owner directive) | Keyless tier verified; intake escalation + non-CLI board extraction; degrades cleanly |
| openpyxl, pyyaml, pypdf | install-dep | Python already required; requirements.txt introduced (upstream has none) |
| pandoc | install-dep (soft) | .docx output only; doctor reports absence, feature degrades |
| context7 / Toolshelf / Toolbelt / ecc / superpowers | omit (product) | Dev-time only; users never need them (B.3) |
| Indeed connector | omit (core) / document | Owner-personal claude.ai connector; not portable or zero-config |
| Typst engine | omit | R3: no engine anywhere, LaTeX is the tested path |
| Databases, vector stores, dashboards beyond html-report, event buses, schedulers, auto-submit | omit | Doc 01 §13 deliberately-absent list stands; nothing found in inspection argues otherwise |
