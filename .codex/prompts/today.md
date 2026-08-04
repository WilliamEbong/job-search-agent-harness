# today (Codex stub)

Execute the workflow `today` exactly as specified in
`.claude/commands/today.md`, applying `RUNTIME-MAP.md` wherever that file
records a difference between runtimes.

The command file is the single source of truth for the procedure. This stub
exists only because Codex has no slash-command registry — it adds no behaviour
and overrides nothing.

Before starting, read:
1. `AGENTS.md` — orientation, including the plain-language routing table and
   the canonical application-status vocabulary
2. `.claude/commands/today.md` — the workflow itself
3. `RUNTIME-MAP.md` — §2 (no Agent tool: reviewer runs as a sequential fresh
   pass), §3 (tool-name mapping), §5 (never print a usage percentage on Codex)
