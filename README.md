# Job Search Agent Harness

An **evidence-gated, human-reviewed application assistant**. It runs inside the AI coding
agent you already have (**Claude Code or Codex, on an ordinary subscription**), on your own
machine. There is no hosted service, no account and no server: your CV, your evidence and
your applications stay in the folder you cloned into.

You give it your CV and your public work. It reads them the way a hiring manager would and
tells you what actually lands, including the unflattering parts and the strong thing you
never wrote down. It measures your profile against real postings and names the gaps worth
closing, the transferable skills worth claiming, and the employers worth watching. When you
decide a job is worth pursuing, it turns "apply to this" into a researched, tailored,
fact-checked CV and cover letter with every claim traced to evidence you supplied, then
archives the lot and keeps your tracker current.

It does not submit anything, and it does not invent anything. A deterministic fact gate
blocks any claim your evidence register cannot back, and every document passes your own
review before it goes anywhere. Generating an application and sending one are different
acts, and the second one stays yours.

---

## Built on ai-job-search

This is a **standalone repository derived from
[ai-job-search](https://github.com/MadsLorentzen/ai-job-search) by MadsLorentzen** (MIT) —
not a GitHub fork; upstream is tracked as a git remote and merged by tag.
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
python harness_setup.py
```

`harness_setup.py` detects your runtimes and **checks** the prerequisites, printing the exact
install command for anything missing (Node, Bun, TeX and poppler are separate
installers it cannot run for you). It **does** install the Python packages and the
job-board tools, offers the optional plugins and MCP servers, and finishes with a doctor
table that tells you the truth — including when something is installed but broken.

Choose **express** when it asks: one confirmation instead of a dozen questions.

Then, in Claude Code or Codex:

```
/setup-harness      # onboarding: your CV first, then a short interview
/today              # every morning: what needs doing, as a numbered list
apply <a posting>   # URL, screenshot, PDF, or pasted text
```

Or just say what you want — "find me jobs", "apply to this", "I got rejected by
Acme". Slash commands are optional.

### What it runs on

| Layer | What it is |
|---|---|
| Harness, gates, tracker | Python 3.10+ (PyYAML, openpyxl, pypdf) |
| Board search | Bun + TypeScript CLIs, zero runtime dependencies |
| Documents | TeX providing `lualatex` and `xelatex`; poppler for `pdftotext` **and** `pdfinfo` |
| Optional | Playwright and Firecrawl MCP servers for pages that will not fetch; pandoc for `.docx` |

Node is needed alongside Bun. Everything in the optional row degrades cleanly when absent,
and `harness_setup.py` reports which of them you actually have.

Full walkthrough of every feature: **[USER-GUIDE.md](USER-GUIDE.md)**.

---

## What it does

**A career review.** Point `/career-review` at your portfolio, site or GitHub and it
reports what a hiring manager would conclude — including the unflattering parts (the
abandoned repo pinned to your profile, the broken contact form), and the strong thing you
did that never made it onto your CV. It only suggests; nothing is added without your
say-so.

**Paths to employability.** `/upskill` compares your profile against the real postings
you have tracked and produces a prioritised gap analysis: which missing skills actually
gate the jobs you want, which you can honestly claim already under another name, and a
learning plan for the rest. `/rank` triages found jobs by fit so effort goes where the
odds are.

**Onboarding that starts with your CV.** It reads your CV, then interviews you on what the
CV left out — the numbers, whether a credential is finished, whether you *led* or
*supported*. Say "speed up" for fewer questions or "that's enough" to stop, at any point;
resume later with `/setup-harness --interview`. It never re-asks something you have
already answered.

**Job discovery you control.** Five scopes — one board, one company, all your companies of
interest, all boards, or everything — and three usage modes from `focused` (one board, no
documents generated) up to `full`. Every run states what it is about to do before it
starts, in plain language, with no invented token arithmetic. The mechanics are in
[How it finds jobs](#how-it-finds-jobs).

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

## How it finds jobs

Board search is the smallest layer in this repository, and it is meant to stay that way.

Each board has a small TypeScript CLI under `.agents/skills/`, run with Bun. They have no
runtime dependencies: plain `fetch` against the public listing endpoints the boards already
expose. LinkedIn's guest job search is one; Jobindex, Jobnet, Jobdanmark, Job Bank
(Canada), Jobbank and Freehire are the others. `/add-portal` generates a new one for your
own local board.

When a page comes back as a JavaScript shell or a cookie wall rather than the posting, the
workflow escalates to a **Playwright or Firecrawl MCP server** if you have one configured.
Both are optional and everything degrades to plain fetching without them, but in practice
they are worth having: career pages in particular are often rendered client-side, and a
plain fetch returns the shell rather than the openings. `harness_setup.py` offers to
install both. What the harness
never does is grow its own scraper: the workflows forbid writing browser or scraping code
into this repository, so there is no proxy layer and no headless-browser fleet here, and
none is planned.

Volume stays low deliberately. A run makes a handful of searches and pulls full detail only
for postings that survive a title-and-snippet filter. A 429 or a block page is recorded as
rate-limited and the tool backs off; it never treats a block as something to route around.
The portal health check spends at most one probe, one retry and one detail fetch per board.

This is personal-use tooling. Automated access to LinkedIn's public job pages is against
their Terms of Service, which is why the low ceiling and the no-custom-scrapers rule are
written into the workflows rather than left as things to optimise away later. Use it for
your own job hunt, on your own responsibility, and not commercially or for bulk collection.

---

## Questions people ask

**Is any of this hosted?** No. It runs on your machine inside Claude Code or Codex. There
is no server and no account. The requests that leave your machine are the job-board
searches you trigger and whatever your coding agent sends to its own model provider.

**Does it use proxies, a crawler or a browser farm?** No. See
[How it finds jobs](#how-it-finds-jobs). Playwright and Firecrawl are MCP servers for a
page that will not fetch: recommended, but not a scraping stack, and the harness works
without them.

**Does it submit applications for me?** No, by design. It produces the package and you
send it.

**Does it need an API key?** Only if you choose Firecrawl. Everything else runs on the
coding-agent subscription you already have.

**Can I use it commercially or to collect job data in bulk?** No. The board CLIs are for
your own job search, at low volume.

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
