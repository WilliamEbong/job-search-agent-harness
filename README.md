# Job Search Agent Harness

A truthful job-application system that runs inside the AI coding agent you already have —
**Claude Code or Codex, on an ordinary subscription.** It finds open jobs, judges whether
they are worth your time, and turns "apply to this" into a researched, tailored,
fact-checked resume and cover letter — then archives everything and keeps your tracker
current.

It does not submit anything. Generating an application and sending one are different acts,
and the second one stays yours.

---

## Built on ai-job-search

This project is a **fork-derivative of
[ai-job-search](https://github.com/MadsLorentzen/ai-job-search) by MadsLorentzen** (MIT).
That project contributes the parts doing the heaviest lifting: the drafter-and-reviewer
apply pipeline, PDF compilation and inspection, ATS text-layer checks, the portal-CLI
architecture, application archives, the tracker, template and portal registration, the
security guards, and the test suites. **This harness would not exist without it**, and
none of that work is presented as original here.

It also builds on three MIT-licensed tools: **Humanizer** (blader), **Ponytail**
(DietrichGebert) and **Caveman** (JuliusBrussee).

What this project adds — portability across runtimes, a deterministic truth tier,
multimodal intake, a preference engine, usage modes, session continuity, and a demo
candidate — is set out in [NOTICE.md](NOTICE.md), which draws the line between inherited
and original work precisely.

> Independent open-source project, not affiliated with or endorsed by Anthropic or OpenAI.
> Claude Code and Codex are named only to describe the toolchain this runs on.

---

## The idea

Most AI job-application tools share one failure: asked to make a candidate look good, a
language model will quietly make things up. A slightly better number. A credential that is
"basically" finished. A technology used once, described as a skill. Each is defensible in
the moment and indefensible in an interview.

So this harness splits two questions that usually get mixed together:

- **What may this person claim?** — `evidence/register.yaml`, built from their own
  documents, where every entry carries a `source:`.
- **How should it be presented?** — templates, drafting and the reviewer pass, which are
  free to rephrase, reorder, reframe and argue for transferable relevance.

Between them sits a deterministic gate. `harness/fact_check.py` reads the finished text
and blocks delivery if it asserts a number, date range, credential or technology that is
not in the register. It judges facts, never phrasing. It runs **again** after the
humanizing pass, because rewriting for style is exactly what turns "supported the
migration" into "led the migration" — which reads better, which is why nobody catches it
by eye.

**A failing check is never resolved by weakening the check.** Fix the draft, or confirm
the fact and record it properly. That rule is written into the workflows themselves, not
just into this README.

---

## Quickstart

```bash
git clone https://github.com/<you>/job-search-agent-harness
cd job-search-agent-harness
python setup.py
```

`setup.py` detects your runtimes, checks prerequisites, installs what is missing, offers
the optional plugins and MCP servers, and finishes with a doctor table that tells you the
truth — including when something is installed but broken.

Then, in Claude Code or Codex:

```
/setup-harness      # onboarding: your CV first, then a short interview
/scrape             # find jobs
apply <a posting>   # URL, screenshot, PDF, or pasted text
```

**Prerequisites:** Python 3.10+, Node, Bun, a TeX distribution providing `lualatex` and
`xelatex`, and poppler (`pdftotext` **and** `pdfinfo`). pandoc is optional and affects
only `.docx` output.

Full walkthrough of every feature: **[USER-GUIDE.md](USER-GUIDE.md)**.

---

## What it does

**Onboarding that starts with your CV.** It reads your CV, then interviews you on what the
CV left out — the numbers, whether a credential is finished, whether you *led* or
*supported*. Say "speed up" for fewer questions or "that's enough" to stop, at any point;
resume later with `/setup-harness --interview`. It never re-asks something you have
already answered.

**A career review, if you want one.** Point `/career-review` at your portfolio, site or
GitHub and it reports what a hiring manager would conclude — including the unflattering
parts, and the strong thing you did that never made it onto your CV. It only suggests;
nothing is added without your say-so.

**Job discovery you control.** Five scopes — one board, one company, all your companies of
interest, all boards, or everything — and three usage modes from `focused` (one board, no
documents generated) up to `full`. Every run states what it is about to do before it
starts, in plain language, with no invented token arithmetic.

**Companies of interest.** Boards only find jobs that were advertised on boards. Keep a
living list of employers worth watching directly; `/companies` also researches candidates
for it — large employers in your field and local ones hiring your skill set — and you
approve each before it lands.

**Apply from anything.** A link, screenshots, a PDF, pasted text, or several at once. The
intake ladder resolves them into one posting, archives the raw artifacts with a provenance
record, and marks a posting `unverified` when it could not be confirmed live rather than
implying otherwise.

**Tracking that cannot lose your notes.** A CSV holds the truth; the four-tab Excel
workbook is a view, regenerated and never read back. Applications move to `applied/` when
you say you have applied, and archive themselves after eight weeks.

**Work that survives a session ending.** State is written at every milestone. `/continue`
resumes at the exact next step — in either runtime — redoing nothing and re-asking
nothing.

---

## Runtimes

Claude Code and Codex both work. Workflows, scripts, register and state files are shared;
[RUNTIME-MAP.md](RUNTIME-MAP.md) is the only place the two may differ, and it records only
differences that were actually verified — how a subagent is spawned, what a tool is
called, and what usage telemetry exists (on Codex: none, so no percentage is ever
printed).

---

## Privacy

Your career data stays on your machine. `evidence/`, `preferences.yaml`, `companies.yaml`,
`state/`, your applications and your tracker are all gitignored, and two guards enforce it
mechanically: `tools/harness_guards.py` fails CI if an ignore rule disappears or a
personal path becomes tracked, and `harness/privacy_sweep.py` scans file *content* before
release.

The only candidate-shaped content in this repository is a fictional demo candidate — Riley
Chen, who does not exist — used for tests, fixtures and the walkthrough.

---

## Updating from upstream

The upstream pin is tag `v1.3.0`. To move it:

```bash
git fetch upstream --tags
python tools/check_upstream_updates.py
git checkout -b upstream-merge && git merge v1.4.0
python tools/security_guards.py && python tools/harness_guards.py
python -m unittest discover -s tests -t . && python -m unittest discover -s tests_harness -t .
```

Merge only once the guards and both suites pass. Note that `check_upstream_updates.py`
compares frontmatter versions and is **not** tag-aware — it previews, it does not decide.

---

## Licence

MIT — see [LICENSE](LICENSE). Attribution and the boundary between inherited and original
work are in [NOTICE.md](NOTICE.md).
