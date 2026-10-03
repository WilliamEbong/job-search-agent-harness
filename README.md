# Job Search Agent Harness

**An AI job-application assistant that will not lie for you.**

Give it your CV. It tells you which jobs you are a strong candidate for, finds them on
real job boards near you, and turns any posting you choose into a tailored CV and cover
letter. Every claim in those documents is checked against evidence you supplied, so
nothing in them falls apart when an interviewer asks about it. You review the result,
and you are the one who presses send.

It runs inside the AI coding agent you may already pay for (**Claude Code or Codex**), on
your own computer. There is no website to sign up for and no server holding your data.

> Built on [ai-job-search](https://github.com/MadsLorentzen/ai-job-search) by
> MadsLorentzen (MIT), which supplies the drafting pipeline, PDF tooling, board search
> and tests. See [Built on ai-job-search](#built-on-ai-job-search) for what comes from
> where.

---

## Why use it

- **Applications you can defend.** AI writing tools inflate: "supported" becomes "led",
  a course becomes a credential. Here a script reads the finished CV and letter and
  blocks anything your evidence cannot back up. It runs again after the final style
  pass, which is exactly when inflation creeps in.
- **A recruiter's honest read, first.** Straight after reading your CV it names the 20
  job titles a good recruiter would put you forward for, each with a fit score, the
  evidence behind it and the honest gap. You cross off any you don't want; searches
  look for the rest first.
- **Jobs found for you.** It searches the job boards and employer career pages you
  choose, filters to what is near you, removes duplicates and ranks by fit.
- **Built to get past the screening software.** Every CV is read the way an
  applicant-tracking system reads it. If that reading loses your email, phone number or
  dates, the package is blocked until the CV is fixed. You also see which of the
  posting's keywords you cover.
- **Apply from anything.** Paste a link, a screenshot, a PDF or the posting text.
- **A finished package, not a draft.** Each application gets its own folder: CV and
  cover letter as PDF and Markdown (and Word, if pandoc is installed), a combined file,
  the ATS report, and an archived copy of the posting.
- **Affordable on an ordinary plan.** Lite mode runs the core loop with about 7 KB of
  instructions per application instead of about 160 KB, and keeps the fact check, the
  ATS check and the page checks.
- **Private by default.** Your CV, evidence, applications and tracker stay in the folder
  you cloned into. Git ignores them, and two checks flag any that get committed anyway.
- **It never submits anything.** Drafting an application and sending one are different
  acts, and the second one is always yours.

---

## How it works

1. **Set up.** Give it your CV. It asks a few questions about what the CV left out (the
   numbers, whether you *led* or *supported*, whether a course is finished), then names
   your 20 best-fit positions. Lite setup takes 5 to 10 minutes.
2. **Find jobs.** Say "find me jobs". You get a short ranked list near you, with the
   reasons for each score, and jobs that break one of your hard rules set aside with the
   posting's own words quoted.
3. **Apply.** Pick one from the list, or say "apply to this" with a link or screenshot.
   It writes the CV and cover letter, compiles them, checks the page count and layout,
   runs the ATS check and the fact check, and saves the package.
4. **You send it.** Open the folder, read the documents, submit them yourself, then say
   "I applied". The tracker updates and the follow-up dates appear in `/today`.

---

## Quickstart

```bash
git clone https://github.com/WilliamEbong/job-search-agent-harness
cd job-search-agent-harness
python harness_setup.py
```

`harness_setup.py` checks what your computer has and prints the exact install command for
anything missing (Node, Bun, TeX and poppler have their own installers). It installs the
Python packages and the job-board tools itself, offers the optional add-ons, and ends with
a doctor table that says plainly what works and what does not.

It asks which plan your coding agent runs on and recommends a mode: **lite** below ChatGPT
Pro or Claude Max, the standard workflows on those plans. Choose **express** for one
confirmation instead of a dozen questions.

Then open Claude Code in the folder and type (in Codex, type `$` where you see `/`):

```
/lite setup         # your CV, five questions, your 20 best-fit positions
/lite search        # jobs for your top 5 positions, near you, deduplicated
/lite apply 2       # one tailored, fact-checked, ATS-checked CV and cover letter
```

Or the standard workflows:

```
/setup-harness      # onboarding: your CV first, then a short interview
/today              # every morning: what needs doing, as a numbered list
apply <a posting>   # URL, screenshot, PDF, or pasted text
```

Commands are optional. Plain sentences work the same way:

| Say | It does |
|---|---|
| "what jobs am I a good fit for?" | the recruiter read: your 20 best-fit positions |
| "find me jobs" | a search, ranked by fit |
| "apply to this" (plus a link, screenshot, PDF or text) | a checked application package |
| "I applied" / "I got rejected by Acme" | updates the tracker |
| "what should I do today?" | the day's list: deadlines, follow-ups, ready packages |
| "prep me for the interview" | interview preparation for a tracked application |

Every walkthrough is in **[USER-GUIDE.md](USER-GUIDE.md)**.

---

## Lite or standard?

| | Lite | Standard |
|---|---|---|
| Recommended for | Plans below ChatGPT Pro or Claude Max | ChatGPT Pro, Claude Max |
| Instructions read per application | about 7 KB | about 160 KB |
| Fact check, ATS check, page and layout checks | yes | yes |
| Style (humanizer) pass and a second reviewer | no | yes |
| Company research for the cover letter | no (uses the posting) | yes |

In lite mode, scripts do the searching, compiling, checking and packaging, and the AI
does only the writing and the judgement. Every standard feature (career review, gap
analysis, interview prep) stays available as its own command. Say "switch to lite mode"
to turn it on; `usage.mode` in `preferences.yaml` holds the choice.

---

## Everything else it does

**Career review.** Point `/career-review` at your portfolio, site or GitHub and it reports
what a hiring manager would conclude: the unflattering parts (an abandoned repo pinned to
your profile, a broken contact form) and the strong work that never reached your CV. It
only suggests; nothing is added without your say-so.

**Gaps worth closing.** `/upskill` compares your profile with the postings you have
tracked: which missing skills actually block the jobs you want, which you can already
claim under another name, and a learning plan for the rest. `/rank` sorts found jobs by
fit so your effort goes where the odds are.

**Search you control.** One board, one employer, your list of employers, all boards, or
everything, at three depths from `focused` to `full`. Each run says what it is about to do
before it starts.

**Employers worth watching.** Many jobs never reach a board. `/companies` keeps a list of
employers to check directly and can suggest more (large employers in your field, local
ones hiring your skills). You approve each one.

**A tracker that cannot lose your notes.** A CSV file holds the record. The four-tab Excel
workbook is generated from it and never read back. Applications move to `applied/` when
you say you have applied and archive themselves after eight weeks.

**Picks up where you left off.** Progress is saved at every step. `/continue` resumes at
the exact next step, in either Claude Code or Codex, without redoing work or asking you
the same question twice.

---

## Why it will not make things up

Ask a language model to make a candidate look good and it will quietly improve the facts:
a better number, a credential that is "basically" finished, a tool used once described as
a skill. Each change is easy to miss on the page and hard to defend in an interview.

So the harness keeps two questions apart:

- **What may you claim?** `evidence/register.yaml`, built from your own documents. Every
  entry records where it came from.
- **How should it be presented?** The templates, the drafting and the reviewer, which are
  free to reword, reorder and argue for how your experience transfers.

Between them sits `harness/fact_check.py`. It reads the finished text and blocks the
package if it states a number, a date range, a credential, a technology or an employer
that the register does not hold, or a phrasing you have banned. It judges facts, not
style.

**A failed check is never fixed by weakening the check.** Either the draft changes, or you
confirm the fact and it is recorded with its source. That rule is written into the
workflows themselves.

---

## What it runs on

| Layer | What it is |
|---|---|
| Harness, checks, tracker | Python 3.10+ (PyYAML, openpyxl, pypdf) |
| Board search | Bun + TypeScript command-line tools, no runtime dependencies |
| Documents | TeX with `lualatex` and `xelatex`; poppler for `pdftotext` and `pdfinfo` |
| Optional | Playwright and Firecrawl MCP servers for pages that will not load plainly; pandoc for Word files |

Node is needed alongside Bun. Everything optional degrades cleanly when absent, and
`harness_setup.py` reports what you actually have.

---

## How it finds jobs

Each job board has a small TypeScript tool under `.agents/skills/`, run with Bun, that
calls the public listing pages the board already serves. LinkedIn's guest job search is
one; Jobindex, Jobnet, Jobdanmark, Job Bank (Canada), Jobbank and Freehire are the others.
`/add-portal` builds a new one for your local board.

When a page comes back as an empty JavaScript shell or a cookie wall, the workflow can use
a **Playwright or Firecrawl MCP server** if you have one. Both are optional, but career
pages are often built in the browser, so they are worth having. The harness never grows
its own scraper: the workflows forbid writing browser or scraping code into this
repository, so there is no proxy layer and no headless-browser fleet here.

Volume stays low on purpose. A run makes a handful of searches and fetches full details
only for postings that pass a title-and-summary filter. A rate limit or a block page is
recorded and the tool backs off; it never tries to get around a block.

This is personal-use tooling. Automated access to LinkedIn's public job pages is against
their Terms of Service, which is why the low ceiling and the no-scrapers rule are written
into the workflows. Use it for your own job hunt, at your own risk, and not commercially
or for bulk collection.

---

## Questions people ask

**Is any of this hosted?** No. It runs on your computer inside Claude Code or Codex. What
leaves your machine is the job-board searches you start and whatever your coding agent
sends to its own model provider.

**Does it submit applications for me?** No, by design. It prepares the package; you send
it.

**Does it need an API key?** Only if you choose Firecrawl. Everything else runs on the
coding-agent subscription you already have.

**Will it work in my country?** The tracker, checks and documents work anywhere. Board
search ships with the boards listed above, and `/add-portal` adds yours. Employer career
pages work wherever they load.

**Does it use proxies, a crawler or a browser farm?** No. See
[How it finds jobs](#how-it-finds-jobs).

**Can I use it commercially or to collect job data in bulk?** No. The board tools are for
your own job search, at low volume.

---

## Claude Code and Codex

Both work, sharing the same workflows, scripts, evidence and saved progress.
[RUNTIME-MAP.md](RUNTIME-MAP.md) is the only place the two may differ, and it records only
differences that were actually tested: how a reviewer is run, what a tool is called, and
what usage figures exist (Codex reports none, so no percentage is ever printed).

In Codex every workflow is a skill in `.agents/skills/`: type `$lite`, `$scrape`,
`$apply-any` and so on, or say what you want.

### Job search in Codex needs network access

Codex runs shell commands in a sandbox that has no internet access by default. Job-board
searches are shell commands, so inside Codex they fail until you allow network access.
Claude Code users can skip this. Setup explains the choice, and you pick one:

| Choice | How | For | Against |
|---|---|---|---|
| **Approve each search** | Nothing to set up. With Codex's usual approval setting it asks before a search runs outside the sandbox; say yes | Nothing changes on your machine, and you see every command that goes online | One approval per search |
| **Turn it on for good** | Add the two lines below to `~/.codex/config.toml`, then restart Codex | Searches just work | Every shell command Codex runs, in any project, can reach the internet |
| **Turn it on for one session** | Start Codex with `codex -c sandbox_workspace_write.network_access=true` | Nothing permanent | You type it every time |

```toml
[sandbox_workspace_write]
network_access = true
```

If the file already has a `[sandbox_workspace_write]` line, add only `network_access = true`
under it: a second copy of that header stops Codex from starting. Codex can make the edit
for you if you ask it to back the file up first and show you the change before writing.
Afterwards, the `Codex network` row of `python harness_setup.py --doctor` reads OK.

If a search fails anyway, the harness says the board could not be searched, never that
there were no jobs.

---

## Privacy

Your career data stays on your machine. `evidence/`, `preferences.yaml`, `companies.yaml`,
`state/`, your applications and your tracker are all gitignored. Two guards enforce it:
`tools/harness_guards.py` fails if an ignore rule disappears or a personal file becomes
tracked, and `harness/privacy_sweep.py` scans file contents before release.

The only candidate in this repository is fictional: Riley Chen, who does not exist, used
for tests, fixtures and the walkthrough.

---

## Built on ai-job-search

This is a **standalone repository derived from
[ai-job-search](https://github.com/MadsLorentzen/ai-job-search) by MadsLorentzen** (MIT),
not a GitHub fork; upstream is tracked as a git remote and merged by tag. That project
contributes the parts doing the heaviest lifting: the drafter-and-reviewer apply pipeline,
PDF compilation and inspection, ATS text-layer checks, the portal-CLI architecture,
application archives, the tracker, template and portal registration, the security guards
and the test suites. **This harness would not exist without it**, and none of that work is
presented as original here.

It also builds on four MIT-licensed tools: **Humanizer** (blader), **Ponytail**
(DietrichGebert), **Caveman** (JuliusBrussee) and **i-have-adhd** (ayghri).

What this project adds (the Codex port, the fact gate and evidence register, lite mode,
the recruiter pass, intake from any format, the preference engine, saved progress and the
demo candidate) is set out in [NOTICE.md](NOTICE.md), which draws the line between
inherited and original work precisely.

> Independent open-source project, not affiliated with or endorsed by Anthropic or OpenAI.
> Claude Code and Codex are named only to describe the tools this runs on.

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

Merge only once the guards and both test suites pass. `check_upstream_updates.py`
compares frontmatter versions and is **not** tag-aware: it previews, it does not decide.

---

## Licence

MIT. See [LICENSE](LICENSE). Attribution and the boundary between inherited and original
work are in [NOTICE.md](NOTICE.md).
