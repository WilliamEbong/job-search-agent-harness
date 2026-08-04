# IMPLEMENTATION-PLAN — Stage-3 build contract (for Opus)

**Plain-language summary (owner, this page is the skim):** Opus builds a
public, MIT-licensed job-search harness in THIS folder, on top of the
open-source ai-job-search project (pinned at its newest release v1.3.0),
porting the proven mechanisms from your private system in sanitized form.
Your private `..\job-search` is never touched — a throwaway read-only copy is
used and deleted. Truth checks are deterministic and can never be weakened to
make something pass. Nothing personal ships: a fictional demo candidate powers
all tests. Your requested features are in: guided CV interview you can speed
up, end, or revisit; portfolio/GitHub career review with CV suggestions;
companies-of-interest lists and company searches; five search scopes;
optional Caveman (explained at setup, lite recommended); a USER-GUIDE at the
repo root. You are needed only for: Windows permission clicks during
installs, one look at the demo application package, and the final "flip
public?" decision. An interrupted build resumes from its progress file with
the same paste.

## 1. The contract

1. **Read first, in order:** this file → `plan-G-phases.md` (binding phase
   specs) → `plan-D-repo-structure.md`, `plan-E-state-model.md`,
   `plan-F-RUNTIME-MAP-draft.md`, `plan-H-file-responsibilities.md`,
   `plan-I-dependency-pinning.md`, `plan-J-licensing-NOTICE.md`,
   `plan-K-test-matrix.md`, `plan-L-fresh-install-test.md`,
   `plan-M-e2e-tests.md`, `plan-N-simplification-audit.md` (its cuts are
   binding) → `plan-A-…`, `plan-B-…` for evidence context.
   `harness-01-architecture.md` is the architecture; the plan-* docs are its
   reconciliation with inspected reality and **win where they differ** (every
   difference is evidence-logged in plan-A §A.5 and PLAN-STATE).
2. **Decided architecture:** doc 01 §§1–13 as reconciled, plus the owner
   directives recorded in PLAN-STATE (Firecrawl included; Caveman optional
   with lite recommendation; onboarding interview controls; career review;
   companies of interest + company search; five search scopes; USER-GUIDE).
   Priority order (doc 01 header) governs every conflict.
3. **Never-edit list:** `..\job-search` (the private system — read-only
   snapshot `..\job-search-ref` only: create at P2 start, delete at P9; never
   copy personal content out of it) · all files marked [U] in plan-D
   (upstream-owned; changes arrive only via the plan-I tag-merge ritual) ·
   `.claude/settings.json` (guard-frozen; local permissions go in
   `settings.local.json`) · the three Stage-1 docs and the plan-* set (record
   divergences in BUILD-STATE, don't edit plans).
4. **Phases:** execute P0→P10 exactly as `plan-G-phases.md` specifies. Each
   phase ends with its mechanical gate. **Green = auto-continue, no asking.**
   Red = bounded repair.
5. **Bounded repair rule:** a failing check is fixed in code or content,
   **never by weakening the check** — not by loosening a fact-check pattern,
   skipping a test, widening an allowlist, editing the register to clear a
   red line, or presenting "with a note". If a check itself is provably
   wrong, fix the check AND pin a regression fixture demonstrating the old
   defect. Three failed repair attempts on one gate → stop and write the
   situation to BUILD-STATE in plain language.
6. **BUILD-STATE ritual:** maintain `docs/BUILD-STATE.md` — `[~]` when a
   sub-step starts, `[x]` + git commit when it completes; append-only
   session blocks; record every deviation, defect, decision, waiver with
   reasons. On a fresh session with the same kickoff: read BUILD-STATE, redo
   nothing `[x]`, continue at the first `[~]`/`[ ]`.
7. **Stopping conditions (halt and surface, never improvise past):** a write
   to the private system would be needed · personal data is about to enter
   the repo · upstream reality contradicts the plan on something load-bearing
   (quote it) · a truth/privacy check would need weakening · a licence
   conflict appears · three failed repairs on one gate.
8. **Owner touchpoints (👤, the ONLY ones):** Windows permission clicks
   during P0/P1 installs · demo-candidate package eyeball at P10 · release
   gate "flip public?" at P10 (default: stay private) · optional Codex-side
   smoke observation. Batch everything non-blocking into BUILD-STATE notes.
9. **Working discipline:** Ponytail ladder on all new code; surgical diffs;
   ECC GateGuard hooks will demand facts before file creation — present them
   and retry; never disable a guard to save time. Caveman (installed on this
   machine at P0) applies to internal chatter only — NEVER to application
   prose, README/USER-GUIDE, or any deliverable text.
10. **Definition of done:** all P0–P10 gates green · full `plan-M` matrix
    (tests 1–40) green or explicitly waived with written reasons ·
    fresh-install test (plan-L) passes incl. the planted-fake fabrication
    block · privacy sweep zero hits · `..\job-search-ref` deleted ·
    NOTICE/README attribution + USER-GUIDE in place · owner saw the demo
    package and answered the release-gate question · BUILD-STATE closes with
    a plain-language summary.

## 2. Session management

At every milestone: update BUILD-STATE and commit. If the context-usage hook
line appears or work quality degrades: finish the current sub-step, commit,
refresh BUILD-STATE, and note that a fresh session with the same kickoff
resumes losslessly. Never let a session die mid-sub-step silently.
