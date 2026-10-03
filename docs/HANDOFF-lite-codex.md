# Handoff - lite mode, recruiter pass, ATS check, Codex (2026-10-02)

Branch `feat/lite-mode-codex-recruiter-ats`, pushed, **not merged**: `main` is untouched
(branch-first rule). 16 commits on the branch, 95 files, about +4.7k / -0.7k lines.
Read this first in a new session; `docs/REVIEW-HANDOFF.md` remains the long-form record of
the conventions.

## What the owner asked for

1. Make the system work in Codex (ChatGPT).
2. An ultra lite mode: highly token-efficient, core features only (search and package
   drafting), quick onboarding, a fraction of the standard token cost, taking full
   advantage of Ponytail, Caveman and i-have-adhd.
3. Make sure ATS matching is done.
4. One of the first onboarding steps acts as a recruiter and names the 20 positions the
   user's CV fits.
5. Setup walks the user through the options and recommends lite below ChatGPT Pro /
   Claude Max.
6. Commit and push; then review for issues and inefficiencies.

It is a general tool. All demo data is the fictional candidate Riley Chen; nothing is
built from the owner's own CV or job search.

## What exists now

| Piece | Where | Notes |
|---|---|---|
| Lite router | `.claude/commands/lite.md` (3.8 KB) | Rules, status, search, applied. Injected on every `/lite` call. |
| Lite steps | `.claude/lite/setup.md` (2.4 KB), `.claude/lite/apply.md` (3.5 KB) | Read on demand. Router + apply must stay under 8 KB (a test pins it). |
| Lite driver | `harness/lite_search.py` | `--top N --record` search; `--show N`; `--save N` (fetch and archive a row); `--start [--from FILE]`; `--gate-fail N`; `--verdict V`; `--package`; `--applied [STATUS] [--match WORD]`. Posting metadata lives in `state/lite-apply.json`, so posting text never passes through a shell. |
| Quiet compile | `harness/latex_build.py` | One line per PDF: page count against the target, `fix:` notes (stranded heading, one-word lines, each with its remedy), or the first TeX error. `/apply` 5a uses it too. |
| ATS check | `harness/ats_check.py` | Parseability (text layer, literal email and phone, years) and keyword coverage from `cv/<stem>.keywords.txt`, with a heuristic fallback. `apply_package.py` writes `ats_report.md` into every package; a parse failure blocks it. |
| Recruiter pass | `.claude/commands/recruiter.md` (4.8 KB, pinned under 5 KB) | 20 positions saved as `preferences.yaml` `target_positions`. `/setup-harness` Step 3b and `/lite setup` step 4. |
| Codex | 25 pointer skills in `.agents/skills/<workflow>/SKILL.md`; `RUNTIME-MAP.md` | `$name` invocation. The dead `.codex/prompts/` was deleted. Portal discovery is narrowed to `.agents/skills/*-search/`. |
| Installer | `harness_setup.py` | Plan question; recommends lite below ChatGPT Pro / Claude Max; seeds `preferences.yaml` `usage.{plan,mode}`. Caveman and i-have-adhd default on in lite. `Codex network` doctor row. Seeds permissions for the new scripts. |
| Fact gate | `harness/fact_check.py` | Back-to-back titles merge by **month**, never bridging a gap. The register's own `banned_phrasings` now block. Every `\cventry` employer or institution must be registered. |
| Today | `harness/today.py` | Lite commands under `usage.mode: lite`; "ready to submit" for unsent packages; no apply offer for gated jobs; one line per application; UTF-8 output. |

Instruction bytes (`wc -c`) for the standard route vs lite. The standard column is what
Codex measured on its full-workflow run (excluding shared orientation, data and source
templates); the earlier ~71 KB onboarding estimate was low.

| Route | Standard | Lite |
|---|---|---|
| One application | 161,525 B | ~7.3 KB |
| One search | 102,290 B | ~3.8 KB + script output |
| Onboarding | 128,101 B | ~27 KB (router, setup, recruiter, register example read once for shape) |

