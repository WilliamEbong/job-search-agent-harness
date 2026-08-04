# Board intelligence

Operational knowledge about job boards, learned by running against them. Ported from
live use and sanitized. This is the file to read before adding a board, and the file to
update when a board surprises you.

The general lesson first, because it applies to every entry below: **a board that
returns nothing and a board that is broken look identical.** Almost everything here is a
variation on that.

---

## Choosing what to add

### Employer ATS sites are usually not worth scraping
Greenhouse, Lever, Workday and friends host thousands of separate employer instances,
each with its own URL and no shared index. Adding "an ATS" as a board means adding one
employer at a time — which is what `companies.yaml` already does, with the user's
approval and a note about why the employer matters.

Use companies-of-interest for individual employers. Use boards for genuine aggregators.

### Check robots.txt and terms before writing anything
Upstream `/add-portal` does this and will decline a board that forbids automated access
or requires authentication. Do not work around it. A board that needs a login is a board
the user should search by hand.

Record the check: which robots.txt, read on what date, and any crawl-delay found. That
record is what makes it possible to re-verify later instead of re-deciding.

### Prefer a public JSON API over HTML
HTML layouts change without notice and break parsers silently — usually into "zero
results", not into an error. A JSON endpoint that changes shape tends to fail loudly.

---

## Behaviours that cost time

### Some boards silently ignore URL filters
You pass a location or date filter, the response is a 200, and the results ignore it
entirely. Nothing errors. The fix is client-side filtering after fetch, plus a test that
would notice: assert that a filtered query returns *different* results from an unfiltered
one, not merely that it returns results.

### JavaScript-rendered boards return a shell
A plain fetch gets navigation, a footer and an empty results container. The give-away is
a 200 response with plausible-looking HTML and no postings.

Escalate per `RUNTIME-MAP.md`: Firecrawl structured extraction first (cheaper, more
stable), Playwright when the page needs real interaction. If neither is configured, mark
the source `unverified` and say so. Never write a bespoke browser driver in this repo.

### Bot walls answer 200 with a challenge page
Same shape as above, different cause, and worth distinguishing in the note — a JS shell
will work with Playwright, a bot wall often will not.

### Honour crawl-delay, and enforce it in code
A board declaring `Crawl-delay: 5` needs five seconds *enforced between requests by the
CLI*, not five seconds a human remembered when writing the code. The ported
`jobbank-ca-search` CLI does this; copy that pattern.

### Postings outlive their listings
A posting can be removed hours after it is found. This is why the intake ladder archives
the posting text at apply time: when the listing disappears, the archived copy is the
only record of what was actually applied to, and interview preparation reads it weeks
later.

---

## Interpreting results honestly

### Zero results is a finding, not an absence
Log every run, including empty ones (`harness/run_log.py`). Without the log, a board
whose CLI broke three weeks ago is indistinguishable from a quiet market — and the
natural conclusion, "there are no jobs", is the wrong one.

### `unverified` is not `none`
When a source cannot be read, the honest report is "could not read this source", not "no
openings". Conflating them removes an employer from someone's search without them ever
deciding to remove it.

### Dedupe across sources, and prefer the employer
The same posting routinely appears on two aggregators and the employer's own careers
page, often with different titles and stale salary data on the aggregators. Deduplicate
by URL first, then by (company, role, location), and treat the employer's own listing as
canonical.

---

## Adding a board

1. Check robots.txt and terms; record what you found and when.
2. Run upstream `/add-portal` — it investigates structure, scaffolds the CLI, and live
   tests it.
3. Verify the live test returned real postings, not a shell.
4. Add a fixture-based test. Live tests are network-flaky and belong in local, on-demand
   runs, not CI.
5. Note anything surprising here.

Boards are added at any time, not only during onboarding, and the next `--scope boards`
run picks them up with no further setup.
