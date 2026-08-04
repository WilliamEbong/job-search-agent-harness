# A — Current-System Audit (private system as of 2026-08-03)

Read-only inspection of the snapshot `../job-search-ref` (clone of the private
system, branch `personal`, `v1.2.0` + 52 commits). Mechanisms only — no
personal career data appears in this document or anywhere in this repo.

## A.1 What the private system IS now

A fork of `MadsLorentzen/ai-job-search` (upstream remote kept, push URL
disabled with the literal string `DISABLED-never-push-to-upstream`), carrying
an owner-added **"scout" layer** namespaced so upstream merges never collide:

| Layer | Contents |
|---|---|
| Upstream, unmodified | README/SETUP/AGENTS/SECURITY/CONTRIBUTING, `tools/`, `tests/` (164 passing + 52 subtests, never touched), CI, 12 stock commands, 3 stock skills, 6 stock portal CLIs, stock LaTeX templates (moderncv CV + cover.cls), salary subsystem |
| Upstream, personalized by design | `CLAUDE.md` (personal content fenced `<!-- scout:begin/end -->`), `.gitignore` tail, profile files 01/02/04/05/06, `search-queries.md` |
| Owner-added | `scout/` (5 Python scripts + register + shortlist + run log + backups), 4 commands (`apply-any`, `verify-facts`, `tracker`, `fact`), `posting-intake` skill, `jobbank-ca-search` portal CLI, `tests_scout/` (21 tests), `docs/` (BUILD-STATE + 5 session handoffs + triage/shortlist docs) |

## A.2 Delta vs its own plan docs (apply-system-01/02, OWNER-BUILD-GUIDE)

**Planned and built:** the five custom components (evidence register,
deterministic fact checker, XLSX view generator, flexible-intake wrapper,
Canadian localization), P0–P4 with gates, BUILD-STATE ritual.

**Planned, still open:** `/gmail-sync` live run (needs owner sign-in; never
executed) · owner's unassisted `/apply-any` graduation run · STAR interview
examples (deferred) · `cv/main_example.tex` personalization (deliberately
skipped — `cv/` is never-edit; contact preamble moved to the template profile
file instead) · Notion sync, scheduler, watchlist tab, Typst template, direct
outreach (all deferred as planned).

**Built beyond the plan (owner-directed after freeze) — all candidates for the
harness because they are proven in live use:**
1. Quad-format outputs per application (`.tex/.pdf/.md/.docx` + combined
   document; `.md` mirror generated from `.tex` so copies cannot drift).
2. 8-week auto-archive + `applied/` auto-move, with one shared folder-matching
   function used by both archiver and workbook so links never disagree.
3. Mandatory humanizer gate before final compile, with explicit rule: any
   post-humanize wording change forces recompile + fact-gate re-run.
4. Draft-time tracker rows + 3 extra CSV columns (`location`, `rationale`,
   `submitted_date`).
5. Match-confidence autonomy ladder (80+ / 60–79 / <60 + a stated exception
   class) deciding draft vs shortlist vs record-only.
6. Five hard constraints (up from three) checked BEFORE scoring; failures
   quote the posting's own wording and are never drafted.
7. Shortlist tab + shortlist CSV with verdict vocabulary
   (`qualified | not-drafted | not-resolved | gate-fail`).
8. Human-readable folder-copy naming + slug build-source naming convention.
9. LaTeX output to `build/` via `-output-directory`.
10. Subscription-only / no-paid-API standing rule.

**Plan-vs-reality corrections it recorded** (the kind Stage 3 must expect):
profile files are 01–08 not 01–07; stock `jobbank-search` is Danish, not
Canada; upstream permissions frozen by a security-guard allowlist so local
permissions go in `settings.local.json`; scraper state lives inside the skill
directory, not repo root.

## A.3 The truth tier as built (port source for the harness)