`CLAUDE.md` (16.5 KB, Claude Code) or `AGENTS.md` (11.7 KB, Codex) loads in both modes.
These are bytes, not billed tokens.

## Verification record

- Tests: 458 harness + 154 upstream, all green. `lint_skills`, `security_guards`,
  `harness_guards` and `privacy_sweep` are OK. jobbank-ca bun smoke tests pass 8/8.
- End-to-end lite runs on the demo candidate:
  - **Run 1 (Claude Code, Sonnet):** worked with friction; every finding was fixed.
  - **Run 2 (Claude Code, Sonnet):** all six commands worked in about 18 minutes; its
    findings were fixed.
  - **Run 3 (Codex):** all six commands passed. Search reached 3 boards; ATS went
    48% -> 88%; fact gate OK.
- Review passes (correctness, ponytail, consistency): all findings verified, then fixed.
- Codex's own fix commit `9ac6883` was reviewed. It is kept, except that it routed lite
  through the 13 KB RUNTIME-MAP; `7374985` reverses that and makes state reads
  BOM-tolerant.
- **Run 4 (Codex, standard workflows):** Setup Harness, Apply Any, Outcome, Today and
  Tracker worked; 2-page CV, 1-page letter, ATS 95%, fact gate zero red lines, package
  moved to `applied/`, no duplicate row or folder. Scrape found six results, then a board
  returned HTTP 500 and the run was recorded incomplete (the intended behaviour).
- Codex's commit `1a3b319` (self-review wording, `/scrape` dispatch row, network
  escalation, Windows encoding, safe metadata passing) was reviewed and kept. One fix:
  its `apply-any.md` line had lost its "On Codex" scope, which would send Claude Code to
  read the 14 KB RUNTIME-MAP on every application; restored and pinned by a test.
- **CI on `main` had failed on every push since 2026-08-08.** Two `PdfBesideTheSource`
  tests passed the user's real `evidence/register.yaml`, so they read personal data on
  the owner's machine and errored on a fresh clone. They now use the demo register.
- **Clean-checkout run (2026-10-02, detached worktree outside OneDrive, demo data):**
  all suites and guards green; a live lite search reached freehire, Job Bank (Canada)
  and LinkedIn with no errors; `--save`, both compiles, `--package`, `--applied`,
  `today.py`, `tracker_xlsx.py` and the archiver all worked, and the package moved to
  `applied/`.

## Decisions worth knowing

- **Branch, not main.** The harness tool rules say branch first. Merge only with the
  owner's approval.
- **`*-search` glob divergence.** The Codex pointers share `.agents/skills/` with the
  portal CLIs, so two upstream files changed one line each (job-scraper `SKILL.md` and
  `search-queries.md`, plus `add-portal.md`). This is recorded in REVIEW-HANDOFF §4.1.
- **Lite never reads RUNTIME-MAP by default.** Its two Codex rules are inline in
  `lite.md`.
- **Lite still looks at each final PDF.** It renders pages with `pdftoppm -png -r 50` on
  both runtimes; the owner treats the look as a never-relaxed rule.
- **Kept on purpose:**
  - the heuristic keyword fallback in `ats_check.py` (only a package built without a
    keywords file uses it);
  - the Verification Checklist inside `CLAUDE.md` (its ATS part was compressed instead
    of moved, to avoid restructuring an upstream file).
- **Recording goes through the driver.** Posting-derived text (company, title, salary) is
  never typed into a command line; this was a review finding about `$` and `$(...)`
  expansion.
- **Market table in `lite_search.py`.** Single-country boards (Danish, Canada) run only
  when the home names that country. National boards without a place flag skip the
  near-home filter, because they write place names in their own language.

## Gotchas for whoever continues

