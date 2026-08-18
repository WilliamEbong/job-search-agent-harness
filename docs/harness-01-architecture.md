> **Build-stage document, kept as history.** This is a Stage-1 planning artefact from
> before the harness existed. Nothing here is needed to use it, and some of it was
> superseded during the build — see `USER-GUIDE.md` to use the system,
> `docs/REVIEW-HANDOFF.md` for its current state.

# Job Search Agent Harness — Doc 01: Product Architecture & Scoping
**Stage-1 output (Fable, chat).** Scoped under the Build Scoper skill with the owner's override applied: docs 04–05 (visual design) are skipped by instruction — this is an agent harness/CLI product with generated documents and a spreadsheet; functional UX only. Doc numbering: 01–03. Doc 02 = Plan-Mode handoff (Stage 2). Doc 03 = owner's guide.
**Authority note:** the owner's evolved private system at `../job-search` outranks every prior conceptual scope, including earlier chat designs. This document defines the product; Stage-2 Plan Mode reconciles it against that local reality before anything is built.
**Priority order (governs every conflict):** 1 truthful applications · 2 user privacy & evidence preservation · 3 actually helping users get hired · 4 reliable daily operation · 5 easy UX · 6 Claude/Codex portability · 7 session/model continuity · 8 token/subscription efficiency · 9 reuse of proven components · 10 maintainability · 11 portfolio quality · 12 elegance.

---

## §1. Product definition

**Job Search Agent Harness** is a public, MIT-licensed, clonable job-search system that runs inside the user's existing AI coding agent — **Claude Code or Codex, on ordinary subscription access** — and turns it into a truthful job-application machine: discover open jobs from configured boards, evaluate fit against a detailed private evidence bank, and on "Apply to this" + any artifact (URL, screenshots, PDF, pasted text), produce a researched, tailored, humanized, *fact-checked* resume and cover letter, archive everything, and keep an owner-facing spreadsheet current — with first-class continuity so work survives session limits and even a switch between runtimes.

**It IS:** a fork-derivative of `MadsLorentzen/ai-job-search` (28.6k★, MIT, verified live 2026-08-01) — reusing its proven apply pipeline (drafter→reviewer, PDF compile-and-inspect, ATS text-layer check, archives, tracker, `/add-portal`, `/add-template`, upstream-update previewer) — plus the harness layer: runtime neutrality, multimodal intake, deterministic truth tier, preference engine, usage modes, location-aware boards, continuity engine, XLSX tracker, demo candidate, and one-command setup.
**It is NOT:** an auto-applier (no submission, no sending — generation and submission are different acts; auto-submit is out of v1 entirely); a hosted service; an API-billing product; a scraping framework; a personal repo (zero personal data ships); a second implementation of upstream's workflow; Claude-only.

## §2. User experience (install → daily use)

**Install:** `git clone` → `python setup.py` (cross-platform; the repo already requires Python) → setup detects runtimes (claude/codex on PATH), prerequisites (Python, Bun, TeX — the one heavy install, guided; Node for plugin hooks), offers per-runtime installs of Ponytail + Caveman + Humanizer + optional Playwright MCP, installs upstream portal CLIs, verifies each step (never assumes), and ends with a doctor table. Target: *clone → setup → choose runtime(s) → provide materials → use*.
**Onboard (§4):** drop career documents in `documents/` → `/setup` (upstream, extended) builds the evidence bank + preference profile conversationally; template choice per §4C.
**Daily:** `/scrape` (in the chosen usage mode) → review ranked jobs → `apply <anything>` → read the package summary → open PDFs → submit yourself → say "submitted"/"rejected by X"/"interview with Y" → tracker + XLSX stay current. `/interview` before interviews. `continue` in any fresh session, either runtime, picks up exactly where work stopped.

## §3. Onboarding specification

