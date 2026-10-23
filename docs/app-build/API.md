# Candor local API (contract between `app/server.py` and `app/static/`)

Server: Python stdlib, `http://127.0.0.1:<port>` (default 8770). `GET /` serves
`app/static/index.html` with the placeholder `__CANDOR_TOKEN__` replaced by a random
per-run token; the page reads it from `<meta name="candor-token" content="...">`.
Every `/api/*` and `/files/*` request must send header `X-Candor-Token: <token>`
(for `/files/*` the token may instead be the query parameter `t=`, so an `<iframe>`/
`<a href>` works). Wrong/missing token: 403. Static assets are `/static/<path>`.

All bodies are JSON (`Content-Type: application/json`) except upload. Errors:
`{"error": "<plain sentence for the person>"}` with status 400/403/404/409/500.

## Reads

`GET /api/ping` — no token needed; `{"app": "candor"}` (the launcher's port probe).

`GET /api/state` — everything the shell and Today need, cheap (no subprocess):
```json
{
  "app": {"name": "Candor", "version": "0.1.0"},
  "setup": {"has_register": true, "has_preferences": true, "has_positions": true,
            "onboarded": true, "cv_files": ["documents/cv/My CV.pdf"]},
  "settings": {"engine": "auto", "mode": "lite", "search_top": 5, "screen_after_search": true},
  "today": { ...the dict from harness/today.py collect(), see below... },
  "counts": {"jobs_new": 7, "applications_open": 2, "ready_to_send": 1},
  "busy": true   // a task is queued/running/waiting for an answer
}
```
`today` keys (from `harness/today.py`): `date`, `lite`, `onboarded`, `needs_positions`,
`followups` [{company, role, days_quiet, followups_sent, status}], `drafted`
[{company, role, ...}] (packages built, not yet sent), `interviews` [{company, role}],
`waiting` [...], `undrafted` [{company, role, url, score}], `deadlines`
[{company, role, url, closes_in}], `search_age_days` (int or null), `total_open`,
`total_applications`, `trials` [...]. Any list may be empty; treat unknown keys as
optional.

`GET /api/engines` — slow (runs `--version`/auth probes, 1-5 s); call on Settings and
setup only:
```json
{"engines": [{"name": "claude", "label": "Claude", "installed": true, "version": "2.1.303",
              "signed_in": true},
             {"name": "codex", "label": "Codex", "installed": true, "version": "0.160.0",
              "signed_in": true}],
 "chosen": "auto", "resolved": {"apply": "codex", "other": "claude"}}
```
`resolved` is null-valued when nothing usable is installed.

`GET /api/jobs`:
```json
{"search": {"date": "2026-10-23", "home": "Winnipeg, MB", "positions": ["Data Analyst"],
            "results": [{"number": 1, "title": "...", "company": "...", "location": "...",
                         "url": "...", "date": "2026-10-20", "deadline": "", "board": "linkedin",
                         "score": 86, "verdict": "", "rationale": "", "applied": false}]},
 "history": [{"date": "...", "company": "...", "role": "...", "location": "...",
              "source": "...", "url": "...", "score": 82, "verdict": "qualified",
              "rationale": "..."}]}
```
`search` is null before any search. `score` is the 0-100 title-match triage score;
`verdict` is the shortlist verdict when the job was screened (`gate-fail`, `qualified`,
`not-drafted`, `not-resolved`) else "". `history` = shortlist.csv newest first.
Thresholds the UI draws across the ranked table: 80 (strong fit, the assistant drafts)
and 60 (below this it will not draft).

`GET /api/applications`:
```json
{"applications": [{"id": "Rivermouth_Environmental_Consulting_Environmental_Data_Analyst",
  "company": "...", "role": "...", "status": "in_progress", "status_label": "Sent, waiting",
  "fit": 82, "date": "2026-08-04", "submitted_date": "2026-08-04", "location": "...",
  "source": "url", "rationale": "...", "followups_sent": 0, "days_quiet": 80,
  "stages": ["found", "drafted", "sent"],
  "folder": "documents/applications/Rivermouth_...",   // or "" when none
  "files": [{"name": "resume ... .pdf", "path": "documents/applications/.../x.pdf",
             "kind": "cv|letter|combined|posting|ats|other", "ext": "pdf"}]}]}
```
Status values (canonical): `in_progress`, `interview_only`, `hired`, `offer_declined`,
`rejected`, `no_response`, `withdrawn`. A row with no `submitted_date` and status
`in_progress` is "Ready to send" (`status_label`). `stages` is the form guide, an
ordered subset of `found, drafted, sent, interview, offer, hired | rejected | no_response
| withdrawn | declined`.

`GET /api/profile`:
```json
{"register": {"owner": "...", "location": "...", "email": "...", "phone": "...",
   "employers": [{"name": "...", "titles": [{"title": "...", "start": "2020-08", "end": "present"}]}],
   "education": [{"degree": "...", "institution": "...", "status": "completed"}],
   "credentials": [{"name": "...", "status": "in-progress", "qualifier": "in progress"}],
   "technologies": [{"name": "...", "ceiling": "AI-assisted only"}],
   "metrics": [{"value": "22%", "claim": "..."}], "entries": 41} ,   // null when no register
 "positions": [{"rank": 1, "title": "...", "fit": 88, "tier": "core", "because": "...",
                "gap": "...", "status": "active|dropped"}],
 "preferences": {"home": "...", "commute_km": 30, "arrangements": ["hybrid"],
                 "minimum_pay": "62000 CAD salary", "exclusions": ["..."],
                 "hard_skips": ["..."], "cv_pages": 2, "mode": "lite"}}
```

`GET /api/tasks` — `{"tasks": [task view...], "history": [{at, title, kind, status,
engine, summary}]}` (history newest first, up to 30).
`GET /api/tasks/<id>?since=<n>` — one task view:
```json
{"id": 3, "kind": "apply", "title": "Preparing an application", "engine": "codex",
 "status": "queued|running|question|done|failed|cancelled|cancelling",
 "args": {"number": 2}, "count": 14,
 "events": [{"kind": "note|step|say|you|done|error", "text": "...", "at": 1792778400.1}]}
```
`events` holds events from index `since`; poll every ~1 s while active.
`say` = the assistant's words (may contain light Markdown: paragraphs, `-` lists,
`1.` lists, `**bold**`, `` `code` ``; render safely as text, never as HTML).
`step` = a plain-language progress line. `you` = the person's reply. A task in
`question` (or `done` with an engine session) accepts a reply.

