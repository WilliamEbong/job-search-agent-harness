# RUNTIME-MAP

The **only** place Claude Code and Codex are allowed to diverge.

Everything not listed here is identical across runtimes and lives once, in the shared
core: workflow command markdown, the evidence register and fact gate, preferences, usage
modes, the intake ladder, tracker and archiver, archive layout, the HANDOFF format, the
`/continue` ritual, every script in `harness/`, and every portal CLI.

**The rule:** never two implementations of a workflow. An adapter maps a *mechanic* — how
a subagent is spawned, what a tool is called — never a procedure. If you find yourself
writing a second version of a workflow "for Codex", stop: that belongs in the shared
command file, with the mechanic mapped here.

Entries exist only where inspection proved a real difference.

---

## 1. Invocation

| Mechanic | Claude Code | Codex |
|---|---|---|
| Run a workflow | `/name` (`.claude/commands/name.md`) | `@`-invoke the skill, or paste the stub from `.codex/prompts/name.md`: "Execute workflow `name` as specified in `.claude/commands/name.md`, applying RUNTIME-MAP.md" |
| Orientation load | `CLAUDE.md` (automatic) | `AGENTS.md` (automatic; global → project walk-down, 32 KiB combined cap — keep `AGENTS.md` thin-pointer style) |
| Skills format | `.claude/skills/*/SKILL.md`. `allowed-tools:` is Claude-only | `.agents/skills/*/SKILL.md` works as-is; Claude-only frontmatter keys are ignored, treat them as advisory |

## 2. Subagent spawning

Two workflows genuinely need this: upstream `apply.md` and `rank.md`.

| | Claude Code | Codex |
|---|---|---|
| `/apply` fresh-context reviewer | Agent tool, `general-purpose` subagent, as upstream writes it | No Agent tool. Run the reviewer as a **sequential fresh pass**: finish drafting, then start the reviewer instructions from the top with *only* the reviewer's inputs (posting, drafts, profile), explicitly discarding the drafting context. Same checklist, same output format. |
| `/rank` parallel scoring (~5 jobs per agent) | Parallel Agent-tool dispatch | Sequential batches of five with the identical scoring rubric. Slower, same result. |

The reviewer's value comes from *not having written the draft*. On Codex that has to be
achieved by discipline instead of by process isolation — which means the discarding step
is the whole mechanism, not a formality.

## 3. Tool-name mapping

| Named in the command markdown | Claude Code | Codex |
|---|---|---|
| `WebFetch` / `WebSearch` | native tools | Codex's own web search/browse. If unavailable in a session, use the Firecrawl or Playwright MCP; if neither is configured, **report the inability — never silently skip the step**. |
| `Glob` / `Read` | native tools | shell equivalents (`ls`/pattern match, file read) |
| `mcp__…` tools | `claude mcp` config | `[mcp_servers.*]` in `~/.codex/config.toml`, or `codex mcp add` |

## 4. Optional MCP-bound features

| Feature | Requires | Absent → |
|---|---|---|
| `/gmail-sync` | Gmail MCP (hard requirement of upstream's design; no IMAP fallback) | Feature unavailable. Say so. |
| `/notion-sync` | Notion MCP | Unavailable; upstream ships its own "adapting to another tool" contract |
| Intake browser escalation | Playwright MCP | Plain fetch; blocked pages become `posting_state: unverified` |
| Structured extraction (intake, company careers pages, non-CLI boards) | Firecrawl MCP (keyless tier works) | Plain fetch + `unverified`; non-CLI boards skipped **with a notice** |

Degradation is always *visible*. A missing optional dependency changes what the system
can confirm, and the user is told which.

## 5. Session-continuity telemetry

The one real per-runtime divergence.

| | Claude Code | Codex |
|---|---|---|
| Signal | `harness/telemetry_statusline.py`, registered as the statusline, mirrors `context_window.used_percentage` and `rate_limits.five_hour/.seven_day.used_percentage` (Pro/Max) into `state/telemetry.json` | None exposed to the agent. `/status` and `/statusline` are human-facing only. |
| Triggers | ≥80% context → refresh HANDOFF · ≥90% → advise a fresh session · ≥90% subscription window → offer continuation in the other runtime | Milestone cadence plus a conservative turn-count heuristic (~every 10 turns, refresh HANDOFF) |
| Reporting | Percentages may be quoted, with their caveats | **Never print a percentage.** No number exists to print, and an invented one is worse than none because the user will plan around it. |
| Caveats | `used_percentage` is input-tokens-only; null before the first call; resets after `/compact` | — |

## 6. Plugin installs (handled by `setup.py`)

| Plugin | Claude Code | Codex |
|---|---|---|
| Ponytail | `claude plugin marketplace add DietrichGebert/ponytail` + `claude plugin install ponytail@ponytail` | `codex plugin marketplace add DietrichGebert/ponytail` + `codex plugin add ponytail@ponytail` |
| Caveman (optional; setup explains it and recommends lite mode) | `claude plugin marketplace add JuliusBrussee/caveman` + `claude plugin install caveman@caveman` | `codex plugin marketplace add JuliusBrussee/caveman` + `codex plugin add caveman@caveman` |
| Humanizer | Vendored — no install (`.claude/skills/humanizer/`) | Vendored; reached via the `AGENTS.md` pointer. If `@`-invocation fails, apply the skill's checklist inline, attributed — **never skip the step** |
| Playwright / Firecrawl MCP | `claude mcp add …` (offered at setup) | `codex mcp add …` (offered at setup) |

Both runtimes use the **same two-command marketplace mechanism**, verified working on
claude 2.1.x and codex-cli 0.144.6. `npx skills add JuliusBrussee/caveman -a codex`
remains a documented fallback if a future Codex drops plugin support.

Every install is verified by listing plugins afterwards. An install command that exits 0
without the plugin appearing in `plugin list` is reported as unverified, not as success.

## 7. Explicitly identical — do NOT fork these

Workflow procedures · the evidence register and fact gate · preferences and hard
constraints · usage modes and cost posture · the intake ladder · tracker, archiver and
workbook · archive layout · the HANDOFF format · the `/continue` ritual · everything in
`harness/` · every portal CLI.

If one of these appears to need a runtime-specific version, the difference is a mechanic.
Find it, map it above, and keep the procedure single.
