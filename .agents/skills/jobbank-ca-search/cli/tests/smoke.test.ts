// Live smoke tests against jobbank.gc.ca (network required). The crawl-delay in
// helpers.ts makes these deliberately slow; the package test timeout is 60s.
import { describe, expect, test } from "bun:test";
import { runCLI, parseJSON } from "./helpers";

interface SearchPayload {
  meta: { count: number; page: number };
  results: Array<{
    id: string | null;
    title: string | null;
    company: string | null;
    location: string | null;
    date: string | null;
    salary: string | null;
    url: string | null;
  }>;
}

describe("flag validation (no network)", () => {
  test("search without --query exits 1 with JSON error on stderr", async () => {
    const r = await runCLI(["search"]);
    expect(r.exitCode).toBe(1);
    const err = JSON.parse(r.stderr) as { error: string; code: string };
    expect(err.code).toBe("NO_QUERY");
  });

  test("bad --jobage exits 1 with JSON error on stderr", async () => {
    const r = await runCLI(["search", "-q", "x", "--jobage", "soon"]);
    expect(r.exitCode).toBe(1);
    const err = JSON.parse(r.stderr) as { code: string };
    expect(err.code).toBe("BAD_ARG");
  });

  test("detail without id exits 1 with JSON error on stderr", async () => {
    const r = await runCLI(["detail"]);
    expect(r.exitCode).toBe(1);
    const err = JSON.parse(r.stderr) as { code: string };
    expect(err.code).toBe("NO_ID");
  });

  test("unknown command exits 1", async () => {
    const r = await runCLI(["frobnicate"]);
    expect(r.exitCode).toBe(1);
    const err = JSON.parse(r.stderr) as { code: string };
    expect(err.code).toBe("BAD_CMD");
  });
});

describe("live search (network)", () => {
  test("search returns >=1 result with non-null id/title/url", async () => {
    const r = await runCLI(["search", "-q", "coordinator", "-l", "Winnipeg, MB", "--limit", "5"]);
    expect(r.exitCode).toBe(0);
    const payload = parseJSON<SearchPayload>(r);
    expect(payload.meta.count).toBeGreaterThanOrEqual(1);
    for (const item of payload.results) {
      expect(item.id).toBeTruthy();
      expect(item.title).toBeTruthy();
      expect(item.url).toContain("jobbank.gc.ca/jobsearch/jobposting/");
      expect(item.url).not.toContain("jsessionid");
    }
  }, 60000);

  test("detail on a live id returns a readable description", async () => {
    const search = await runCLI(["search", "-q", "coordinator", "-l", "Winnipeg, MB", "--limit", "1"]);
    const payload = parseJSON<SearchPayload>(search);
    expect(payload.results.length).toBeGreaterThanOrEqual(1);
    const id = payload.results[0].id as string;

    const detail = await runCLI(["detail", id]);
    expect(detail.exitCode).toBe(0);
    const d = parseJSON<{ id: string; title: string; description: string | null }>(detail);
    expect(d.id).toBe(id);
    expect(d.title).toBeTruthy();
    expect(d.description).toBeTruthy();
    expect((d.description as string).length).toBeGreaterThan(50);
    expect(d.description).not.toContain("<");
  }, 120000);
});