- **Register** (`scout/evidence_register.yaml`, ~36 KB YAML): sections `meta,
  employers, education, credentials, positioning_constraints,
  technology_claim_rules, technologies, metrics, projects,
  public_repositories, research, leadership, languages, responsibilities`.
  Invariant: every entry carries `source:` (document path or
  `owner-confirmed <date>`). Notable generalizable fields: `claim_ceiling`,
  `qualifier_required` (in-progress credentials), `banned_phrasings` /
  `sanctioned_phrasings`, tiered tech claims (`direct` / `ai_assisted` /
  `familiarity_only`).
- **Checker** (`scout/fact_check.py`, ~326 lines, stdlib+PyYAML, exit code =
  red-line count). Six check classes: numerals-with-units vs registered
  metrics (or token-bounded match in the archived posting); date-range
  containment; tech-lexicon keyword leakage; in-progress credential must
  render with its qualifier (±120/160-char window); credential-shaped phrases
  must name a registered credential; machine-checkable positioning-constraint
  patterns with nearby-marker exemptions. LaTeX stripped before checking;
  percentage spellings normalized.
- **Gate wiring:** blocking in three places (standing rule, apply wrapper,
  intake skill). Exactly three legal resolutions: fix the draft · confirm the
  fact via the writeback command · fix the checker and pin a fixture. Editing
  the register to clear a red line, weakening a pattern, or presenting "with a
  note" are forbidden in writing.
- **Writeback** (`/fact`): route → contradiction check → backup → write with
  `owner-confirmed <date>` → mirror into the profile file the model-grounding
  audit reads → re-run checker tests + YAML parse → confirm.
- **Live history:** two real checker defects were root-fixed with regression
  tests (percentage-spelling false positive; substring whitelist false
  negative that had let a package pass spuriously — the record was corrected,
  not papered over). Known deliberate ceiling: checker cannot distinguish
  "I have not used X" from "I used X"; honest-gap sentences are reworded
  rather than the guard loosened.

## A.4 Intake, pipeline, boards, tracker, continuity as built

- **Intake** (`posting-intake` skill): 6 rungs — paste/file · URL (WebFetch →
  Playwright/Firecrawl escalation on JS shells or cookie/bot walls) ·
  screenshots (native vision → canonical re-acquisition via visible URL then
  `"<company>" "<exact title>"` search) · PDF/saved page (same) · mixed
  (authority order: employer careers page > job board > screenshot; then
  currency; conflicts recorded, never silently resolved) · expired/unreachable
  → `posting_state: unverified`, surfaced plainly. Archive per application:
  `posting_source/` raw artifacts + `provenance.md` (rungs attempted, chosen
  source, canonical URL, state, conflicts) + resolved `job_posting.md`.
  A resolution quality gate requires company · exact title · location/remote ·
  requirements, and asks rather than infers.
- **Pipeline order:** intake → hard-constraint gate → upstream `/apply`
  (fit eval → draft → fresh-context reviewer → revise) → humanizer (may never
  add a fact/name/number/date) → compile (lualatex CV / xelatex letter) →
  visual page loop → ATS text-layer check (`pdftotext -layout`) →
  **deterministic fact gate on final text (re-runs after any humanizer
  change)** → archive + tracker row + archiver → present with intake +
  fact-check summary blocks.
