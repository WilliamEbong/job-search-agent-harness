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
| Run a workflow | `/name` (`.claude/commands/name.md`) | `$name`, or the plain-language phrase from the `AGENTS.md` routing table. `$name` mentions the pointer skill `.agents/skills/name/SKILL.md` (type `$`, or run `/skills`, to pick from the list); the pointer only says to read `.claude/commands/name.md` in full and follow it, applying this file |
| Orientation load | `CLAUDE.md` (automatic) | `AGENTS.md` (automatic; global → project walk-down, 32 KiB combined cap — keep `AGENTS.md` thin-pointer style). `CLAUDE.md` is not loaded: full workflows read it once per session for the candidate profile and the Verification Checklist; lite mode reads only what `lite.md` names |
| Skills format | `.claude/skills/*/SKILL.md`. `allowed-tools:` is Claude-only | `.agents/skills/*/SKILL.md` works as-is; the portal CLIs (`*-search`) and the workflow pointers share it. **`.claude/skills/` is not auto-discovered** — `posting-intake`, `humanizer`, `job-application-assistant`, `job-scraper` and `upskill` all live there, and two of them (`posting-intake`, `humanizer`) are mandatory in `/apply-any`. On Codex, read the SKILL.md directly by path and follow it; the `AGENTS.md` pointer names where they are |

