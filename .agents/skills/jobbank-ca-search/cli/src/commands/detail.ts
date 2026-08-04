import { DETAIL_URL, htmlFetch, idFromInput, parseJobDetail, writeError } from "../helpers.js"

export interface DetailOpts {
  id: string
  format: "json" | "plain"
}

export async function runDetail(opts: DetailOpts): Promise<number> {
  const id = idFromInput(opts.id)
  if (!id) {
    writeError(`could not parse a posting id from "${opts.id}"`, "BAD_ID")
    return 1
  }

  let html: string
  try {
    html = await htmlFetch(`${DETAIL_URL}/${id}`)
  } catch (e) {
    writeError(e instanceof Error ? e.message : String(e), "FETCH_FAILED")
    return 1
  }

  const detail = parseJobDetail(html, id)
  if (!detail) {
    writeError(`posting ${id} not found (removed or expired)`, "NOT_FOUND")
    return 1
  }

  if (opts.format === "plain") {
    const lines = [
      `${detail.title}`,
      `Employer: ${detail.company ?? "?"}`,
      `Location: ${detail.location ?? "?"}`,
      `Posted: ${detail.datePosted ?? "?"}   Closes: ${detail.validThrough ?? "?"}`,
      `Type: ${detail.employmentType ?? "?"}`,
      `Salary: ${detail.salary ?? "?"}`,
      `URL: ${detail.url}`,
      "",
      detail.description ?? "(no description found)",
    ]
    process.stdout.write(lines.join("\n") + "\n")
  } else {
    process.stdout.write(JSON.stringify(detail, null, 2) + "\n")
  }
  return 0
}