`GET /files/<relative path>?t=<token>` — serves a file under `documents/` only
(PDF inline, others as download). 404 outside it.

## Actions

| Request | Body | Effect / response |
|---|---|---|
| `POST /api/upload?name=<file name>` | raw bytes (≤ 20 MB; pdf, docx, doc, txt, md, png, jpg, jpeg) | saves to `documents/cv/` (or `documents/postings/` with `&to=posting`); `{"path": "documents/cv/x.pdf"}` |
| `POST /api/setup` | `{"cv": "documents/cv/x.pdf", "answers": ["Winnipeg, MB, Canada; citizen; 30 km; hybrid", "62000 CAD salary", "door-to-door sales", "", ""]}` (5 strings, "" = skip) | queues the setup task; `{"task": view}` |
| `POST /api/search` | `{"top": 5}` | queues the board search (a script; no AI) and, when `screen_after_search`, a screening task; `{"task": view}` |
| `POST /api/apply` | `{"number": 2}` or `{"url": "https://..."}` or `{"text": "posting text"}` or `{"file": "documents/postings/x.pdf"}`; also `{"numbers": [1, 3, 4]}` for a batch | queues one apply task per posting (the batch loop runs them one after another); `{"tasks": [view...]}` |
| `POST /api/applications/status` | `{"company": "...", "role": "...", "status": "in_progress", "sent": true}` | `sent: true` sets `submitted_date` today + status `in_progress`; otherwise sets status; then archives; `{"ok": true}` |
| `POST /api/followup` | `{"company": "...", "role": "..."}` | agent drafts a follow-up email; `{"task": view}` |
| `POST /api/interview` | `{"company": "...", "role": "..."}` | interview prep; `{"task": view}` |
| `POST /api/fact` | `{"text": "I finished the Google certificate in May 2026"}` | `{"task": view}` |
| `POST /api/ask` | `{"text": "..."}` | free question, routed by the harness; `{"task": view}` |
| `POST /api/tasks/<id>/reply` | `{"text": "..."}` | continues the session; `{"task": view}`; 409 if not waiting |
| `POST /api/tasks/<id>/cancel` | `{}` | `{"task": view}` |
| `POST /api/positions` | `{"rank": 3, "status": "dropped"\|"active"}` | strikes/restores a target position; `{"ok": true}` |
| `POST /api/settings` | any of `{"engine": "auto\|claude\|codex", "mode": "lite\|standard", "search_top": 5, "screen_after_search": true}` | `{"settings": {...}}` |
| `POST /api/open` | `{"path": "documents/applications/<folder>"}` | opens the folder/file in Explorer/Finder; `{"ok": true}` |
| `POST /api/doctor` | `{}` | runs `harness_setup.py --doctor`; `{"output": "<text>", "ok": true}` (10-60 s) |

409 with `{"error": ...}` when an action needs setup first (no register) or no engine
is installed.
