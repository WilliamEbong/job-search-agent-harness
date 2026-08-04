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
- Plan approved by owner 2026-08-03.

## Checklist
- [x] Snapshot ../job-search-ref created (git clone --local, personal branch)
- [x] git init + docs baseline commit
- [x] PLAN-STATE.md (this file)
- [x] A  plan-A-current-system-audit.md
- [x] B  plan-B-capability-audit.md
- [ ] C  plan-C-reuse-matrix.md
- [ ] D  plan-D-repo-structure.md
- [ ] E  plan-E-state-model.md
- [ ] F  plan-F-RUNTIME-MAP-draft.md
- [ ] G  plan-G-phases.md
- [ ] H  plan-H-file-responsibilities.md
- [ ] I  plan-I-dependency-pinning.md
- [ ] J  plan-J-licensing-NOTICE.md
- [ ] K  plan-K-test-matrix.md
- [ ] L  plan-L-fresh-install-test.md
- [ ] M  plan-M-e2e-tests.md
- [ ] N  plan-N-simplification-audit.md (runs over C–M before O)
- [ ] O  IMPLEMENTATION-PLAN.md + OPUS-KICKOFF.txt
- [ ] Privacy sweep of all written docs (zero personal strings)
- [ ] Delete ../job-search-ref
- [ ] Plain-language owner summary
