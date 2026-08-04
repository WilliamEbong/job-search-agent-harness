# H — File-Level Responsibilities (harness-owned files only)

Upstream files keep upstream responsibilities (see D for ownership). One line
per harness file; phase = where it lands.

| File | Responsibility | Phase |
|---|---|---|
| `setup.py` | Detect runtimes/prereqs, guided installs, per-runtime plugin installs, portal CLI deps, verify each step, doctor table | P1 |
| `requirements.txt` | Pin pyyaml, openpyxl, pypdf | P0 |
| `harness/fact_check.py` | Tier-1 deterministic checker; 6 check classes; exit code = red lines; judges facts never phrasing | P2 |
| `harness/fact_check_config.yaml` | Candidate-agnostic tech lexicon, constraint patterns, exemption markers | P2 |
| `harness/tracker_xlsx.py` | Regenerate-only 4-tab workbook from tracker CSV + shortlist + run log | P6 |
| `harness/archive_applications.py` | applied/-move on submitted_date, 8-week zip, shared `match_folder()` | P6 |
| `harness/run_log.py` | Append one search-run row | P5 |
| `harness/tex_to_md.py` | Drift-proof .md mirror of generated .tex (pandoc source for .docx) | P4 |
| `harness/telemetry_statusline.py` | Claude statusline → `state/telemetry.json` mirror (context %, 5h/7d %) | P7 |
| `harness/privacy_sweep.py` | Scan tree for personal-data families before release; release-gate + CI | P9 |
| `tools/harness_guards.py` | CI guard: gitignore families intact, no un-allowlisted negations, harness paths untracked | P9 |
| `evidence/register.example.yaml` | Documented register schema + fictional demo entries | P2 |
| `preferences.example.yaml` | Documented preference schema incl. usage modes + caps | P3 |
| `.claude/commands/apply-any.md` | Multimodal intake wrapper → upstream /apply → humanize → re-ground → package → track | P4 |
| `.claude/commands/verify-facts.md` | Run fact gate on final text; 3 legal resolutions; forbids weakening | P2 |
| `.claude/commands/fact.md` | Sole register writeback path (backup → write with source → mirror → tests) | P2 |
| `.claude/commands/tracker.md` | Regenerate workbook + run archiver (backup-first) | P6 |
| `.claude/commands/continue.md` | Bootstrap ritual: AGENTS.md → HANDOFF.md → git/filesystem → resume | P7 |
| `.claude/commands/scrape.md` | ONE wrapper: usage modes + cost posture + per-run overrides around upstream scraping (N-audit cut #1) | P5 |
| `.claude/commands/setup-harness.md` | Onboarding wrapper: evidence bank build + conversational preference interview + hard-constraint/autonomy generalization + template choice (N-audit cut #2 — no separate skill) | P3 |
| `.claude/skills/posting-intake/SKILL.md` | 6-rung intake ladder, provenance, quality gate, `unverified` marking | P4 |
| `.claude/skills/humanizer/SKILL.md` | Vendored MIT skill + voice calibration + never-add-a-fact rule | P4 |
| `.codex/prompts/*.md` | Thin per-workflow stubs pointing at shared command md + RUNTIME-MAP | P8 |
| `RUNTIME-MAP.md` | The only place adapters diverge (from deliverable F) | P8 |
| `AGENTS.md` (harness block) | Thin pointers: workflows, RUNTIME-MAP, state/, evidence/ | P8 |
| `NOTICE.md` | Attribution text (deliverable J) | P10 |
| `README.md` | Product intro, quickstart, attribution front-and-center | P10 |
| `docs/board-intelligence.md` | Ported operational board knowledge (sanitized) | P5 |
| `docs/latex-gotchas.md` | Ported compile gotchas (fontspec cwd, @@key@@, \mbox{}) | P4 |
| `documents/demo/` + `examples/` | Fictional demo candidate inputs + example outputs | P9 |
| `state/` (generated) | session-log.md, HANDOFF.md, telemetry.json — continuity spine | P7 |
| `tests_harness/*` | Ported + new test suites (fact check, tracker, archiver, intake, setup, privacy) | P2–P9 |