- **Upstream files.** Byte-identical upstream files are listed in REVIEW-HANDOFF §4. Any
  upstream edit is recorded in §4.1. Never edit `CHANGELOG.md` or `SETUP.md`.
- **Line endings are mixed.** `core.autocrlf` is false. Python `write_text` on Windows
  flips an LF file to CRLF, so prefer the Edit tool. Check with
  `git ls-files --eol $(git diff --name-only)`; every row must read `i/X w/X`.
- **Backslashes in scripted edits.** Heredoc Python mangles `\textbf`, `\needspace` and
  similar escapes; use the Edit tool for LaTeX-bearing text.
- **Pinned by tests:**
  - lite router + apply under 8 KB; `recruiter.md` under 5 KB;
  - the `AGENTS.md` and `CLAUDE.md` tails after "### Saying it in plain language" are
    identical;
  - an `AGENTS.md` edit needs a `framework_version` bump (`check_framework_version.py`);
  - every workflow has a Codex pointer, and no pointer name ends in `-search`.
- **Never touch the real local data in the checkout.** That means
  `evidence/register.yaml`, `job_search_tracker.csv`, `shortlist.csv` and `run_log.csv`;
  their byte sizes are 12,035 / 945 / 675 / 112. Tests redirect paths; `run_log.append`
  and `apply_package` read their paths at call time for that reason.
- **End-to-end runs belong in a detached worktree at a short path outside OneDrive.**
  For example `git worktree add --detach C:/Users/Owner/jsah-e2e HEAD`. Deep OneDrive
  paths fail to delete ("Filename too long"). The Agent tool's `isolation: worktree`
  starts from `main`, not the branch.

## Open items

Done on 2026-10-02: the Codex full-workflow run and its review (above), and two of the
optional items:

- **Folder names cut at a whole word.** `apply_package.folder_name` cuts each part at its
  last whole word within 45 characters. `package_folder` reuses a folder started under
  the old mid-word cut, so an application in flight at upgrade time never gets a second
  folder. `lite_search.py` calls `package_folder` too.
- **Bold labels in cover letters.** One `\defaultfontfeatures` line in `cover.cls`
  (upstream divergence, recorded in REVIEW-HANDOFF §4.1). A real-compile test checks the
  bold face is embedded.

Declined, with the reason, so nobody re-opens them by accident:

- **Routing `/scrape`'s board sweep through `lite_search.py`.** It would save about 50 KB
  per standard search, but the standard route would lose the job-scraper skill's
  deadline extraction, mass-posting flags, portal health check and query tiers. Lite is
  already the cheap path.
- **Moving the Verification Checklist out of `CLAUDE.md`.** Upstream's `/apply` Step 6
  reads it there, so the move restructures two upstream files for about 5 KB per Claude
  Code session.

Still open:

1. **Owner:** approve the merge, then
   `git checkout main && git merge --ff-only feat/lite-mode-codex-recruiter-ats && git push`.
   `main` has no commits the branch lacks, so it fast-forwards.
2. **Owner environment:** make Codex network permanent if they search inside Codex
   (`[sandbox_workspace_write]` with `network_access = true` in `~/.codex/config.toml`).
   They used a per-session `-c` override. This is the owner's sandbox decision; the
   repo never ships a `.codex/config.toml`.
3. **Retry a live board search in Codex.** Run 4's search hit an HTTP 500 from a board.
   The harness recorded it correctly as incomplete. The demo candidate's three boards
   answered cleanly from Claude Code on 2026-10-02; a Codex rerun with network on would
   close it.
4. **Cross-runtime drill** (REVIEW-HANDOFF Outstanding A.3): start in Claude Code, resume
   with `$continue` in Codex mid-application, and back. Needs a human at two terminals.

## Verify in one go

```bash
python -m unittest discover -s tests_harness -t .
python -m unittest discover -s tests -t .
python tools/lint_skills.py && python tools/security_guards.py && python tools/harness_guards.py
python harness/privacy_sweep.py && python tools/check_framework_version.py
```
