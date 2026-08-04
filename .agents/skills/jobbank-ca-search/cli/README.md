# jobbank-ca-cli

Zero-runtime-dependency CLI for searching **Canada Job Bank** (`jobbank.gc.ca`)
public postings with `bun`. Part of the `jobbank-ca-search` skill; see
`../SKILL.md` for the command reference and `../url-reference.md` for the
parsing anchors.

```bash
bun install          # dev types only (typescript, @types/bun)
bun run typecheck
bun run src/cli.ts search -q "project coordinator" -l "Winnipeg, MB" --format table
bun run src/cli.ts detail <id> --format plain
bun test             # includes live smoke tests (network required)
```

Notes:

- Zero runtime dependencies by design (plain `fetch` + regex chunk parsing);
  `bun install` pulls dev types only.
- `helpers.ts` enforces the site's `Crawl-delay: 5` between requests, so
  multi-request runs are deliberately slow. Keep volume low; personal use only.
- Tests hit the live site (there is no fixture server); they need a network
  connection and tolerate the crawl delay via the 60s test timeout.
