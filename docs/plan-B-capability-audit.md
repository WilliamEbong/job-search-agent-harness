# B — Installed-Capability Audit (build machine, verified 2026-08-03)

Every claim below was verified by direct command or file inspection this
session. UNVERIFIED items are marked and carry a resolution step.

## B.1 Runtimes

| Item | State | Harness consequence |
|---|---|---|
| Claude Code | 2.1.220, working | Primary build/test lane |
| **Codex CLI** | **0.144.6 installed**; `~/.codex/config.toml`; AGENTS.md honored (global + project walk-down, 32 KiB cap, closer-to-cwd wins); plugin marketplace commands work (`codex plugin list` verified); MCP config present (context7/fcrawl/playwright); skills invoked with `@` | **Live Codex lane** (doc 01 §14.1 default overridden by evidence) |
| Python | 3.14.3 (+ uv 0.11.29) | Meets upstream 3.10+ |
| Node / npm | v24.14.1 / 11.11.0 | Plugin hooks OK |
| Bun | **not on PATH** | P0 install (portal CLIs are Bun/TS) |
| TeX (lualatex/xelatex) | **not installed** | P0 install (MiKTeX or TeX Live; both engines needed) |
| poppler (pdftotext/pdfinfo) | **not installed** | P0 install (ATS + PDF verification) |
| Typst | not installed | Not needed (reconciliation R3) |
| git / gh | 2.48.1 / 2.93.0 | OK; gh enables private-repo creation + release gate |
| pandoc | not probed this session — **UNVERIFIED** | Resolve in P0 doctor; soft dependency (no pandoc → no .docx output) |

## B.2 Agent plugins & skills

| Capability | State | Decision |
|---|---|---|
| Ponytail | 4.8.4 installed both runtimes, ACTIVE (full) | Reuse; dev-discipline + `/ponytail-review` on harness changes (doc 01 §11) |
| Caveman | **not installed** (exists only as a ponytail benchmark arm). Verified install commands: Claude `claude plugin marketplace add JuliusBrussee/caveman` + `claude plugin install caveman@caveman`; Codex `npx skills add JuliusBrussee/caveman -a codex`; SHA-256-manifest installer | **Owner directives: install during P0 on both runtimes** (build machine), verify post-install. **For end users it is OPTIONAL**: setup explains what Caveman is (internal-chatter compression, output-token savings) and recommends **lite** mode for this harness; user chooses; hard-fenced OFF deliverables regardless |
| Humanizer | 2.9.1 installed as Claude plugin; MIT (LICENSE present); portable SKILL.md format; upstream repo blader/humanizer 32.9k★ | Vendor SKILL.md into shared skills + voice calibration; Codex path UNVERIFIED → P8 verifies `@`-invocation on Codex, fallback = inline checklist (attributed) |
| superpowers / ecc | installed (Claude only) | Dev-time only; NOT product dependencies. Note: ecc hooks (GateGuard fact-force, cost tracker, suggest-compact) fire during Stage-3 builds on this machine |
| Playwright MCP | connected on both runtimes (`@playwright/mcp@latest`) | Optional install offered at setup per runtime (doc 01 §11) |
| **Firecrawl MCP** | connected on both runtimes; keyless tier verified (unauthenticated Search/Scrape/Parse with limits) | **Part of the harness (owner directive, overrides doc 01 §11 omit):** optional MCP at setup, wired into intake escalation (incl. stealth for bot-blocked pages) + non-CLI board extraction; degrades to plain fetch + `unverified` when absent |
| context7 MCP | connected | Dev-time only; never a product dependency |
| Indeed connector (claude.ai) | live, owner-personal (search_jobs/get_job_details/get_company_data/get_resume) | Documented optional integration; never core (not portable, not zero-config) |
| Gmail/Drive/Calendar connectors | live, owner-personal | Upstream `/gmail-sync` remains optional-if-configured, as upstream ships it |

## B.3 Toolbelt / Toolshelf (handoff §1B — confirmed inspected)

- **Toolbelt** (global CLAUDE.md v1.0.2 block; user MCPs context7, playwright,
  fcrawl): private system genuinely uses **Playwright + Firecrawl** (intake
  escalation rung; Firecrawl JSON-schema extraction for non-CLI boards).
  Portable equivalents chosen above. Nothing else in the Toolbelt is needed by
  the product. Users never need the owner's Toolbelt.
- **Toolshelf** (manifest of 1045 entries; searched: job boards, job search,
  resume/CV, xlsx, spreadsheet, pdf, handoff/session, humanize, latex, typst):
  **zero domain-relevant hits** — all 16 "resume" matches are the verb; only
  genuinely useful entries are first-party xlsx/pdf/docx skills, and XLSX is
  already covered by openpyxl. → nothing vendored from the shelf; the
  build-minimal decisions in deliverable C stand on this evidence.

## B.4 Telemetry ground truth (resolves doc 01 §10 investigation)

- **Claude Code:** statusline scripts receive JSON with
  `context_window.used_percentage` (input-tokens-only; `current_usage` null
  before first call and after `/compact`) and
  `rate_limits.five_hour.used_percentage` / `.seven_day.used_percentage`
  (Pro/Max). **Hooks receive no usage fields at all** (verified against
  official docs). No statusline is currently configured on this machine.
  → Harness ships a small statusline script that mirrors this JSON to
  `state/telemetry.json`; workflows read it at milestones for the 80/90%
  context and 90% subscription-window triggers.
- **Codex:** `/status`, `/statusline` are human-facing; no documented
  programmatic channel to the running agent (UNVERIFIED that none exists —
  treated as absent). → Codex lane uses milestone cadence + conservative
  turn-count heuristic; percentages never fabricated.

## B.5 Per-capability decision summary (need → private-system use → portable equivalent → decision)

| Capability | Needed? | Private uses? | Portable equivalent | Decision |
|---|---|---|---|---|
| Apply pipeline | yes | yes (upstream) | upstream itself | reuse-upstream @v1.3.0 |
| Deterministic truth tier | yes | yes (scout) | plain Python | port-from-private, generalized |
| Multimodal intake | yes | yes (scout) | runtime-neutral skill md | port-from-private |
| XLSX owner view | yes | yes (scout) | openpyxl | port-from-private |
| Board CLIs | yes | yes | Bun CLIs (already portable) | reuse-upstream + port jobbank-ca |
| Browser escalation | yes | yes | Playwright MCP (both runtimes) | install-optional |
| Structured web extraction | yes | yes | Firecrawl MCP (keyless tier) | install-optional (owner directive) |
| Humanization | yes | yes | vendored MIT skill | vendor |
| Chatter compression | yes (doc 01) | no (not installed privately either) | Caveman plugin both runtimes | install at setup + P0 |
| Dev discipline | build-time | yes | Ponytail both runtimes | install at setup (recommended) |
| Docs lookup (context7) | dev-time | dev-time | — | omit from product |
| Email sync | optional | present, never run | upstream command + user's own Gmail MCP | reuse-upstream, optional |
| Notion view | no | deliberately unconfigured | upstream optional | leave upstream-optional |
| Salary subsystem | no | unused | — | leave upstream files untouched, unused |
| Indeed connector | no (core) | available | — | document as optional |
