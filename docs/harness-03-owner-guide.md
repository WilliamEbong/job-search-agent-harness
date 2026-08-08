> **Build-stage document, kept as history.** This walked the owner through
> commissioning the build in 2026-08; the build is done and the repository is public.
> The step-by-step instructions here are for that process, not for using the harness —
> see `USER-GUIDE.md` for that, and `docs/REVIEW-HANDOFF.md` for the current state.

# Job Search Agent Harness — Doc 03: Owner's Guide
**Your manual for the whole pipeline: design is done (Stage 1 — this package). You run Stage 2 (Fable plans in Claude Code), Stage 3 (Opus builds), and then anyone can use the product. Your total attention: ~30–45 minutes across everything, mostly two pastes and a few clicks. Your private job-search system is never touched.**

## Before you start (3 min)
1. File Explorer → `Documents\job-search-build` (it exists — your private system lives in its `job-search` subfolder).
2. Create a new folder next to it: `job-search-agent-harness`.
3. Inside it, create a folder `docs` and put these three files in it: `harness-01-architecture.md`, `harness-02-planmode-handoff.md`, this guide.

## Stage 2 — Fable plans (your part: ~5 min, then walk away)
1. VS Code → **File → Open Folder…** → `job-search-agent-harness` → trust the folder.
2. **Terminal → New Terminal** → type `claude` → Enter.
3. Type `/model` → Enter → pick **Fable** (the newest frontier model listed).
4. **Press Shift+Tab until the footer shows Plan Mode.**
5. Paste this (byte-identical to handoff §5) and press Enter:
```
Read docs/harness-01-architecture.md and docs/harness-02-planmode-handoff.md in full. You are
Fable in Plan Mode: inspect and plan only — write no production code. First snapshot the
private system read-only per handoff §0.1, then work the §1 inspection list, then produce
every §2 deliverable, ending with IMPLEMENTATION-PLAN.md and OPUS-KICKOFF.txt. Keep
docs/PLAN-STATE.md current so this same paste resumes a cut-off session. Prefer the recorded
defaults over asking me; batch any real questions into one message.
```
6. It inspects your machine and your private system (read-only, via a throwaway copy) and writes the full implementation plan. It may ask you **one batched question message** — the likely items: *do you have Codex installed?* (answer honestly; "no" is fine — the plan adjusts) and any real ambiguity it found. Answer once.
7. **What good looks like:** `docs\` fills with the audit, reuse matrix, phases, test matrix, `IMPLEMENTATION-PLAN.md`, and `OPUS-KICKOFF.txt`. Skim `IMPLEMENTATION-PLAN.md`'s first page — if the summary matches what you expect (public harness, private system untouched, truth checks intact), you're ready. Reply **"plan approved"**.

## Stage 3 — Opus builds (your part: ~10 min spread out)
1. Same terminal: type `/model` → pick the newest **Opus**.
2. **Press Shift+Tab until Plan Mode is OFF** (normal/auto mode).
3. Open `docs\OPUS-KICKOFF.txt`, copy its contents, paste, Enter. Opus builds everything hands-off.
4. Your moments, when it asks: click **Yes** on any Windows permission boxes · confirm the demo-candidate application "package looks right" (this uses the **fictional** sample person — your real career data never enters this project) · at the very end, the release gate: it shows the privacy-sweep results and asks whether to flip the repo **public** — say yes when you're happy (default path creates it private first).
5. **Cut off mid-build?** Reopen the folder → `claude` → `/model` Opus → paste the same `OPUS-KICKOFF.txt` contents. It resumes from its progress file; nothing is lost. (Same trick in Stage 2 with the Stage-2 paste.)

## How you know it's done (3 min)
- `docs\` contains a README-quality manual, the plan documents, and test results all green — including the fabrication tests (a planted fake credential was **caught and blocked**).
- github.com → your repositories → `job-search-agent-harness` — public (or private until you flip it), with the attribution section crediting ai-job-search, Ponytail, Caveman, and Humanizer, and your original contributions listed.
- The demo works: in the repo, `claude` → follow the README quickstart as if you were a stranger → the sample candidate gets a full application package.

## Using it yourself (optional, later)
The harness is for the public; **your** job search stays in your private `job-search` system. If you ever want to dogfood the harness with your real profile, clone it to a separate private folder and onboard there — never inside the public repo folder.

## If something looks wrong
| You see | Do |
|---|---|
| It wants to change `..\job-search` | It won't — that's a hard stop in its rules. If it ever asks, reply "no — read-only, use the snapshot." |
| A question you think the docs answer | "Re-check the architecture doc and handoff first; ask only what they don't answer." |
| Stuck install / long download | Ask "install status?" — it works on other steps meanwhile. |
| Session died | The resume trick in Stage 3 step 5. |
| Anything else | Paste the message and ask: "explain in plain language and tell me what to do." |

**Plain-language recap:** two pastes start everything — one for the planner, one for the builder. You answer one question batch, click a few permission boxes, eyeball one fake-person application, and approve going public. Your own system and your personal data stay completely out of it.

---

## Stage 3 outcome (added 2026-08-04, after the build)

Stage 3 is built. The repository exists at
`github.com/WilliamEbong/job-search-agent-harness` and is **private**.

- **Where the detail lives:** `docs/build-history/BUILD-STATE.md` — the phase ledger, the
  40-test results table with its seven written waivers, and a plain-language
  close-out at the end. Read that file's close-out section if you read nothing
  else.
- **The demo package** is at
  `documents/applications/Rivermouth_Environmental_Consulting_Environmental_Data_Analyst/`. It is the
  fictional Riley Chen applying to a fictional employer. Open the two PDFs.
- **The fabrication test passed live.** Seven fake claims planted into the demo
  CV were all caught and blocked; the honest version passes cleanly.
- **Your private system is untouched.** The throwaway copy used to port
  mechanisms has been deleted.
- **Still yours to decide:** whether the demo package looks right, and whether
  to make the repository public. It stays private until you say otherwise.
