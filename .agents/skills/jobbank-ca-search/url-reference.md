# Canada Job Bank - endpoint and parsing reference

Recon date: 2026-08-02 (robots.txt checked 2026-08-01). Update this file first when
the portal changes markup - the parsers in `cli/src/helpers.ts` are anchored here.

## Endpoints

| Purpose | URL |
|---|---|
| Search | `https://www.jobbank.gc.ca/jobsearch/jobsearch` |
| Detail | `https://www.jobbank.gc.ca/jobsearch/jobposting/<id>` |
| robots | `https://www.jobbank.gc.ca/robots.txt` - `User-agent: *`, `Crawl-delay: 5`, no Disallow |

## Search parameters

| Param | Meaning | Notes |
|---|---|---|
| `searchstring` | keywords | `+`-separated; accepted as input even though the site normalizes to `term=` internally |
| `locationstring` | city/province text, e.g. `Winnipeg%2C+MB` | free text; the site geocodes it |
| `sort` | `D` = date (newest first), `M` = best match | |
| `page` | 1-indexed page number | 25 results per page |
| `fprov` | province filter, e.g. `AB` | appears in the site's own filter links; not required when `locationstring` is used |

Job age: the site's "posted within" filtering was **not** found as a stable URL
parameter (form-field scan found no `fage`-style name). `--jobage` is therefore a
**client-side filter** on the parsed card date. Revisit if a stable param appears.

## Search-results markup (per card)

Response is server-rendered HTML, ~25 `<article>` cards per page:

```html
<article id="article-49987890" class="action-buttons">
  <a href="/jobsearch/jobposting/49987890;jsessionid=...?source=searchresults" class="resultJobItem">
    <h3 class="title"> ... <span class="noctitle"> construction project coordinator </span></h3>
    <ul class="list-unstyled">
      <li class="date">July 31, 2026</li>
      <li class="business">Manitoba Glass Company Inc.</li>
      <li class="location"> ... Edmonton (AB) ... </li>
      <li class="salary"> ... Salary $80,000.00 to $110,000.00 annually (to be negotiated)</li>
      <li class="source"> ... 3635023</li>   <!-- internal job number, unused -->
    </ul>
  </a>
</article>
```

Parsing rules used by the CLI:
- split on `<article id="article-` and parse each chunk independently
- id = digits immediately after the split point
- canonical URL = `https://www.jobbank.gc.ca/jobsearch/jobposting/<id>` (drop `;jsessionid` and query)
- location text needs whitespace collapsing and removal of the invisible `wb-inv` label spans
- salary: strip the leading word `Salary`; null when the `li.salary` block is absent
- card date `Month D, YYYY` -> emitted as ISO `YYYY-MM-DD`

## Detail-page markup (schema.org RDFa)

| Field | Anchor |
|---|---|
| title | `<span property="title">...</span>` |
| employer | `<span property="hiringOrganization" ...><span property="name"><strong>NAME</strong></span></span>` |
| date posted | `<span property="datePosted" class="date"> Posted on July 31, 2026</span>` |
| salary | `<span ... property="baseSalary" typeof="MonetaryAmount">` with `minValue`/`maxValue` content attrs |
| employment type | `<span property="employmentType" class="attribute-value">Permanent employment<span ...>Full time</span></span>` |
| closing date | `<p property="validThrough">2026-08-14 ...</p>` |
| description | `<span class="hidden" property="description">FULL PLAIN TEXT</span>` - already tag-free, sentences joined with `. ` |
| location | `li` items near the `fa-map-marker-alt` icon; the CLI reuses the card location when called after a search, else parses the address block |

The hidden description span is the load-bearing anchor: it is plain text (no tags to
strip) and exists because the site emits Google-for-Jobs structured data. If it ever
disappears, fall back to the visible `#comparisonchart` / job-details sections.

## Quirks

- Every internal link carries `;jsessionid=<hex>.jobsearch<NN>` - always strip it.
- External-source postings (aggregated from employer sites) can have sparser detail
  pages; card-level fields still parse.
- 404 on a removed posting returns a styled "Not found" page with HTTP 404.
- Respect `Crawl-delay: 5`: the CLI enforces a minimum gap between requests.
