# F — RUNTIME-MAP.md (draft)

This becomes the repo-root `RUNTIME-MAP.md`. It contains ONLY differences that
inspection proved real (handoff §2F). Everything not listed here is identical
across runtimes and lives once in the shared core. Rule: never two
implementations of a workflow — adapters map mechanics, not procedures.

## 1. Invocation

| Mechanic | Claude Code | Codex |
|---|---|---|
| Run a workflow | `/name` (`.claude/commands/name.md`) | `@`-invoke the skill, or paste stub from `.codex/prompts/name.md`: "Execute workflow `name` as specified in `.claude/commands/name.md`, applying RUNTIME-MAP.md" |
| Orientation load | `CLAUDE.md` (auto) | `AGENTS.md` (auto; global → project walk-down, 32 KiB combined cap — keep AGENTS.md thin-pointer style) |
| Skills format | `.claude/skills/*/SKILL.md` (`allowed-tools:` is Claude-only — Codex ignores it; treat as advisory) | `.agents/skills/*/SKILL.md` portable format works as-is; framework skills read via pointer |

## 2. Subagent spawning (the two heavy cases found: `apply.md`, `rank.md`)

| | Claude Code | Codex |
|---|---|---|
| `/apply` fresh-context reviewer | Agent tool, `general-purpose` subagent (as upstream writes it) | No Agent tool: run the reviewer as a **sequential fresh pass** — complete drafting, then start reviewer instructions from the top with only the reviewer inputs (posting, drafts, profile), explicitly discarding drafting context. Same checklist, same output format |
| `/rank` parallel scoring (~5 jobs/agent) | Parallel Agent-tool dispatch | Sequential batches of 5 with the identical scoring rubric; slower, same result |

## 3. Tool-name mapping (mild cases: add-portal, add-template, expand, setup, rank, outcome, interview, notion-sync)

| Named in command md | Claude Code | Codex |
|---|---|---|
| `WebFetch` / `WebSearch` | native tools | Codex web search/browse capability; if unavailable in a session, use Firecrawl/Playwright MCP (both configured in `~/.codex/config.toml`) or report inability — never silently skip |
| `Glob` / `Read` | native tools | shell equivalents (`ls`/pattern match, file read) |
| MCP tools (`mcp__…`) | `claude mcp` config | `[mcp_servers.*]` in `~/.codex/config.toml`; same servers verified available (playwright, fcrawl, context7) |

## 4. Optional MCP-bound features

| Feature | Requirement | Absent → |
|---|---|---|
| `/gmail-sync` | Gmail MCP (hard-required by upstream design; no IMAP fallback) | feature unavailable; say so |
| `/notion-sync` | Notion MCP | unavailable (upstream ships its own "Adapting to Another Tool" contract) |
| Intake browser escalation | Playwright MCP | plain fetch; blocked pages → `posting_state: unverified` |
| Intake/board structured extraction (incl. stealth) | Firecrawl MCP (keyless tier OK) | plain fetch + `unverified`; non-CLI boards skipped with notice |

## 5. Session-continuity telemetry (the one real per-runtime divergence)

| | Claude Code | Codex |
|---|---|---|
| Signal | `harness/telemetry_statusline.py` registered as statusline; mirrors `context_window.used_percentage` + `rate_limits.five_hour/.seven_day.used_percentage` (Pro/Max) to `state/telemetry.json` | none exposed to the agent (verified: /status is human-only) |
| Triggers | ≥80% context → refresh HANDOFF; ≥90% → advise fresh session; ≥90% subscription window → offer continuation in other runtime | milestone cadence + conservative turn-count heuristic (~every 10 turns refresh HANDOFF); never print a percentage |
| Caveats (documented, never papered over) | used_percentage is input-tokens-only; resets after /compact; null before first call | — |

## 6. Plugin installs (setup.py per-runtime)

| Plugin | Claude Code | Codex |
|---|---|---|
| Ponytail | `claude plugin marketplace add DietrichGebert/ponytail` + `claude plugin install ponytail@ponytail` | `codex plugin marketplace add DietrichGebert/ponytail` + `codex plugin add ponytail@ponytail` |
| Caveman | `claude plugin marketplace add JuliusBrussee/caveman` + `claude plugin install caveman@caveman` | `npx skills add JuliusBrussee/caveman -a codex` (per-session `/caveman`) |
| Humanizer | vendored skill (no install) | vendored skill via AGENTS.md pointer; if `@`-invocation fails → inline checklist fallback (attributed) — P8 verifies |
| Playwright/Firecrawl MCP | `claude mcp add …` (offered) | `[mcp_servers.*]` entries (offered) |

Note: `codex plugin marketplace add` syntax is verified working on this
machine's codex-cli 0.144.6 but is thin in official docs (UNVERIFIED-thin);
setup.py must verify each install by listing plugins afterwards, never assume.

## 7. Explicitly identical (do NOT fork these)

Workflow procedures, evidence register + fact gate, preferences, usage modes,
intake ladder logic, tracker/archiver/workbook, archive layout, HANDOFF
format, `/continue` ritual (read AGENTS.md → HANDOFF.md → git/filesystem →
resume), all Python in `harness/`, all portal CLIs.
