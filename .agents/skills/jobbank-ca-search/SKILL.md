---
name: jobbank-ca-search
version: 1.0.0
description: >
  Use this skill to search jobs on Canada Job Bank (jobbank.gc.ca), the Government
  of Canada's national job board, for any Canadian city, province, or remote work
  within Canada. Invoke for Canadian job openings, vacancies, government-listed
  postings, and NOC-coded roles. Trigger phrases: jobs in Canada, Canada Job Bank,
  jobbank.gc.ca, Guichet-Emplois, "jobs in Winnipeg", "jobs in Manitoba", Canadian
  job search, emplois au Canada, offres d'emploi.
context: fork
enabled: true  # set to false to keep this portal installed but have /scrape skip it
allowed-tools: Bash(bun run .agents/skills/jobbank-ca-search/cli/src/cli.ts *)
---

# Canada Job Bank Search Skill

Search live postings on **Canada Job Bank** (`jobbank.gc.ca`), the Government of
Canada's national job board. Public pages, no authentication, no API key, **zero
runtime dependencies** - runs with just `bun`.

> Not to be confused with the shipped `jobbank-search`, which is the **Danish**
> Akademikernes Jobbank. This skill is the Canadian board.

## Access status

`jobbank.gc.ca/robots.txt` (checked 2026-08-01) has a general `User-agent: *` block
with `Crawl-delay: 5` and **no Disallow rules** - the search and posting paths are
permitted. Respect the crawl delay: **keep volume low, a handful of requests per
run, never a crawl.** Personal use only.

## When to use this skill

- Search Canadian job openings by keyword, city/province, and recency
- Get the full description, salary, employment type and closing date of a posting
- Feed `/scrape` runs for the Canadian market

## Commands

### `search`

```bash
bun run .agents/skills/jobbank-ca-search/cli/src/cli.ts search -q "<keywords>" [flags]
```

| Flag | Meaning |
|---|---|
| `--query`, `-q <text>` | Keywords (title, skill, NOC). Required. |
| `--location`, `-l <text>` | City/province, e.g. `"Winnipeg, MB"`, `"Manitoba"`. Optional - omit for all of Canada. |
| `--jobage <days>` | Posted within N days. **Client-side filter** on the card date - Job Bank's own age filter is not URL-stable, so the CLI filters after parsing. |
| `--page <n>` | 1-indexed page (25 results/page). Default 1. |
| `--limit <n>` | Cap results emitted (client-side). |
| `--sort D\|M` | `D` = newest first (default), `M` = best match. |
| `--format <fmt>` | `json` (default) \| `table` \| `plain`. |

### `detail`

```bash
bun run .agents/skills/jobbank-ca-search/cli/src/cli.ts detail <id|url> [--format json|plain]
```

Accepts a numeric posting id or a full `jobbank.gc.ca/jobsearch/jobposting/...` URL.

## Examples

```bash
# Coordination roles in Winnipeg, newest first
bun run .agents/skills/jobbank-ca-search/cli/src/cli.ts search -q "project coordinator" -l "Winnipeg, MB" --format table

# Instructional design anywhere in Manitoba, last 14 days
bun run .agents/skills/jobbank-ca-search/cli/src/cli.ts search -q "instructional designer" -l "Manitoba" --jobage 14 --format table

# Remote-friendly training roles across Canada, capped at 10
bun run .agents/skills/jobbank-ca-search/cli/src/cli.ts search -q "training specialist remote" --limit 10 --format table

# Lab safety coordination, best-match ordering
bun run .agents/skills/jobbank-ca-search/cli/src/cli.ts search -q "laboratory safety coordinator" --sort M --format table

# Full posting text
bun run .agents/skills/jobbank-ca-search/cli/src/cli.ts detail 49987890 --format plain
```

## Output format

| Field | Notes |
|---|---|
| `id` | Numeric posting id |
| `title` | Job title |
| `company` | Employer name |
| `location` | `City (PROV)` as shown on the card |
| `date` | Card date, `YYYY-MM-DD` |
| `salary` | Salary text as posted, or `null` |
| `url` | Canonical posting URL (session id stripped) |

`detail` adds: `description` (plain text), `employmentType`, `validThrough`
(closing date), `datePosted`, `applyUrl`. Missing values are `null`, never omitted.

JSON shape: `{ "meta": { "count": ..., "page": ... }, "results": [...] }`.
Errors go to **stderr** as `{ "error": "...", "code": "..." }` with exit code 1.

## Notes (portal quirks, recorded at build time)

- Result cards are `<article id="article-<ID>">` blocks; the title lives in
  `span.noctitle`, fields in `li.date` / `li.business` / `li.location` / `li.salary`.
- Posting URLs carry a `;jsessionid=...` segment - the CLI strips it.
- The detail page embeds schema.org RDFa: the **full description is a hidden
  `<span property="description">`** (plain text), plus `datePosted`,
  `hiringOrganization`, `baseSalary`, `employmentType`, `validThrough`.
- Some postings are external ("Posted on <source site>" cards); their `detail`
  pages may have a sparser description. The card fields still parse.
- French UI (`guichetemplois.gc.ca`) mirrors the same structure; this CLI uses the
  English host.
