# E — Canonical State Model

One owner per family. Everything else that shows the same information is a
**view** and is regenerate-only — a view can always be deleted and rebuilt
with zero data loss.

| Family | Canonical owner (single writer) | Format | Views (regenerate-only) |
|---|---|---|---|
| Career facts (what may be claimed) | `evidence/register.yaml` — written only by `/setup` onboarding and `/fact` writeback (backup-first, `owner-confirmed <date>` sourced) | YAML, 14 sections, every entry has `source:` | profile files consumed by upstream grounding (mirror maintained by `/fact`, as the private system proved necessary); fact-check reports |
| Preferences | `preferences.yaml` — written by `/setup` preference interview + explicit user updates | YAML: compensation, location, driving, exclusions, remote_tradeoffs, hard_skips (mandatory-vs-preferred preserved), role_families, seniority, employment_type, work_authorization, industries, direction, usage_mode, volume caps | cost-posture line printed per run; mode defaults |
| Discovered jobs | `job_scraper/seen_jobs.json` (upstream, dedupe) + `shortlist.csv` (`date,company,role,location,source,url,score,verdict,rationale`; verdicts `qualified\|not-drafted\|not-resolved\|gate-fail`) | JSON + CSV | Shortlist tab in workbook |
| Search runs | `run_log.csv` (`date,portal,query,found,new,notes`) | CSV | Search Runs tab |
| Application state | `job_search_tracker.csv` (upstream 13 + 3 columns: `…,location,rationale,submitted_date`) — status written ONLY by `/outcome`; rows created at draft time by `/apply-any` | CSV; status vocab `in_progress\|interview_only\|hired\|offer_declined\|rejected\|no_response` | `Job_Search_Tracker.xlsx` (4 tabs), `/html-report` dashboard, optional `/notion-sync` |
| Application artifacts | `documents/applications/<Company>_<Role>/` — posting_source/ + provenance.md + job_posting.md + quad-format documents; `applied/` move on submitted_date; `archive/` zip at 8 weeks | files | none (the archive IS the record; interview prep reads it) |
| Templates | `templates/<family>/<name>/` + managed ACTIVE-TEMPLATE blocks in the two template profile files (upstream `/add-template` model) | LaTeX + TEMPLATE.md manifest | compiled test PDFs |
| Continuity | `state/session-log.md` (append-only milestones) + `state/HANDOFF.md` (refreshed at milestones; objective, intent, inputs, decisions, session-confirmed facts, work done/underway, files touched, verification state, unresolved, task list, exact next step, do-not-redo, git state) | markdown | none — HANDOFF is itself the durable view of session context |
| Telemetry | `state/telemetry.json` (written by the statusline mirror script, Claude lane only) | JSON: context_pct, five_hour_pct, seven_day_pct, ts | continuity triggers read it; absent file = degrade to milestone cadence |

Cross-cutting invariants (enforced in commands + tests):
1. **No second truth store.** The workbook, html-report, and Notion are never
   read back; user corrections travel through conversation → `/outcome` or
   `/fact`.
2. **Backup-before-rewrite:** register + tracker CSV copied to `backups/`
   (keep 5) before any command that rewrites them.
3. **Facts flow one way:** documents → register (with `source:`) → claims.
   A previous resume used as template contributes structure only (doc 01 §3B).
4. **Gitignore + CI guard cover every family** except templates' shipped
   examples and the demo candidate.
5. **Single folder-matcher** shared by archiver + workbook links (ported).
