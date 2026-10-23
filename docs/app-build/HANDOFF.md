# Handoff: Candor desktop app

**Where things stand (2026-10-23).** Built and verified on branch `feat/desktop-app`.
Candor is a double-click Windows app over the harness: a Python standard-library server
(`app/server.py`) on 127.0.0.1:8770, vanilla ES-module screens (`app/static/`), an
app-window launcher (`app/launcher.py`) and an installer (`Install Candor.cmd` →
`app/install.ps1`). AI work runs the person's own `claude` or `codex` CLI headless
through a one-at-a-time queue (`app/tasks.py`, `app/engines.py`); job search runs
`harness/lite_search.py` directly with no AI.

## Run it

- App window: `python -m app.launcher` (or double-click `Candor.cmd`).
- Server only, for development: `python -m app.server --port 8771 --no-browser`.
- Tests: `python -m unittest discover -s tests_app -t .` (24), plus the existing
  `tests_harness` (461) and `tests` (154) suites and `tools/*_guards.py`.

## Contracts and docs

- API between server and screens: `docs/app-build/API.md`.
- Product truth: `PRODUCT.md`. Design system: `DESIGN.md` + `.impeccable/design.json`.
  Direction contract: `.impeccable/surfaces/app-static-index-html.md`.
- Decisions and why: `docs/app-build/SESSION-LOG.md`. Plan and Later list:
  `docs/app-build/BUILD-PLAN.md`.

## Gotchas

- Windows Python writes CRLF with `open(..., "w")`; the repo is LF. Write with
  `newline=""` or normalise (`sed -i 's/\r$//'`).
- `.gitignore` ignores `*.png`/`*.jpg` (personal photos) and the guards forbid negations,
  so shipped images are `.webp` (`docs/media/`).
- The Playwright MCP browser profile was locked by another session's Chrome; screens
  were verified in the built-in browser pane and with a headless CDP script
  (`scratchpad/shoot.mjs`, outside the repo).
- Claude runs use `--setting-sources project,local` so the person's global hooks and
  plugins don't load; Codex gets network only per run via `-c`.
- A task that ends with "?" becomes `question`; any finished agent task with a session
  accepts a reply (`can_reply`).

## Local demo state (gitignored, made during this build)

`preferences.yaml` (from the example, mode lite), `state/lite-last-search.json`
(11 synthetic jobs), one gate-fail row in `shortlist.csv`, `documents/postings/demo-posting.md`,
and a real package made by a live Codex run: `documents/applications/Lakeshore_Water_Authority_Water_Quality_Data_Coordinator/`
plus its tracker row and `cv/`, `cover_letters/` sources. Delete them to see the
first-run wizard.

## Not verified

- `Install Candor.cmd` was syntax-checked, never executed (it installs software).
- The API-key sign-in warning was not captured (no API-key login on this machine).
- macOS paths in the launcher are untested.
