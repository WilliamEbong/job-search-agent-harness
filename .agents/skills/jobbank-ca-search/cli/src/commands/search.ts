import {
  SEARCH_URL,
  htmlFetch,
  parseJobCards,
  writeError,
  type JobCard,
} from "../helpers.js"

export interface SearchOpts {
  query: string
  location?: string
  jobage: number
  page: number
  limit?: number
  sort: "D" | "M"
  format: "json" | "table" | "plain"
}

// Job Bank's locationstring biases ordering but does not hard-filter; the site's
// own province facet is fprov=<CODE>. Derive it from the --location text so
// "Winnipeg, MB" and "Manitoba" actually restrict results to the province.
const PROVINCES: Record<string, string> = {
  alberta: "AB", "british columbia": "BC", manitoba: "MB", "new brunswick": "NB",
  "newfoundland and labrador": "NL", "nova scotia": "NS", "northwest territories": "NT",
  nunavut: "NU", ontario: "ON", "prince edward island": "PE", quebec: "QC",
  saskatchewan: "SK", yukon: "YT",
}

export function provinceCode(location: string): string | null {
  const trimmed = location.trim().toLowerCase()
  if (PROVINCES[trimmed]) return PROVINCES[trimmed]
  const code = location.match(/,\s*([A-Za-z]{2})\.?\s*$/)
  if (code) {
    const upper = code[1].toUpperCase()
    if (Object.values(PROVINCES).includes(upper)) return upper
  }
  return null
}

function withinAge(card: JobCard, days: number): boolean {
  if (!days || days >= 9999) return true
  if (!card.date) return true // keep undated cards rather than silently dropping them
  const posted = Date.parse(card.date)
  if (isNaN(posted)) return true
  return Date.now() - posted <= days * 86400000
}

export async function runSearch(opts: SearchOpts): Promise<number> {
  const params = new URLSearchParams()
  params.set("searchstring", opts.query)
  // What the location flag actually achieved, so the caller is never told a
  // filter applied when none did. `locationstring` only biases ordering, so a
  // location that yields no province code searches the whole country: asking
  // for "Winnipeg" returns Montreal and Brossard postings that look local
  // until you read the location column. Measured against the live board.
  let locationFilter = "none supplied"
  if (opts.location) {
    params.set("locationstring", opts.location)
    const prov = provinceCode(opts.location)
    if (prov) {
      params.set("fprov", prov)
      locationFilter = `province:${prov}`
    } else {
      locationFilter = "none - nationwide; add a province (\"Winnipeg, MB\") to narrow"
    }
  }
  params.set("sort", opts.sort)
  params.set("page", String(opts.page))

  let html: string
  try {
    html = await htmlFetch(`${SEARCH_URL}?${params.toString()}`)
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "FETCH_FAILED")
    return 1
  }

  let results = parseJobCards(html).filter((c) => withinAge(c, opts.jobage))
  if (opts.limit && opts.limit > 0) results = results.slice(0, opts.limit)

  if (opts.format === "table") {
    for (const r of results) {
      process.stdout.write(
        `${r.id}  ${r.date ?? "----------"}  ${(r.title ?? "").slice(0, 44).padEnd(44)}  ` +
          `${(r.company ?? "").slice(0, 30).padEnd(30)}  ${r.location ?? ""}\n`,
      )
    }
    process.stdout.write(
      `\n${results.length} result(s), page ${opts.page}, location filter: ${locationFilter}\n`,
    )
  } else if (opts.format === "plain") {
    for (const r of results) {
      process.stdout.write(
        `${r.title} - ${r.company ?? "?"} - ${r.location ?? "?"} - ${r.date ?? "?"}\n${r.url}\n\n`,
      )
    }
  } else {
    process.stdout.write(
      JSON.stringify(
        { meta: { count: results.length, page: opts.page, location_filter: locationFilter }, results },
        null,
        2,
      ) + "\n",
    )
  }
  return 0
}
