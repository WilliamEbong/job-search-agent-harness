// Data source: Canada Job Bank (jobbank.gc.ca) public server-rendered pages.
// Search returns <article id="article-<ID>"> cards; detail pages embed schema.org
// RDFa (property="...") including a hidden plain-text description span.
// Parsed with regex over per-card chunks - the markup is shallow and stable.
// Anchors documented in ../url-reference.md; update that file first on breakage.

export const SEARCH_URL = "https://www.jobbank.gc.ca/jobsearch/jobsearch"
export const DETAIL_URL = "https://www.jobbank.gc.ca/jobsearch/jobposting"

export function writeError(error: string, code: string): void {
  process.stderr.write(JSON.stringify({ error, code }) + "\n")
}

const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

// robots.txt declares Crawl-delay: 5 - enforce a minimum gap between requests.
const CRAWL_DELAY_MS = 5000
let lastRequestAt = 0

/** Fetch HTML with the robots crawl delay and exponential backoff on 429/5xx. Returns "" on 404. */
export async function htmlFetch(url: string): Promise<string> {
  const sinceLast = Date.now() - lastRequestAt
  if (lastRequestAt > 0 && sinceLast < CRAWL_DELAY_MS) {
    await new Promise((r) => setTimeout(r, CRAWL_DELAY_MS - sinceLast))
  }
  const maxRetries = 6
  let delay = 1000
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    lastRequestAt = Date.now()
    const response = await fetch(url, {
      headers: {
        "User-Agent": UA,
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-CA,en;q=0.9",
      },
      redirect: "follow",
      signal: AbortSignal.timeout(20000),
    })
    if (response.status === 429 || response.status >= 500) {
      if (attempt === maxRetries) {
        throw new Error(`Request failed: ${response.status} ${response.statusText}`)
      }
      const jitter = Math.floor(Math.random() * 500)
      await new Promise((r) => setTimeout(r, delay + jitter))
      delay = Math.min(delay * 2, 10000)
      continue
    }
    if (response.status === 404) return ""
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status} ${response.statusText}`)
    }
    return response.text()
  }
  throw new Error("Request failed after max retries")
}

export interface JobCard {
  id: string
  title: string
  company: string | null
  location: string | null
  date: string | null
  salary: string | null
  url: string
}

export interface JobDetail extends JobCard {
  description: string | null
  employmentType: string | null
  datePosted: string | null
  validThrough: string | null
  applyUrl: string | null
}

function numericEntity(cp: number): string {
  return cp >= 0 && cp <= 0x10ffff ? String.fromCodePoint(cp) : ""
}

function decodeHtmlEntities(text: string): string {
  return text
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/&#(\d+);/g, (_, dec) => numericEntity(parseInt(dec, 10)))
    .replace(/&#[xX]([0-9a-fA-F]+);/g, (_, hex) => numericEntity(parseInt(hex, 16)))
    .replace(/&nbsp;/g, " ")
}

function stripTags(html: string): string {
  return html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim()
}

/** Strip tags + decode entities + collapse whitespace. */
export function clean(html: string): string {
  return decodeHtmlEntities(stripTags(html))
}

const MONTHS: Record<string, string> = {
  january: "01", february: "02", march: "03", april: "04", may: "05", june: "06",
  july: "07", august: "08", september: "09", october: "10", november: "11", december: "12",
}

/** "July 31, 2026" -> "2026-07-31". Returns null when the text does not parse. */
export function toISODate(text: string | null): string | null {
  if (!text) return null
  const m = text.match(/([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})/)
  if (!m) {
    const iso = text.match(/(\d{4}-\d{2}-\d{2})/)
    return iso ? iso[1] : null
  }
  const month = MONTHS[m[1].toLowerCase()]
  if (!month) return null
  return `${m[3]}-${month}-${m[2].padStart(2, "0")}`
}

/** Extract the text of the first <li class="..."> block with the given class. */
function liText(chunk: string, cls: string): string | null {
  const m = chunk.match(new RegExp(`<li class="${cls}"[^>]*>([\\s\\S]*?)</li>`, "i"))
  if (!m) return null
  // Drop invisible label spans (<span class="wb-inv">Location</span>) before cleaning.
  const withoutInv = m[1].replace(/<span class="wb-inv"[^>]*>[\s\S]*?<\/span>/gi, " ")
  return clean(withoutInv) || null
}

/**
 * Parse the search-results page: <article id="article-<ID>"> cards. Each chunk is
 * parsed independently so one malformed card cannot break the rest.
 */
export function parseJobCards(html: string): JobCard[] {
  const results: JobCard[] = []
  const chunks = html.split(/<article id="article-/).slice(1)

  for (const chunk of chunks) {
    const idMatch = chunk.match(/^(\d+)/)
    if (!idMatch) continue
    const id = idMatch[1]

    const titleMatch = chunk.match(/<span class="noctitle"[^>]*>([\s\S]*?)<\/span>/i)
    const title = titleMatch ? clean(titleMatch[1]) : null
    if (!title) continue

    const salaryRaw = liText(chunk, "salary")
    const salary = salaryRaw ? salaryRaw.replace(/^Salary\s*/i, "") || null : null

    results.push({
      id,
      title,
      company: liText(chunk, "business"),
      location: liText(chunk, "location"),
      date: toISODate(liText(chunk, "date")),
      salary,
      url: `${DETAIL_URL}/${id}`,
    })
  }

  return results
}

/** Extract the inner text of the first element carrying a schema.org property. */
function rdfa(html: string, property: string, tag = "span"): string | null {
  const m = html.match(
    new RegExp(`<${tag}[^>]*property="${property}"[^>]*>([\\s\\S]*?)</${tag}>`, "i"),
  )
  return m ? clean(m[1]) || null : null
}

/** Parse a posting detail page. Returns null when the page is a 404/empty body. */
export function parseJobDetail(html: string, id: string): JobDetail | null {
  if (!html) return null
  const title = rdfa(html, "title")
  if (!title) return null

  // Employer: <span property="hiringOrganization"><span property="name"><strong>N</strong></span></span>
  let company: string | null = null
  const org = html.match(
    /property="hiringOrganization"[^>]*>[\s\S]*?property="name"[^>]*>([\s\S]*?)<\/span>/i,
  )
  if (org) company = clean(org[1]) || null

  // Full plain-text description lives in a hidden schema.org span.
  const desc = html.match(/<span class="hidden" property="description">([\s\S]*?)<\/span>/i)
  const description = desc ? decodeHtmlEntities(desc[1]).replace(/\s+/g, " ").trim() || null : null

  // Employment type has a nested attribute-value span ("Permanent employment" + "Full time").
  let employmentType: string | null = null
  const et = html.match(/property="employmentType"[^>]*>([\s\S]*?)<\/span>\s*<\/span>/i)
  if (et) employmentType = clean(et[1]) || null
  if (!employmentType) employmentType = rdfa(html, "employmentType")

  const datePostedRaw = rdfa(html, "datePosted")
  const datePosted = toISODate(datePostedRaw)

  const validThrough = toISODate(rdfa(html, "validThrough", "p"))

  const salaryBlock = html.match(/<span[^>]*property="baseSalary"[^>]*>([\s\S]*?)<\/span>\s*<\/span>/i)
  const salary = salaryBlock ? clean(salaryBlock[1]) || null : null

  const apply = html.match(/href="([^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*Apply/i)
  const applyUrl = apply ? decodeHtmlEntities(apply[1]) : null

  // <span property="joblocation" typeof="Place"> ... addressLocality / addressRegion
  const locality = rdfa(html, "addressLocality")
  const region = rdfa(html, "addressRegion")
  const location = locality ? (region ? `${locality} (${region})` : locality) : null

  return {
    id,
    title,
    company,
    location,
    date: datePosted,
    salary,
    url: `${DETAIL_URL}/${id}`,
    description,
    employmentType,
    datePosted,
    validThrough,
    applyUrl,
  }
}

/** Parse a numeric posting id out of a raw id or a jobbank.gc.ca posting URL. */
export function idFromInput(input: string): string | null {
  if (/^\d{4,}$/.test(input)) return input
  const m = input.match(/jobposting\/(\d+)/)
  return m ? m[1] : null
}
