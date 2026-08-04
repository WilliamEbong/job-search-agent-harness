# M — End-to-End Test List (the brief's full list, mapped)

All use the FICTIONAL demo candidate. Phase = where first run; all re-run at
P9. Lane: C = Claude, X = Codex, B = both.

| # | Test (handoff §2M item) | How verified | Phase | Lane |
|---|---|---|---|---|
| 1 | Onboarding | demo docs → register + preferences, all `source:`-tagged | P3 | B |
| 2 | CV ingestion | master-CV facts land in register, not directly in claims | P3 | C |
| 3 | Resume-as-template | template-inference → /add-template → test compile passes; facts did NOT enter register from the template | P3 | C |
| 4 | Preference profile | interview covers doc 01 §3D set; skips doc-answered questions; remote trade-offs asked not assumed | P3 | B |
| 5 | One-board focused search | mode caps + cost posture + run-log row | P5 | B |
| 6 | All-board search | balanced mode dedupes + ranks across boards | P5 | C |
| 7 | Remote + location boards | freehire (remote) + jobbank-ca (local) both return; location-aware research step proposes ≤3 boards | P5 | C |
| 8 | User-added board | "Add this job board: URL" → /add-portal path → live-tested integration | P5 | C |
| 9 | Closed-job rejection | closed/expired fixture → not recommended; `unverified` marking on unverifiable | P5 | C |
| 10 | URL application | intake rung 2 → package | P4 | B |
| 11 | Screenshot application | rung 3: vision extract → canonical re-acquisition → both archived | P4 | C |
| 12 | PDF application | rung 4 | P4 | C |
| 13 | Pasted-text application | rung 1 | P4 | X |
| 14 | Transferable-skill framing | demo candidate vs adjacent-field fixture: bridge appears, no fabricated experience | P4 | C |
| 15 | Hard skip-filter | posting requiring a demo-candidate hard-skip → skipped with reason; "preferred"-only version → NOT skipped | P5 | C |
| 16 | Unsupported metric rejection | planted numeral not in register → red line blocks | P2 | B |
| 17 | Unsupported credential rejection | planted credential (doc 03's fabrication test) → blocked; in-progress credential without qualifier → blocked | P2 | B |
| 18 | Research step | research notes carry provenance; no manufactured enthusiasm in output | P4 | C |
| 19 | Humanize → re-ground | humanizer changes wording → recompile + fact gate re-run (test asserts the re-run happened) | P4 | B |
| 20 | ATS parse | pdftotext text-layer: contact literals, reading order, no (cid:) markers | P4 | B |
| 21 | Render QA | page counts exact (CV 2pp, letter 1pp); visual inspect loop | P4 | C |
| 22 | Archive | posting_source/ + provenance.md + job_posting.md + quad-format present | P4 | B |
| 23 | Tracker update | draft-time row; /outcome status change; applied/ move on submitted_date; XLSX regenerates | P6 | C |
| 24 | Interview prep | /interview builds pack from EXACT archived submitted materials | P6 | C |
| 25 | Context handoff | ~80% trigger (simulated telemetry file) → HANDOFF refresh | P7 | C |
| 26 | Usage handoff where detectable | 90% five-hour/seven-day (simulated) → offer other-runtime continuation; Codex: no percentages ever printed | P7 | B |
| 27 | Claude→Codex continuation | mid-application switch, resume exact next step | P8 | B |
| 28 | Codex→Claude continuation | reverse drill | P8 | B |
| 29 | Interrupted-session recovery | kill mid-apply → `continue` → nothing redone | P7 | B |
| 30 | Demo privacy sweep | privacy_sweep + harness_guards + `git status` clean | P9 | — |
| 31 | Fresh install | deliverable L script | P9 | B |
| 32 | Attribution presence | README first screen + NOTICE.md complete | P10 | — |
| 33 | Upstream-update drill | fetch a future tag (or simulate) → ritual → guards/tests stay green | P9 | — |
| 34 | Interview controls (owner directive) | "speed up" reduces question count; "that's enough" ends keeping data; `setup --interview` revisits without re-asking | P3 | B |
| 35 | Career review (owner directive) | demo portfolio/GitHub links → CV improvement suggestions produced; NO auto-write to register/CV; accepted fact routes through `/fact` | P3 | C |
| 36 | Companies-of-interest build (owner directive) | user-named + researched proposals (big + local, CV/location-driven) each user-approved into companies.yaml | P3 | C |
| 37 | Company-of-interest search (owner directive) | fixture careers page → openings ranked with provenance; blocked page → `unverified` | P5 | C |
| 38 | Search scopes (owner directive) | each of the 5 scopes (board/company/companies/boards/all) selects exactly the right sources | P5 | B |
| 39 | Caveman optional prompt (owner directive) | setup explains Caveman + recommends lite; decline path leaves it uninstalled; accept path verifies install | P1 | B |
| 40 | USER-GUIDE.md presence | root-level guide covers every shipped feature (checklist against C matrix) | P10 | — |

Rule: a failing test is fixed in code or content, never by weakening the
check (bounded repair). Results table lands in BUILD-STATE; waivers need
written reasons.
