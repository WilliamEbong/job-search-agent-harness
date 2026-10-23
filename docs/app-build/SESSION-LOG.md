# Session log

- 2026-10-23 Branch `feat/desktop-app` from main 8d02378. Resume cron c52ae3a4 (hourly :17).
- 2026-10-23 Decision: skip Spec Kit. `specify init` writes skills into `.claude/` and `.agents/`, which in this repo are the product shipped to job seekers' agents; speckit skills there would leak into every user's Claude/Codex. Undo: run the Spec Kit setup on a separate checkout.
- 2026-10-23 Decision: Python stdlib HTTP server + vanilla ES modules, no build step and no new dependency (harness already needs only Python + PyYAML). Undo: swap `app/server.py` for FastAPI; front end is framework-free so it ports.
- 2026-10-23 Decision: "/design" = the impeccable skill (no skill named design exists). No image generation on this machine, so code-led. William is away under build-continuously, so the direction round is decided by me instead of the decision page; disclosed in the report.
- 2026-10-23 Decision: engine runs per task. "Auto" uses Codex for the long apply/search loops when installed, Claude otherwise; Codex gets network for that one run only via `-c sandbox_workspace_write.network_access=true` (nothing written to config.toml). Undo: Settings > Engine.
- 2026-10-23 Decision: app name "Candor" (the harness's promise: it will not lie for you). Undo: one constant `APP_NAME` + title strings.