- **Boards:** 7 Bun/TS portal CLIs, zero-auth. Usable set: `linkedin-search`
  (guest endpoints; ToS caution documented), `freehire-search` (public JSON
  API, ~50 ATS aggregated), owner-built `jobbank-ca-search` (HTML+RDFa;
  robots.txt verified 2026-08-01: `Crawl-delay: 5`, no Disallow — CLI enforces
  the 5s gap; province-code derivation; client-side age filter). 4 Danish
  demos inherited. Non-CLI boards handled via Firecrawl JSON-schema extraction
  driven by a query/roster doc. Board intelligence (unreachable boards, boards
  that ignore URL filters, JS-rendered boards, "employer ATS sites aren't
  worth scraping") is recorded in BUILD-STATE §board-intelligence.
- **Tracker:** canonical CSV (upstream 13 columns + 3 owner columns), status
  vocabulary unchanged; shortlist CSV; run-log CSV. `tracker_xlsx.py`
  regenerates a 4-tab workbook (Applications with frozen header, autofilter,
  status colors, Open/Closed split, Days-since, follow-up-due, live
  hyperlinks; Summary funnel; Shortlist score-sorted with pipeline
  cross-check; Search Runs). **Strictly one-direction regenerate-only** —
  nothing is read back from the workbook, so regeneration cannot lose a note;
  notes live in CSV + per-application `outcome.md`; state changes route
  through conversation → `/outcome` (single status writer; filled
  `submitted_date` triggers the `applied/` move). Backup rule: register + CSV
  → `backups/` (keep 5) before any rewriting command.
- **Continuity:** BUILD-STATE.md ritual (`[~]` at start, `[x]` + commit at
  completion, append-only session blocks) + SESSION-HANDOFF-01..05, whose §8
  is a paste-ready continuation prompt. No `/continue` command, no `state/`
  dir — the harness formalizes this (doc 01 §10) rather than inventing it.
- **Outcome/interview:** `/outcome` archives submitted materials and is the
  only status writer; follow-up branch drafts only, never sends. `/interview`
  preps from the archived posting + actually-submitted documents.
  `/gmail-sync` is propose-and-approve only and has never been run.

## A.5 Findings that adjust doc 01 (reconciliation log seeds)

| # | Doc 01 said | Reality (evidence) | Consequence |
|---|---|---|---|
| R1 | "tagged-release updates via its own `check_upstream_updates.py`" (§11) | Script compares `framework_version` frontmatter vs `upstream/master`; not tag-aware. The *ritual* (fetch --tags → script → merge release tag on throwaway branch → guards/lint/tests) is what was drilled | Harness pins by tag itself and documents the ritual; notes script limitation honestly |
| R2 | Prereqs: Python, Bun, TeX, Node (§2) | Upstream also requires **poppler** (`pdftotext`/`pdfinfo`) for ATS + PDF verification | Poppler added to setup/doctor |
| R3 | Templates "LaTeX/Typst" (§3C) | No Typst anywhere; upstream is LaTeX-only (lualatex + xelatex); private system never added Typst | Template inference targets LaTeX; Typst only via upstream `/add-template`'s any-CLI path |
| R4 | Archive package (§5) unspecified format | Proven quad-format (.tex/.pdf/.md/.docx + combined) with drift-proof .md mirror | Ported; pandoc soft-dependency (no pandoc → no .docx, doctor notes it) |
| R5 | §14.1 default: Codex lane static if absent | Codex installed (0.144.6) | Live Codex lane in test matrix |
| R6 | §11 Firecrawl "omit" | Private system uses Firecrawl (incl. stealth for bot-blocked pages) in intake escalation + non-CLI board extraction; **owner directive at plan review: include** | Optional MCP at setup, keyless-limited works, degrades to plain fetch + `unverified` |
| R7 | Private repo "personal data local-only" | Register + shortlist are tracked in the (private) repo | Public harness is stricter: evidence/, preferences, shortlist, state/, tracker outputs all gitignored + CI-guarded |
| R8 | §10 telemetry "investigate" | Claude statusline JSON exposes context % + 5h/7d rate-limit % (Pro/Max); hooks expose none; Codex human-only | Harness ships statusline mirror script (Claude); milestone cadence + turn heuristic (Codex) |

Hygiene notes seen in the private repo, deliberately NOT ported: a committed
Excel lock file (`~$…xlsx`), `.pytest_cache`/`__pycache__`/`build/` in the
working tree, a stale "three tabs" line in `tracker.md`'s self-test text.
Harness ships correct equivalents from the start.