**A typed `/name` means the same workflow** wherever it reaches the model; treat
it exactly like `$name`. In the Codex CLI it usually does not reach the model:
the composer rejects a slash command it does not know ("Unrecognized command")
and never sends the message
([openai/codex#29131](https://github.com/openai/codex/issues/29131), open when
this was written). On Codex, say `$name` or the plain-language phrase.

Translate user-facing next actions from `/name` to `$name`, including actions
printed by shared scripts. Keep the shared procedures and script output runtime-neutral.

Codex custom prompts are not the mechanism. They are deprecated and are only
ever read from the Codex home (`~/.codex/prompts`), never from a repository,
so the `.codex/prompts/` stubs this repo used to ship were never loaded.

Codex lists every skill's name and description in context each session, within
a budget of about 2% of the context window; past it, descriptions are cut or
dropped. Keep each pointer's description to one short sentence of trigger
phrases. No pointer name ends in `-search`: that suffix marks a job-portal CLI,
and `/scrape` and `/add-portal --list` find portals with
`.agents/skills/*-search/SKILL.md`.

Every command has a pointer except two, and the omissions are deliberate rather
than an oversight: **`apply`**, because `CLAUDE.md` and `AGENTS.md` both
redirect a bare `/apply` to `/apply-any` (it skips posting intake, the
hard-constraint gate, the humanizer pass, the fact gate and the tracker row),
and **`setup`**, which `/setup-harness` invokes and which asks the wrong
questions when run on its own. `/upskill` is a skill rather than a command, so
its pointer names `.claude/skills/upskill/SKILL.md`.

## 2. Subagent spawning

Two workflows genuinely need this: upstream `apply.md` and `rank.md`.

| | Claude Code | Codex |
|---|---|---|
| `/apply` fresh-context reviewer | Agent tool, `general-purpose` subagent, as upstream writes it | Available delegation tools vary by host and session. The default fallback is a **sequential review pass**: finish drafting, then apply the reviewer instructions from the top to the posting, drafts and profile. Same checklist and output format, but the drafting context is still present. Report this as self-review, not a fresh-context review. Use an isolated reviewer only when a tool provides that isolation and the session permits delegation. |
| `/rank` parallel scoring (~5 jobs per agent) | Parallel Agent-tool dispatch | Sequential batches of five with the identical scoring rubric. Slower, same result. |

A sequential pass can catch errors, but cannot discard context already in the session
or provide the independence of a reviewer who did not write the draft. Lite mode still
prohibits subagents and does not run this review step.

## 3. Tool-name mapping

| Named in the command markdown | Claude Code | Codex |
|---|---|---|
| `WebFetch` / `WebSearch` | native tools | Use the built-in web tool actually exposed in the session (for example `web.run` or `web__run` through tool discovery); do not assume its callable name is `web_search`. CLI `web_search` is also a configuration setting: cached results do not establish that a posting is live. Check the returned source and retrieval evidence. If no web tool works, use configured Firecrawl or Playwright MCP tools; otherwise **report the inability — never silently skip the step**. Do not change the user's configuration automatically. |
| `Glob` / `Read` | native tools | shell equivalents (`ls`/pattern match, file read) |
| "Read the PDF" (visual page check) | Read tool on the PDF | `pdftoppm -png -r 50 <pdf> <prefix>` (poppler, the package `pdftotext` comes from) writes `<prefix>-1.png`, `<prefix>-2.png`, …; open each with Codex's `view_image` tool. 50 DPI shows page count, page breaks and overflow; re-render one page with `-r 100 -f N -l N` when words must be read. No `pdftoppm`, or a model without image input → say the visual check did not run; never mark it passed |
| `AskUserQuestion` | native tool | Ask one concise plain-text question that names the options inline ("focused, balanced or full?"), then stop and wait for the reply. Codex's `request_user_input` tool exists only in Plan mode. Never answer for the user to keep going |
| `$ARGUMENTS` | the text after `/name` | the text after `$name` (or what the plain-language request supplies) |
| `mcp__…` tools | `claude mcp` config; `claude mcp list` | `[mcp_servers.*]` in `~/.codex/config.toml`, or `codex mcp add`; `codex mcp list` |
| `allowed-tools:` in SKILL.md frontmatter | honoured | Ignored: Codex's skill parser reads only `name`, `description` and `metadata`. The sandbox and approval policy decide instead |
| Network for shell commands (portal CLIs `bun run .agents/skills/*-search/…`, `bun install`, `pip install`, `curl`) | governed by the permission allowlist: `.claude/settings.json` pre-approves `bun run`; other commands ask | **Off by default** in Codex's sandbox. The user either enables it in their own `~/.codex/config.toml` (`[sandbox_workspace_write]` then `network_access = true`) or, under `approval_policy = "on-request"`, approves Codex's request per command. With neither, a board search fails: report "could not reach the board", never "no jobs found". The repo ships no `.codex/config.toml`: a project config loads only for a trusted project, and the sandbox posture is the user's decision |

Sandbox restrictions also cover filesystem and profile access. A sibling worktree may
need write escalation even after `git worktree add` succeeds. On Windows, installed
MiKTeX engines may fail while accessing their user profile; inspect the error and
request escalation for the affected compile before diagnosing a missing installation.
Use the session's escalation mechanism when available; never retry silently as success
or alter global configuration to bypass the restriction.

Write workflow data as UTF-8 without a BOM using file-edit tools. Windows PowerShell
5.1 `>` writes UTF-16 and `Set-Content -Encoding UTF8` adds a BOM; either can make
`state/lite-apply.json` unreadable to the driver's UTF-8 JSON reader. Keep posting text
out of shell command lines, including shell-based file-writing commands.

## 4. Optional MCP-bound features

| Feature | Requires | Absent → |
|---|---|---|
| `/gmail-sync` | Gmail MCP (hard requirement of upstream's design; no IMAP fallback) | Feature unavailable. Say so. |
| `/notion-sync` | Notion MCP | Unavailable; upstream ships its own "adapting to another tool" contract |
| Intake browser escalation | Playwright MCP | Plain fetch; blocked pages become `posting_state: unverified` |
| Structured extraction (intake, company careers pages, non-CLI boards) | Firecrawl MCP (keyless tier works) | Plain fetch + `unverified`; non-CLI boards skipped **with a notice** |

Degradation is always *visible*. A missing optional dependency changes what the system
can confirm, and the user is told which.

**Codex Cloud tasks** (started with **Work in → Cloud** on the web or in the desktop
app) run in an isolated workspace built from a cloud environment: the repositories,
dependencies, tools and access settings configured for it. Skills stored in the
repository are available there, so `$name` works; personal skills from the user's own
computer are not synced. Internet access is an environment setting (**Allow Codex to
access internet**, then package managers, custom domains only, or unrestricted), so a job
board is reachable only if the environment allows its host. TeX, poppler, Bun and MCP
servers exist in a cloud task only if the environment provides them, and each missing
one degrades visibly — "could not compile", "visual check not run", "could not reach
the board" — never silently.

## 5. Session-continuity telemetry

The one real per-runtime divergence.

| | Claude Code | Codex |
|---|---|---|
| Signal | `harness/telemetry_statusline.py`, registered as the statusline, mirrors `context_window.used_percentage` and `rate_limits.five_hour/.seven_day.used_percentage` (Pro/Max) into `state/telemetry.json` | No portable per-session context signal. Some desktop hosts expose account-wide usage limits, which are not context utilization; this harness does not consume them. `/status` and `/statusline` are human-facing. |
| Triggers | ≥80% context → refresh HANDOFF · ≥90% → advise a fresh session · ≥90% subscription window → offer continuation in the other runtime | Milestone cadence plus a conservative turn-count heuristic (~every 10 turns, refresh HANDOFF) |
| Reporting | Percentages may be quoted, with their caveats | **Never print a percentage** for harness continuity or usage telemetry. Follow the milestone cadence; do not infer context utilization from account-wide limits. This does not prohibit measured ATS scores. |
| Caveats | `used_percentage` is input-tokens-only; null before the first call; resets after `/compact` | — |

## 6. Plugin installs (handled by `harness_setup.py`)

| Plugin | Claude Code | Codex |
|---|---|---|
| Ponytail | `claude plugin marketplace add DietrichGebert/ponytail` + `claude plugin install ponytail@ponytail` | `codex plugin marketplace add DietrichGebert/ponytail` + `codex plugin add ponytail@ponytail` |
| Caveman (optional; default yes in lite mode) | `claude plugin marketplace add JuliusBrussee/caveman` + `claude plugin install caveman@caveman` | `codex plugin marketplace add JuliusBrussee/caveman` + `codex plugin add caveman@caveman` |
| i-have-adhd (optional; default yes in lite mode). Start per session: `/i-have-adhd` (Codex `$i-have-adhd`, which Codex never starts on its own); stop: "normal mode" | `claude plugin marketplace add ayghri/i-have-adhd` + `claude plugin install i-have-adhd@i-have-adhd` | `codex plugin marketplace add ayghri/i-have-adhd --ref main` + `codex plugin add i-have-adhd@i-have-adhd` |
| Humanizer | Vendored — no install (`.claude/skills/humanizer/`) | Vendored; read `.claude/skills/humanizer/SKILL.md` by path (§1) and apply its checklist, attributed — **never skip the step** |
| Playwright / Firecrawl MCP | `claude mcp add …` (offered at setup) | `codex mcp add …` (offered at setup) |

Both runtimes use the **same two-command marketplace mechanism**, verified working on
claude 2.1.x and codex-cli 0.144.6. `npx skills add JuliusBrussee/caveman -a codex`
remains a documented fallback if a future Codex drops plugin support.

Every install is verified by listing plugins afterwards. An install command that exits 0
without the plugin appearing in `plugin list` is reported as unverified, not as success.

An empty `codex plugin list` inside the sandbox is not proof that the host has no
plugins. If it contradicts skills exposed in the session, verify the inventory with
host-profile access through an approved escalation before offering an installation.

## 7. Explicitly identical — do NOT fork these

Workflow procedures · the evidence register and fact gate · preferences and hard
constraints · usage modes and cost posture · the intake ladder · tracker, archiver and
workbook · archive layout · the HANDOFF format · the `/continue` ritual · everything in
`harness/` · every portal CLI.

If one of these appears to need a runtime-specific version, the difference is a mechanic.
Find it, map it above, and keep the procedure single.
