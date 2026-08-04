# I — Dependency Pinning Approach

| Dependency | Pin | Mechanism |
|---|---|---|
| ai-job-search (upstream) | **tag `v1.3.0`** (2026-08-03) | git history from the tag; `upstream` remote with push URL `DISABLED-never-push-to-upstream`; updates only via the documented ritual: `git fetch upstream --tags` → `python tools/check_upstream_updates.py` (frontmatter preview; NOT tag-aware — documented) → merge **release tag** on a throwaway branch → guards/lint/tests → merge |
| Ponytail plugin | 4.8.4 (version at verification) | marketplace install; setup records installed version in doctor output; no hard version requirement (dev-discipline tool) |
| Caveman plugin | latest-at-install | its installer verifies files against a committed SHA-256 manifest; setup verifies presence post-install via plugin list |
| Humanizer | **vendored at 2.9.1** (MIT) | SKILL.md copied into `.claude/skills/humanizer/` with LICENSE + provenance header (repo, version, sha); updates are deliberate re-vendors, never auto |
| Python deps | `requirements.txt`: `pyyaml`, `openpyxl`, `pypdf` pinned to the versions tested in P2–P6 (exact pins written at build time) | pip; upstream ships no requirements file — this is a harness addition, noted in NOTICE as original |
| pandoc | soft external; no pin | doctor reports version or absence; .docx output degrades |
| TeX | MiKTeX (Windows default) or TeX Live; engines lualatex + xelatex | doctor verifies both engines compile the stock templates |
| poppler | any providing `pdftotext`/`pdfinfo` | doctor verifies |
| Bun | ≥ version upstream CI uses (read from upstream ci.yml at P0) | per-CLI `bun install`; lockfiles per upstream's model |
| Playwright MCP | `@playwright/mcp@latest` (as both runtimes configure it today) | optional; setup offers, verifies connection |
| Firecrawl MCP | hosted endpoint (keyless tier) | optional; setup offers; user key optional |
| Node | ≥ current LTS (24 verified) | plugin hooks only |

Principles: every pin is written down where setup/doctor can check it; nothing
is "latest" silently except explicitly-soft tools; plugin installs are always
verified by listing afterwards (never assumed); upstream update drill is
documented in README so users can advance the pin safely.
