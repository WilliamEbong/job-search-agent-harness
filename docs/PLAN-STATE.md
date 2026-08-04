# PLAN-STATE — Stage 2 (Fable Plan Mode) resumability checklist

**How to resume:** re-paste the kickoff from harness-02 §5. Read this file, skip
every `[x]`, continue at the first `[~]`/`[ ]`. Approved plan (decisions + findings):
`~/.claude/plans/read-docs-harness-01-architecture-md-and-abstract-garden.md`.

## Session facts (verified 2026-08-03)
- Inspection complete via 3 read-only audits: private system as-built,
  installed capabilities, upstream/external ground truth.
- Codex IS installed (codex-cli 0.144.6) → live Codex test lane.
- Upstream v1.3.0 released 2026-08-03 → pin target.
- Owner directives at plan review: install Caveman during Stage-3 build (both
  runtimes); Firecrawl is part of the harness (optional MCP, keyless-degraded,
  overrides doc 01 §11 omit).
- Owner directives mid-execution (2026-08-03, baked into B/C/E/F/G/H/M/N + O):
  Caveman OPTIONAL for users — setup explains it, recommends lite mode ·
  root USER-GUIDE.md covering all features · CV-first onboarding interview
  with built-in speed-up/end controls + revisit (`setup --interview`) ·
  career review of portfolio/website/GitHub → CV improvement suggestions
  (suggestions only, no auto-writes) · companies-of-interest list
  (user input + researched: big + local companies hiring the user's skill
  set, CV/location-driven, each entry user-approved) + company-of-interest
  search of those companies' boards/career pages · five search scopes:
  specific board(s) / specific company(ies) / all companies / all boards /
  everything.
- Plan approved by owner 2026-08-03.

## Checklist
- [x] Snapshot ../job-search-ref created (git clone --local, personal branch)
- [x] git init + docs baseline commit
- [x] PLAN-STATE.md (this file)
- [x] A  plan-A-current-system-audit.md
- [x] B  plan-B-capability-audit.md
- [x] C  plan-C-reuse-matrix.md
- [x] D  plan-D-repo-structure.md
- [x] E  plan-E-state-model.md
- [x] F  plan-F-RUNTIME-MAP-draft.md
- [x] G  plan-G-phases.md
- [x] H  plan-H-file-responsibilities.md
- [x] I  plan-I-dependency-pinning.md
- [x] J  plan-J-licensing-NOTICE.md
- [x] K  plan-K-test-matrix.md
- [x] L  plan-L-fresh-install-test.md
- [x] M  plan-M-e2e-tests.md (40 tests incl. owner-directive additions 34–40)
- [x] N  plan-N-simplification-audit.md (cuts applied back to D/G/H)
- [x] O  IMPLEMENTATION-PLAN.md + OPUS-KICKOFF.txt
- [x] Privacy sweep of all written docs (grep for owner name/email/private
      URL/location identifiers: zero hits)
- [x] Delete ../job-search-ref
- [x] Plain-language owner summary (delivered in chat at session close)

**STAGE 2 COMPLETE 2026-08-03.** Next: owner runs Stage 3 per
harness-03-owner-guide.md (switch model to Opus, Plan Mode OFF, paste
docs/OPUS-KICKOFF.txt).
