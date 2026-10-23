# Build plan: the desktop app

**Goal.** Turn the job-search agent harness into a double-click desktop app that a
non-technical job seeker can install, understand and use without a terminal or a chat
window, at least at Qualia's level of maturity and UX (`Documents/Qualia`). It runs on
the person's own Claude or Codex subscription; long agent loops run in Codex where it
is installed.

## Deepened brief

1. **What a professional adds.** A first-run wizard that checks the engine before
   anything else (the commonest failure is "Codex/Claude not installed or not signed
   in"); forms instead of chat for the five setup questions; plain-language errors with
   a next step; empty states on every screen; a live progress view for agent runs with
   a way to answer the agent's question and to cancel; one-at-a-time task lock so two
   runs never fight over the same files; keyboard focus and 40px targets; nothing ever
   submitted to an employer.
2. **Rawest material.** The harness scripts themselves (`harness/today.py --json`,
   `lite_search.py`, tracker CSV, shortlist CSV, `preferences.yaml`,
   `evidence/register.yaml`, application folders), the lite workflow files, the real
   `claude` 2.1.303 and `codex` 0.160.0 CLIs on this machine, Qualia's launcher and
   installer.
3. **Methods.** Python stdlib server (no new dependency), vanilla ES-module front end
   (no build step), Qualia's app-window launcher pattern, impeccable for design,
   Playwright for proof, a fresh-context reviewer at the end.
4. **Acceptance checks** (the definition of done):
   - A1 `python -m unittest discover -s tests_app -t .` passes (server API, path
     confinement, prompt building, engine resolution, task lifecycle with a fake engine).
   - A2 Existing suites still pass: `tests_harness`, `tests`, `tools/harness_guards.py`.
   - A3 Playwright: every screen renders on the demo candidate (Riley Chen) at 1440 and
     390 wide, with no console errors; the first-run wizard renders on an empty profile.
   - A4 A real agent run through the app (a short status/ask task) completes on the
     installed CLI and streams progress into the UI.
   - A5 `python app/launcher.py` opens the app window and the server stops when idle.
   - A6 Fresh-context reviewer findings fixed; impeccable detector run once.
   - A7 No personal data committed; privacy guards pass.

## Steps

| # | Step | Status |
|---|---|---|
| 1 | Study harness, Qualia, CLIs | done |
| 2 | PRODUCT.md, design direction (impeccable) | done |
| 3 | Server: state readers, files, settings, deterministic actions | done |
| 4 | Agent runner: Claude/Codex adapters, tasks, streaming, reply, cancel | done |
| 5 | Front end: shell, wizard, Today, Jobs, Apply, Applications, Profile, Settings | done |
| 6 | Launcher, installer `.cmd`, desktop shortcut | done (installer not executed) |
| 7 | Tests (A1, A2) | done: 22 app tests, 461 harness, 154 upstream |
| 8 | Browser pass (A3), live agent run (A4), launcher (A5) | done (live Codex apply: full package in 7 min) |
| 9 | Review, DESIGN.md, docs (README, USER-GUIDE section) | done |
| 10 | Commit, merge to main, push | done |

## Later (not built)

- Packaged release ZIP / signed installer like Qualia's GitHub release.
- Tutorial videos and an online read-only demo.
- Gmail/Notion sync, salary lookup and career review as app screens (they stay
  available through "Ask the assistant").
- macOS app bundle (launcher already finds Edge/Chrome on macOS; untested).