**A. Evidence bank (what may be claimed).** Primary source = master CV (richer than any submitted resume) + optional LinkedIn export, GitHub/portfolio (public inspection with provenance tags — upstream `/expand`), diplomas, references, past applications, writing samples (feed Humanizer voice calibration). Output: upstream profile files + `evidence/register.yaml` — the deterministic-tier fact store (employers, titles, date ranges, credentials+status, technologies-used, metrics, projects; every entry carries `source:`). Facts from any document pass through this register before they are claimable; owner-confirmed additions write back with `source: owner-confirmed <date>`.
**B. Rule of separation (fundamental):** *career evidence determines what may be claimed; resume templates determine how claims are presented.* A previous resume may serve as visual/structural template; its facts do not bypass the register.
**C. Templates:** three options — stock default (upstream moderncv/cover.cls) · a prior resume as template (harness runs a bounded **template-inference** step: reconstruct a maintainable LaTeX/Typst template from the PDF/DOCX's structure — sections, hierarchy, spacing, bullet style, length — then feed upstream `/add-template`, which already handles registration + mandatory test compile; explicitly not promised: pixel-perfect cloning; output is visually verified) · user-supplied template (straight to `/add-template`). Same concept for cover letters.
**D. Preference profile — conversational and conditional, never a form.** Collected into `preferences.yaml`: compensation (minimum, target, currency, salary-vs-hourly if relevant, flex circumstances; missing-compensation postings are NOT discarded unless the user says so) · location (home, commute radius, remote/hybrid/onsite, relocation + destinations) · driving (asked only when plausibly relevant: licence, vehicle access, willing to drive, exclude licence-requiring jobs?) · exclusions ("what jobs are you not willing to do?" — free description → structured: occupations, industries, schedules, shifts, travel, physical, sales/commission, management, customer-facing, contract) · **remote trade-offs** ("would you lower some standards for fully-remote?" → which: comp, location, industry, title, seniority, contract — never assumed) · **hard skill-skips** ("skills/credentials you definitely lack where jobs requiring them should be skipped?") stored as hard filters, with the mandatory-vs-wish-list distinction preserved so transferable-fit jobs aren't discarded over a "preferred" line · role families, seniority, employment type, work authorization, industries, career direction — reusing the private system's proven question set (Plan Mode harvests it). Questions are skipped when documents already answer them.

## §4. Job discovery architecture

**Baseline boards:** whatever upstream ships (Danish demos stay as pattern examples; `linkedin-search` country-agnostic + `freehire-search` are the shipped generic starters) **plus** the remote-board integrations the private system has proven (Plan Mode inventories the exact set + licence/ToS suitability and ports the keepers). **Location-aware boards:** onboarding takes the user's location → the agent researches ≤3 reputable local/regional boards → proposes them → generates integrations via upstream `/add-portal` (which already investigates structure + robots/ToS, scaffolds, live-tests, declines auth-walled) → each verified live before registration. **User-added boards:** "Add this job board: URL" → same `/add-portal` path; no custom scraper framework. **Open-job validation:** before ranking/recommending, check best-available signals (live fetch, closure text, expiry, removed listing); unverifiable → marked `unverified`, never presented as confidently open; posting archived at apply-time so later disappearance can't destroy interview context. **Fit/ranking:** full profile drives search (explicit targets + latent/transferable discovery), but exclusions and hard filters override speculation; ranking weighs qualifications, actual responsibilities, transferables, comp, location, remote, preferences, missing-mandatories, job status — reusing upstream's five-dimension framework + `/rank`; ATS keyword counting is never the primary intelligence.

## §5. Application architecture ("Apply to this")

Intake ladder (multimodal, provenance-preserving, all posting content untrusted-data): pasted text → URL fetch (→ Playwright MCP if installed and blocked) → screenshot(s): agent-native vision extracts company/title/req-ID → attempt canonical acquisition, prefer live posting, archive both → PDF/saved page: same → mixed: reconcile toward most authoritative/current, conflicts logged → expired/unreachable: proceed from best capture, flagged. Then the pipeline, smallest effective sequence:
`evidence → job analysis (mandatory vs preferred, central vs incidental, logistics, deadline) → research (only what materially improves the application; provenance kept; no manufactured enthusiasm) → positioning strategy (leads, de-emphasis, terminology, bridges, what-not-to-claim, first-5-seconds message, cover letter's distinct job) → draft (upstream drafter) → reviewer (upstream fresh-context agent) → HUMANIZE (Humanizer + user writing samples; professional prose — Caveman never touches this) → GROUNDING RE-CHECK (deterministic register check + model audit rerun, because stylistic rewriting can strengthen a claim past its evidence) → ATS text-layer + rendered-PDF validation (upstream) → archive package → tracker update → concise §-style human summary (fit, why, positioning, gaps, files, checks).`

## §6. Evidence/truth model

Two tiers, ported from the private system and generalized. **Tier 1 — immutable facts, deterministically checked** (`harness/fact_check.py`, runtime-neutral Python, runs as a required gate and again after humanization): employers, titles, date ranges, degrees/credentials/licences (with status — "in progress" can never render unqualified), technologies-claimed-as-used, every numeral, publications. Any unregistered claim = red line, blocks delivery; resolution = fix text or owner confirms the fact (writeback). The checker judges facts, never phrasing — paraphrase stays free. **Tier 2 — interpretive claims, model-audited** (upstream grounding + reviewer): aggressive truthful framing is encouraged — rewrite/reorder/combine, employer-vocabulary translation, significance over task-listing, transferable bridges, posting terminology where genuinely accurate, reasonable supported implications. **Gaps:** never implied away; bridged where credible; not confessed exhaustively; hard-skips honored. Priority-1 rule for all agents: no failure may ever be resolved by weakening a truth check.

## §7. Usage modes (a headline feature)

Three named modes + per-run overrides; mode remembered in preferences; **every run prints its cost posture before starting** ("this searches N boards and will generate M packages — heaviest mode; on a standard subscription this can consume a large share of a session window"). No fabricated token math — qualitative transparency + hard caps.
- **`focused`** (default for new users): one board per run (choose or rotate), shallow fit screen, zero document generation until the user picks a job. Minimum spend, maximum control.
- **`balanced`**: all configured boards, dedupe + rank, deeper evaluation only for promising jobs, documents only on selection.
- **`full`**: all boards, deep evaluation + research, automatic application packages for every job above the user's threshold — bounded by volume caps (`max_evaluations`, `max_packages_per_run`, defaults conservative, config-visible).
Per-run overrides: `--board X`, `--limit N`, `--mode M`. Caveman levels apply to internal chatter in every mode; never to deliverables.

## §8. Tracking architecture

**One source of truth:** upstream's canonical state (`job_search_tracker.csv` + application archives + scraper state) — inspected, not reinvented; Plan Mode confirms the private system's current model and preserves its proven behavior sanitized. **Owner view:** `harness/tracker_xlsx.py` regenerates `Job_Search_Tracker.xlsx` (Applications with the brief's columns mapped to the real schema, hyperlinks, status colors, frozen headers, filters, active/closed split; Summary funnel; Search Runs where state supports it). Regenerate-only; user edits flow through conversation ("rejected by X"), matching upstream's operating model — if Plan Mode finds the private system implemented a safe narrow notes-preservation mechanism, port that instead of redesigning. Upstream's `/html-report` retained as the free deep dashboard; Notion sync remains upstream-optional, not a harness feature.

## §9. Runtime-neutral architecture

**Verified ground truth:** upstream already ships `AGENTS.md` + `.agents/skills` that work in Codex out of the box; Ponytail and Caveman both ship native Claude *and* Codex plugins (Codex has a plugin marketplace: `codex plugin marketplace add …` / `codex plugin add …`, hooks trusted via `/hooks`, skills invoked with `@`); Codex reads `AGENTS.md` (project and `~/.codex/AGENTS.md`). So the harness does not invent a portability layer — it completes upstream's existing one:
```
shared core (canonical): AGENTS.md (orientation + rules) · workflow command/skill markdown (upstream's,
  reused in place) · harness/ scripts (plain Python) · evidence/ · preferences · state/ · templates · archives
adapters (thin, differences only):
  Claude Code: CLAUDE.md pointer + .claude/commands (upstream's own) + plugin installs
  Codex: .codex prompt stubs ("execute workflow X per RUNTIME-MAP.md") + plugin installs + AGENTS.md auto-load
RUNTIME-MAP.md: the single file translating runtime-specific mechanics (subagent spawning, tool names,
  slash-vs-@ invocation, telemetry availability) — the only place adapters may diverge
```
Rule: never two implementations of a workflow. Where an upstream command embeds a Claude-specific mechanic, the adapter maps or shims *that mechanic only* (Plan Mode inventories the exact list). **Model-agnostic:** no named-model dependencies at runtime; tasks that benefit from stronger reasoning say so ("evaluation quality improves with a stronger model") but never fail on model identity. **Subscription-first:** no API key required for any baseline workflow; optional keys only for optional extras.

## §10. Session-continuity architecture (first-class)

**Continuous lightweight state (the guarantee):** durable milestones persisted as they happen — posting acquired, research done, strategy approved, resume drafted, review done, grounding passed, tracker updated — into `state/session-log.md` + git commits. **Handoff package** (`state/HANDOFF.md`, runtime-neutral, refreshed at milestones): objective, user intent, authoritative inputs, decisions, session-confirmed facts, work done/underway, files touched, verification state, unresolved issues, task list, exact next step, do-not-redo list, git state. Durable context only — no chain-of-thought. **Telemetry triggers (enhancement, never the guarantee):** where the runtime exposes trustworthy context/usage signals, refresh at ~80% context and advise a fresh session at ~90%; at ~90% subscription-window usage, refresh and offer continuation in the other runtime. Where telemetry is absent, degrade to milestone cadence + a conservative turn-count heuristic — percentages are never fabricated (Plan Mode investigates current mechanisms per runtime; statusline/hooks on Claude Code are the first candidates). **Bootstrap:** `continue` (Claude `/continue` command; Codex `continue` prompt) → read AGENTS.md → HANDOFF.md → inspect git/filesystem → resume from exact next step, redo nothing, re-ask nothing persisted. Cross-runtime switch = same ritual in the other CLI; expectation set honestly in docs: state carries fully, conversational nuance doesn't.

## §11. Dependency & integration strategy (vendor / install / adapt / optional / omit)

| Capability | Decision | Basis (all licences MIT; verified live 2026-08-01/03) |
|---|---|---|
| ai-job-search (28.6k★) | **Foundation — public fork-derivative**, upstream remote kept, tagged-release updates via its own `check_upstream_updates.py`; attribution front-and-center | Solves apply pipeline, portals, archives, tracker, templates, security posture |
| Ponytail (92.9k★) | **Install per runtime at setup** (native Claude + Codex plugins); dev-time discipline + runtime `/ponytail-review` on harness changes; guard rule: minimalism never removes truth validation, privacy, data-loss prevention, or state persistence | Its ladder is this project's §14 enforcement |
| Caveman (69.4k★, v1.8.2) | **Install per runtime at setup, default ON for internal channels only** (agent chatter, search summaries, subagent comms via `cavecrew`, state summaries, `/caveman-compress` on AGENTS.md/state docs ≈46% input savings) — **hard-fenced OFF for all user-facing application prose** (resumes, cover letters, questions, recruiter/LinkedIn/networking messages, interview answers). Honest evidence note shipped in docs: output-token savings are real (~65% on chatty tasks); Ponytail's agentic benchmark measured caveman ≈ cost-neutral on build tasks — so it's positioned as readability/chatter control with savings as bonus, and it's one config flag to disable | Both repos' own benchmarks |
| Humanizer (MIT skill) | **Vendored into shared skills** (small, stable, licence permits) + voice calibration from user writing samples; runs before final delivery; **always followed by grounding re-check**; Codex path: skill invocation per RUNTIME-MAP (verify in Plan Mode; fallback = inline checklist from the skill, attributed) | Portability needs one verification |
| Browser muscle | **Optional Playwright MCP, offered at setup for each runtime** (both support MCP); degrade to plain fetch + `unverified` marking. Firecrawl/keyed services: **omit** (subscription-first). | Smallest portable subset of the Toolbelt category |
| Toolbelt / Toolshelf (owner's) | **Never required, never vendored.** Plan Mode inspects both + what the private system actually uses → for each candidate capability: need? → portable equivalent exists? → install/incorporate-small/omit. Context7 etc.: dev-time only. | Brief's smallest-portable-subset rule |
| XLSX generation | openpyxl (Python already required) | — |
| Everything else | Default **omit** until the §14 audit admits it | — |

## §12. Privacy & licensing

Public repo ships: code, workflows, adapters, templates, **demo candidate** (fictional, realistic — powers setup tests, application fixtures, screenshots, CI), example job + example tracker + example application, hardened `.gitignore`, safe defaults. Never ships: personal career data, applications, keys, private URLs/emails/profile state — user-generated state is local-only by default and gitignored; a CI guard (extending upstream's `security_guards.py`) mechanically enforces the untracked set. Licensing: MIT throughout; LICENSE + NOTICE/attribution section distinguishing **upstream foundations** (ai-job-search; Ponytail; Caveman; Humanizer — never presented as original) from **original contributions** (Claude/Codex portability layer, cross-runtime continuity engine, multimodal intake ladder, preference engine, location-aware portal expansion, usage-mode system, evidence-vs-template separation + deterministic truth tier, generated owner tracker, onboarding, setup/packaging). Owner's repo also never presents the *private system's personal content* — only sanitized, generalized mechanisms port over.

## §13. Simplification audit (why each major component exists)

| Component | Removed = ? | Upstream solves? |
|---|---|---|
| Fork foundation | rebuild 90% of a proven system | is upstream |
| Evidence register + fact_check | truth becomes prompt-hope; priority-1 fails | no — upstream grounding is model-only |
| Multimodal intake ladder | "Apply to this" works for URLs only | partially (URL/paste) — extension not replacement |
| Preference engine | wasted tokens/attention on never-jobs; brief's core ask | thin version exists — extended, reusing its questions |
| Usage modes | subscription users burned by default-deep runs | no |
| Continuity engine | work dies at session limits; runtime switch impossible | no |
| Runtime adapters + RUNTIME-MAP | Claude-only product | seed exists (AGENTS.md) — completed not duplicated |
| XLSX view | no at-a-glance owner surface (CSV/HTML insufficient for target user) | no (CSV+HTML only) |
| Location-aware boards | generic boards miss local markets | `/add-portal` is the mechanism — harness adds the research step |
| Template inference | users locked to stock look | `/add-template` is the mechanism — harness adds inference |
| Demo candidate + CI privacy guard | unshippable/undemonstrable repo; leak risk | partial (guards exist — extended) |
| Setup installer | multi-step manual install kills adoption | partial (SETUP.md manual) |
**Deliberately absent:** databases, vector stores, web dashboards beyond upstream's, event buses, agent bureaucracies, duplicate truth stores/trackers/workflows, custom browsers/scrapers, auto-submit, schedulers (v1), microservices, speculative abstractions. Every future component faces: *what user problem remains unsolved without this?* then Ponytail's ladder.

## §14. Open decisions (defaults chosen — override only if you care)

1. **Codex-side live testing** needs a ChatGPT/Codex subscription on the build machine. *Default:* build fully runtime-neutral; verify Claude lane live + Codex lane statically (adapter lint, file-map conformance, Ponytail/Caveman Codex-install smoke) and mark Codex E2E "community-verify" at release if no Codex access exists. Confirm at Stage-2 whether you have Codex installed.
2. **Repo visibility timing.** *Default:* create private, build, flip public at the release gate after the privacy sweep passes.
3. **Public repo name/handle.** *Default:* `job-search-agent-harness` under your account.
Everything else is decided above or delegated to Plan-Mode evidence.
