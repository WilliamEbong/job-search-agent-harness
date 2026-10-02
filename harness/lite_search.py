#!/usr/bin/env python3
"""Lite job search: every enabled portal, one compact ranked list, one command.

`/lite search` runs this in place of the job-scraper skill. The full route has the model
read the scrape command, the job-scraper skill and every portal SKILL.md, then parse raw
CLI JSON itself. Here the board quirks live in small tables below, and the model reads
at most 12 numbered rows.

    python harness/lite_search.py --top 5 --record
    python harness/lite_search.py --show 3     # one row, plus the command for its full text
    python harness/lite_search.py --save 3     # fetch and archive row 3 for /lite apply

Exit 0 = searched (even when nothing was new), 1 = every board failed, 2 = nothing to
search with (no preferences, positions, boards or bun); one printed line says which.

In order: search terms from `target_positions` (the recruiter pass), or `role_families`
plus trial families when there are none; each enabled `.agents/skills/*-search/` CLI once
per term (boards in parallel, one board's own calls in sequence); results near
`location.home`; repeats dropped (within the run, against `job_scraper/seen_jobs.json`,
against the tracker); a 0-100 score on job-title overlap, which is triage, not judgement.

It writes the full system's files in the full system's formats, so a user can move
between lite and full at any time: new jobs join `job_scraper/seen_jobs.json` (the store
`/rank` and `/upskill` read), the numbered list goes to `state/lite-last-search.json`, and
`--record` appends `shortlist.csv` rows (verdict `not-resolved`, /scrape's word for
title-level triage) and one `run_log.csv` row per board.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import yaml

HARNESS_DIR = Path(__file__).resolve().parent
ROOT = HARNESS_DIR.parent
sys.path.insert(0, str(HARNESS_DIR))
import run_log  # noqa: E402
import shortlist_row  # noqa: E402
import tracker_row  # noqa: E402

# Each board's SKILL.md documents its own flags. Most share `search -q <text> --limit N
# --format json`; these are the documented exceptions. A board added later with
# /add-portal gets the shared shape, and if that is wrong it fails on its own status line
# without stopping the run.
QUERY_FLAG = {"jobbank-search": "--key", "jobdanmark-search": "--text",
              "jobnet-search": "--search-string"}
# Only these document a free-text place flag. The others take region codes or nothing,
# so their results are filtered here on the location text instead.
LOCATION_FLAG = {"linkedin-search": "--location", "jobbank-ca-search": "--location"}
# jobnet results carry no URL; its SKILL.md documents the posting page pattern.
URL_TEMPLATE = {"jobnet-search": "https://jobnet.dk/job/{id}"}
# Boards that list one country's jobs. A home naming one of these countries skips the
# other countries' boards; a home naming none of them keeps every board.
MARKET = {"jobbank-ca-search": "canada", "jobbank-search": "denmark",
          "jobdanmark-search": "denmark", "jobindex-search": "denmark",
          "jobnet-search": "denmark"}
COUNTRY = {
    "canada": {"canada", "ab", "bc", "mb", "nb", "nl", "ns", "nt", "nu", "on", "pe", "qc",
               "sk", "yt", "alberta", "british columbia", "manitoba", "new brunswick",
               "newfoundland and labrador", "nova scotia", "ontario",
               "prince edward island", "quebec", "saskatchewan", "yukon"},
    "denmark": {"denmark", "danmark", "dk"},
}

TIMEOUT_S = 60
PAUSE_S = 5        # between one board's own calls: jobbank-ca's Crawl-delay, the strictest
MAX_ROWS = 10      # printed rows (lite shows 10); the rest stay in the saved list
MIN_SHOWN = 40     # a weaker title match is noise in the table (still saved for --show)
RECORD_TOP = 10    # shortlist rows per --record: lite presents at most 10 jobs
LAST_SEARCH = Path("state") / "lite-last-search.json"
STOPWORDS = {"a", "an", "and", "at", "for", "in", "of", "on", "or", "the", "to", "with"}


def norm(text) -> str:
    """Lowercase words joined by single spaces: the comparison form for every key."""
    return " ".join(re.findall(r"\w+", str(text or "").lower()))


def clip(text, width: int) -> str:
    text = str(text or "")
    return text if len(text) <= width else text[:width - 3] + "..."


def place(location, width: int = 30) -> str:
    """Clipped location that never loses its remote/hybrid/onsite tag."""
    location = str(location or "")
    match = re.search(r"\s*\((remote|hybrid|onsite)\)\s*$", location, re.I)
    tag = f" ({match[1].lower()})" if match else ""
    return clip(location[:match.start()] if match else location, width - len(tag)) + tag


def iso_date(value) -> str:
    """YYYY-MM-DD from ISO timestamps or jobdanmark's DD-MM-YYYY; '' for "ASAP" and the like."""
    text = str(value or "").strip()
    if re.match(r"\d{4}-\d{2}-\d{2}", text):
        return text[:10]
    match = re.match(r"(\d{2})-(\d{2})-(\d{4})", text)
    return f"{match[3]}-{match[2]}-{match[1]}" if match else ""


def normalise(raw: dict, board: str) -> dict:
    """One result in the shared shape, whatever the board called its fields."""
    def first(*keys) -> str:
        for key in keys:
            value = raw.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    job = {"title": first("title"),
           "company": first("company", "companyName", "hiringOrgName"),
           "location": first("location", "municipality", "postalDistrictName",
                             "companyAddress", "workPlaceAddress", "country"),
           "url": first("url"),
           "date": iso_date(first("date", "publicationDate", "publishedDate", "posted")),
           "deadline": iso_date(first("deadline", "applicationDeadline", "validThrough")),
           "id": first("id", "jobAdId", "slug"),
           "board": board}
    mode = first("work_mode")  # freehire: remote | hybrid | onsite
    if mode and mode.lower() not in job["location"].lower():
        job["location"] = f"{job['location']} ({mode})".strip()
    if not job["url"] and job["id"] and board in URL_TEMPLATE:
        job["url"] = URL_TEMPLATE[board].format(id=job["id"])
    return job


def home_tokens(home) -> list[str]:
    """'Winnipeg, Manitoba, Canada' -> ['winnipeg', 'manitoba', 'canada']; the city first."""
    return [token for token in (norm(part) for part in str(home or "").split(",")) if token]


def home_country(tokens: list[str]) -> str:
    return next((country for country, names in COUNTRY.items() if names & set(tokens)), "")


COUNTRY_WORDS = {"canada", "denmark", "danmark", "usa", "us", "united states", "uk",
                 "united kingdom", "ireland", "germany", "france", "netherlands", "sweden",
                 "norway", "australia", "new zealand", "india"}


def split_home(tokens: list[str]) -> tuple[list[str], str]:
    """(city and region, country). A country names a market, not a commute: matching
    it let 'North Vancouver, BC, Canada' through for a Winnipeg home."""
    if len(tokens) >= 3 or (len(tokens) == 2 and tokens[1] in COUNTRY_WORDS):
        return tokens[:-1], tokens[-1]
    return tokens, ""


def other_market(boards: list[str], tokens: list[str]) -> list[str]:
    """Single-country boards for a country that is not home; none when home is unknown."""
    country = home_country(tokens)
    return [b for b in boards if country and MARKET.get(b, country) != country]


def near_home(location, tokens: list[str], remote_ok: bool) -> bool:
    """A whole-word match on home's city or region; or, when remote is accepted, a
    remote listing that is open to home's country (or names no other place).

    Hybrid does not bypass the check: a hybrid role still has an office, and when that
    office is near home its city matches anyway.
    """
    places, country = split_home(tokens)
    text = f" {norm(location)} "
    if any(f" {token} " in text for token in places):
        return True
    if not (remote_ok and " remote " in text):
        return False
    rest = text.replace(" remote ", " ").strip()
    return (not rest or (country and f" {country} " in text)
            or any(f" {w} " in text for w in ("worldwide", "anywhere", "global")))


def words(text) -> set[str]:
    return {word for word in norm(text).split() if word not in STOPWORDS}


def score(title, phrases, location="", city="") -> int:
    """0-100: the best share of any phrase's words found in the title (worth up to 90),
    plus 10 when the location names the home city."""
    have = words(title)
    best = max((len(have & words(p)) / len(words(p)) for p in phrases if words(p)),
               default=0.0)
    bonus = 10 if city and f" {city} " in f" {norm(location)} " else 0
    return min(100, round(best * 90) + bonus)


def fit(points: int) -> str:
    return "high" if points >= 70 else "medium" if points >= 40 else "low"


def load_positions(prefs: dict, top: int) -> list[dict]:
    """What to search, in priority order: [{title, query, phrases, trial}].

    Active `target_positions` by rank, each searched on its first search term. With none,
    `role_families` plus trial families, the /scrape fallback. Empty = nothing to search.
    """
    block = prefs.get("target_positions")
    listed = block.get("positions") if isinstance(block, dict) else block
    active = [p for p in (listed if isinstance(listed, list) else [])
              if isinstance(p, dict) and str(p.get("title") or "").strip()
              and str(p.get("status") or "active").strip().lower() == "active"]
    active.sort(key=lambda p: p["rank"] if isinstance(p.get("rank"), int) else 10**6)
    out = []
    for position in active:
        title = str(position["title"]).strip()
        listed_terms = position.get("search_terms") or []
        if isinstance(listed_terms, str):  # one term written without list brackets
            listed_terms = [listed_terms]
        terms = [str(t).strip() for t in listed_terms if str(t).strip()]
        terms = terms or [title]
        out.append({"title": title, "query": terms[0], "phrases": [title] + terms,
                    "trial": False})
    if not out:
        families = prefs.get("role_families")
        discovery = prefs.get("discovery")
        trials = discovery.get("trial_families") if isinstance(discovery, dict) else None
        named = [(str(f).strip(), False)
                 for f in (families if isinstance(families, list) else []) if str(f).strip()]
        named += [(str(t["name"]).strip(), True)
                  for t in (trials if isinstance(trials, list) else [])
                  if isinstance(t, dict) and t.get("status") == "trial" and t.get("name")]
        out = [{"title": name, "query": name, "phrases": [name], "trial": trial}
               for name, trial in named]
    return out[:top]


def board_enabled(skill_text: str) -> bool:
    """A portal runs unless its SKILL.md frontmatter says `enabled: false`; missing = on."""
    if not skill_text.startswith("---"):
        return True
    try:
        meta = yaml.safe_load(skill_text.split("---", 2)[1])
    except (yaml.YAMLError, IndexError):
        return True
    if not isinstance(meta, dict):
        return True
    return str(meta.get("enabled", True)).strip().lower() not in ("false", "no", "off", "0")


def discover_boards(root: Path) -> tuple[list[str], list[str]]:
    """(enabled, disabled) portal names. Only `*-search` folders are portals; the other
    `.agents/skills/` entries are workflow pointer skills."""
    enabled, disabled = [], []
    for skill in sorted((root / ".agents" / "skills").glob("*-search/SKILL.md")):
        text = skill.read_text(encoding="utf-8", errors="replace")
        (enabled if board_enabled(text) else disabled).append(skill.parent.name)
    return enabled, disabled


def dedupe(jobs: list[dict], seen: dict, tracker_rows: list[dict]) -> list[dict]:
    """Drop repeats within the run (URL, then company+title+location), then anything
    seen_jobs.json holds (URL or company+title) or the tracker holds (company+role)."""
    entries = [entry for entry in seen.values() if isinstance(entry, dict)]
    seen_urls = set(seen) | {entry.get("url") for entry in entries}
    seen_pairs = {(norm(e.get("company")), norm(e.get("title"))) for e in entries}
    applied = {(norm(r.get("company")), norm(r.get("role"))) for r in tracker_rows}
    out, urls, triples = [], set(), set()
    for job in jobs:
        pair = (norm(job["company"]), norm(job["title"]))
        triple = (*pair, norm(job["location"]))
        if (job["url"] and job["url"] in urls) or triple in triples:
            continue
        urls.add(job["url"])
        triples.add(triple)
        if (job["url"] and job["url"] in seen_urls) or pair in seen_pairs or pair in applied:
            continue
        out.append(job)
    return out


def remember(data: dict, jobs: list[dict], today: str) -> int:
    """Add new jobs in the job-scraper's entry shape; existing entries are never touched."""
    seen, added = data["seen"], 0
    for job in jobs:
        key = job["url"] or "_".join(norm(f"{job['company']} {job['title']}").split())
        if key in seen:
            continue
        seen[key] = {"title": job["title"], "company": job["company"], "url": job["url"],
                     "first_seen": today, "fit": job["fit"], "status": "new",
                     "portal": job["board"]}
        added += 1
    return added


def read_seen(path: Path) -> tuple[dict, bool]:
    """(data, writable). An unreadable store is reported, and never overwritten."""
    if not path.exists():
        return {"seen": {}}, True
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig") or "{}")
    except (OSError, ValueError) as exc:
        print(f"WARNING: {path} is unreadable ({str(exc)}); not deduplicating against "
              "it and not updating it")
        return {"seen": {}}, False
    if not isinstance(data, dict) or not isinstance(data.setdefault("seen", {}), dict):
        print(f"WARNING: {path} has no 'seen' mapping; left untouched")
        return {"seen": {}}, False
    return data, True


def write_json(path: Path, data) -> None:
    """Atomic: a crash mid-write never leaves half a file behind."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def cli_error(proc: subprocess.CompletedProcess) -> str:
    """The CLI's own message; by the portal contract stderr is {"error": ..., "code": ...}."""
    text = (proc.stderr or "").strip()
    try:
        return str(json.loads(text.splitlines()[-1])["error"])[:120]
    except (ValueError, IndexError, KeyError, TypeError):
        pass
    if proc.returncode == 0:
        return "output was not JSON"
    return str(text.splitlines()[-1] if text else f"exit code {proc.returncode}")[:120]


def run_board(bun: str, root: Path, board: str, queries: list[str], home: str,
              limit: int) -> dict:
    """One board's queries in order. Stops at the first error: a blocked or rate-limited
    board fails every call the same way, and retrying it is impolite as well as slow."""
    cli = root / ".agents" / "skills" / board / "cli" / "src" / "cli.ts"
    run = {"board": board, "jobs": [], "found": 0, "error": "", "note": "",
           "post_filter": not (home and board in LOCATION_FLAG)}
    for number, query in enumerate(queries, 1):
        if number > 1:
            time.sleep(PAUSE_S)
        cmd = [bun, "run", str(cli), "search", QUERY_FLAG.get(board, "-q"), query,
               "--limit", str(limit), "--format", "json"]
        if home and board in LOCATION_FLAG:
            cmd += [LOCATION_FLAG[board], home]
        where = f"query {number}/{len(queries)}"
        try:
            proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=TIMEOUT_S)
        except subprocess.TimeoutExpired:
            run["error"] = f"{where} timed out after {TIMEOUT_S}s"
            break
        except OSError as exc:
            run["error"] = f"{where}: {str(exc)}"
            break
        try:
            payload = json.loads(proc.stdout) if proc.returncode == 0 else None
        except ValueError:
            payload = None
        if not isinstance(payload, dict):
            run["error"] = f"{where}: {cli_error(proc)}"
            break
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        if "none" in str(meta.get("location_filter", "")).lower():
            # jobbank-ca says so when it could not turn the place into a province filter.
            run["post_filter"], run["note"] = True, f"board: {meta['location_filter']}"
        rows = [row for row in payload.get("results") or [] if isinstance(row, dict)]
        run["found"] += len(rows)
        run["jobs"] += [normalise(row, board) for row in rows]
    return run


def log_runs(path: Path, runs: list[dict], queries: list[str]) -> None:
    """One run_log.csv row per board."""
    for run in runs:
        notes = "lite" + (f"; error: {run['error']}" if run["error"] else "") \
            + (f"; {run['note']}" if run["note"] else "")
        run_log.append({"portal": run["board"], "query": "; ".join(queries),
                        "found": run["found"], "new": run["new"], "notes": notes}, path)


def search(args) -> int:
    root = Path(args.root)
    prefs_path = Path(args.preferences) if args.preferences else root / "preferences.yaml"
    if not prefs_path.is_file():
        print(f"lite_search: no preferences at {prefs_path} - run /lite setup first")
        return 2
    try:
        prefs = yaml.safe_load(prefs_path.read_text(encoding="utf-8-sig")) or {}
    except yaml.YAMLError as exc:
        print(f"lite_search: {prefs_path.name} does not parse ({str(exc)})")
        return 2
    positions = load_positions(prefs if isinstance(prefs, dict) else {}, args.top)
    if not positions:
        print("lite_search: preferences.yaml has no active target_positions and no "
              "role_families - run /recruiter first")
        return 2

    location = prefs.get("location") if isinstance(prefs.get("location"), dict) else {}
    home = str(location.get("home") or "").strip()
    tokens = home_tokens(home)
    remote_ok = "remote" in [str(a).strip().lower() for a in location.get("arrangements") or []]

    enabled, disabled = discover_boards(root)
    elsewhere = other_market(enabled, tokens)
    boards = [b for b in enabled if b not in elsewhere]
    if args.boards:
        elsewhere = []
        boards = [b if b.endswith("-search") else b + "-search"
                  for b in (part.strip() for part in args.boards.split(",")) if b]
        unknown = [b for b in boards if b not in enabled + disabled]
        if unknown:
            print(f"lite_search: no board named {', '.join(unknown)}; installed: "
                  f"{', '.join(enabled + disabled)}")
            return 2
        disabled = []
    if not boards:
        print("lite_search: no enabled boards under .agents/skills/*-search/")
        return 2
    bun = shutil.which("bun")
    if not bun:
        print("lite_search: bun is not installed, and every portal CLI needs it - "
              "run: python harness_setup.py --doctor")
        return 2

    queries = [position["query"] for position in positions]
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(boards)) as pool:
        runs = list(pool.map(
            lambda board: run_board(bun, root, board, queries, home, args.limit), boards))

    pooled = []
    country = home_country(tokens)
    for run in runs:
        jobs = [job for job in run["jobs"] if job["title"]]
        # A home-country national board without a place flag (the Danish ones) lists
        # places in its own language ("København K" for a "Copenhagen" home), so its
        # rows go to the model's location screen instead of being dropped here.
        if run["post_filter"] and tokens and MARKET.get(run["board"]) != country:
            jobs = [job for job in jobs if near_home(job["location"], tokens, remote_ok)]
        run["near"] = len(jobs)
        pooled += jobs
    seen_path = (Path(args.state_dir) if args.state_dir else root / "job_scraper") \
        / "seen_jobs.json"
    data, writable = read_seen(seen_path)
    tracker, _ = tracker_row.read_rows(root / "job_search_tracker.csv")
    fresh = dedupe(pooled, data["seen"], tracker)
    city = tokens[0] if tokens else ""
    for job in fresh:
        # Against every searched position: one query's find may fit another position better.
        job["score"], job["position"], job["trial"] = max(
            ((score(job["title"], p["phrases"], job["location"], city), p["title"],
              p["trial"]) for p in positions), key=lambda match: match[0])
        job["fit"] = fit(job["score"])
    fresh.sort(key=lambda job: (job["score"], job["date"]), reverse=True)
    for number, job in enumerate(fresh, 1):
        job["n"] = number
    for run in runs:
        run["new"] = sum(1 for job in fresh if job["board"] == run["board"])

    today = date.today().isoformat()
    added = remember(data, fresh, today) if writable else 0
    if added:
        write_json(seen_path, data)
    if fresh:  # a repeat search with nothing new keeps the list --show/--save refer to
        write_json(root / LAST_SEARCH, {"date": today, "home": home,
                                        "positions": [p["title"] for p in positions],
                                        "results": fresh})
    shown = [job for job in fresh if job["score"] >= MIN_SHOWN][:MAX_ROWS]
    recorded = []
    if args.record:
        for job in shown[:RECORD_TOP]:
            rationale = f"lite title match: {job['position']}" \
                + (f"; trial: {job['position']}" if job["trial"] else "")
            shortlist_row.append({
                "company": job["company"], "role": job["title"],
                "location": job["location"], "source": job["board"], "url": job["url"],
                "score": job["score"], "verdict": "not-resolved", "rationale": rationale,
                "deadline": job["deadline"]}, root / "shortlist.csv")
        log_runs(root / "run_log.csv", runs, queries)
        recorded = [f"{min(len(shown), RECORD_TOP)} shortlist row(s) (not-resolved)",
                    f"{len(runs)} run-log row(s)"]
    # Every board failing is "could not search", never "no new jobs".
    failed = all(run["error"] and not run["found"] for run in runs)

    where = str(home) + (" (+remote)" if remote_ok else "") if home \
        else "not set, so results are not location-filtered"
    print(f"lite search {today} - {len(positions)} position(s), {len(runs)} board(s), "
          f"home: {where}")
    for run in runs:
        name = run["board"].ljust(19)
        if run["error"] and not run["found"]:
            print(f"  {name} FAILED {run['error']}")
            continue
        near = f", {run['near']} near home" if run["post_filter"] and tokens else ""
        extra = "; ".join(x for x in (run["note"] and clip(run["note"], 70),
                                      run["error"] and "stopped at " + run["error"]) if x)
        print(f"  {name} {run['found']} found{near}, {run['new']} new"
              + (f"  [{extra}]" if extra else ""))
    if disabled:
        print(f"  skipped (disabled): {', '.join(disabled)}")
    if elsewhere:
        print(f"  skipped (another country): {', '.join(elsewhere)}")
    if shown:
        print("\n  # match  title | company | location")
    for job in shown:
        print(f"{job['n']:>3} {job['score']:>5}  {clip(job['title'], 55)}"
              f" | {clip(job['company'], 28)} | {place(job['location'])}")
    more = f" (showing {len(shown)}, title match {MIN_SHOWN}+)" if len(shown) < len(fresh) else ""
    store = f"{seen_path.name} +{added}" if writable else f"{seen_path.name} NOT updated"
    if failed:
        print("\nEvery board failed, so nothing was searched. This is not 'no new jobs'.")
        return 1
    print(f"\n{len(fresh)} new job(s){more}; {store}"
          + (f"; recorded {', '.join(recorded)}" if recorded else ""))
    return 0


def last_row(root: Path, number: int) -> tuple[dict, str] | None:
    """(row, search date) from the saved list; None, with the reason printed."""
    try:
        data = json.loads((root / LAST_SEARCH).read_text(encoding="utf-8-sig"))
        rows = data["results"]
    except (OSError, ValueError, KeyError, TypeError):
        print("lite_search: no saved search - run /lite search first")
        return None
    if not 1 <= number <= len(rows):
        print(f"lite_search: no row {number}; the search of {data.get('date')} "
              f"has {len(rows)}")
        return None
    return rows[number - 1], data.get("date")


def save(args) -> int:
    """Fetch row N's posting with its board's `detail` command and archive it the way
    apply_package.py requires (posting_source/, job_posting.md, provenance.md), then
    print the text. The model reads the posting once and never has to retype it."""
    root = Path(args.root)
    found = last_row(root, args.save)
    if not found:
        return 2
    job = found[0]
    bun = shutil.which("bun")
    if not bun or not job["id"]:
        print(f"lite_search: no {'bun' if not bun else 'job id'} to fetch the text with; "
              f"fetch {job['url'] or 'the posting'} instead")
        return 1
    cli = root / ".agents" / "skills" / job["board"] / "cli" / "src" / "cli.ts"
    try:
        proc = subprocess.run([bun, "run", str(cli), "detail", str(job["id"]), "--format",
                               "plain"], cwd=root, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=TIMEOUT_S)
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"lite_search: detail failed ({exc}); fetch {job['url']} instead")
        return 1
    import apply_package  # only here: it is the owner of the folder name
    body = (proc.stdout or "").strip()
    if proc.returncode != 0 or len(body) < apply_package.MIN_POSTING_CHARS:
        why = cli_error(proc) if proc.returncode else "the text came back nearly empty"
        print(f"lite_search: detail failed ({why}); fetch {job['url']} instead")
        return 1
    meta = {"company": job["company"], "role": job["title"], "url": job["url"],
            "location": job["location"], "channel": job["board"],
            "deadline": job.get("deadline", "")}
    return archive(root, meta, body, f"{job['board']}_detail.md",
                   f"/lite search row {args.save}: {job['board']} detail {job['id']}",
                   "verified")


def archive(root: Path, meta: dict, body: str, raw_name: str, source: str,
            state: str) -> int:
    """Write what apply_package.py's archive check needs (the raw text in
    posting_source/, job_posting.md, provenance.md), then start the application."""
    import apply_package  # the owner of the folder name
    folder = (root / "documents" / "applications"
              / apply_package.folder_name(meta["company"], meta["role"]))
    today = date.today().isoformat()
    (folder / "posting_source").mkdir(parents=True, exist_ok=True)
    (folder / "posting_source" / raw_name).write_text(
        f"source: {source}\nsaved: {today}\n\n{body}\n", encoding="utf-8")
    (folder / "job_posting.md").write_text(
        f"# {meta['role']} - {meta['company']}\n\n{meta.get('location', '')} | "
        f"{meta.get('url', '')}\n\n{body}\n", encoding="utf-8")
    (folder / "provenance.md").write_text(
        f"# Provenance\n\n- date: {today}\n- source: {source}\n- url: {meta.get('url', '')}\n"
        f"- posting_state: {state}\n", encoding="utf-8")
    return start(root, meta, body)


def start_from(root: Path, path: str) -> int:
    """A URL, pasted or file posting: archive its text from `path`, so the model writes
    the posting at most once (a URL's or a paste's text) and never in two formats."""
    import apply_package
    meta = load_meta(root)
    if meta is None:
        return 2
    try:
        body = Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError as exc:
        print(f"lite_search: cannot read {path} ({exc})")
        return 2
    if len(body) < apply_package.MIN_POSTING_CHARS:
        print(f"lite_search: {path} holds {len(body)} characters - too little for a "
              "posting; ask for the full text")
        return 2
    return archive(root, meta, body, "posting.md",
                   f"{meta.get('channel') or 'file'}: {Path(path).name}",
                   meta.get("posting_state") or "unverified")


# The posting being applied to. Company, role and URL come from a posting, which is
# untrusted text: they travel from this file into the recording scripts as Python
# values, never through a shell command line where `$`, backticks or `$(...)` would
# be expanded.
APPLYING = Path("state") / "lite-apply.json"


def load_meta(root: Path) -> dict | None:
    """The JSON the model wrote for a posting that did not come from a search row."""
    try:
        meta = json.loads((root / APPLYING).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        print(f"lite_search: write {APPLYING.as_posix()} first (company, role, url, "
              "location, channel)")
        return None
    return meta if isinstance(meta, dict) else None


def mark_seen(root: Path, url: str, status: str) -> None:
    """Keep the shared seen_jobs.json (read by /rank and /upskill) in step with a
    lite verdict; a job not in it (a pasted posting) is left alone."""
    path = root / "job_scraper" / "seen_jobs.json"
    if not url or not path.is_file():
        return
    data, writable = read_seen(path)
    entry = data["seen"].get(url)
    if writable and isinstance(entry, dict):
        entry["status"] = status
        write_json(path, data)


def start(root: Path, meta: dict | None = None, body: str = "") -> int:
    """Fix the application folder and slug for the posting in APPLYING (or `meta`)."""
    import apply_package  # the owner of the folder name
    if meta is None:
        try:
            meta = json.loads((root / APPLYING).read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            print(f"lite_search: write {APPLYING.as_posix()} first (company, role, url, "
                  "location, channel)")
            return 2
    if not (str(meta.get("company") or "").strip() and str(meta.get("role") or "").strip()):
        print(f"lite_search: {APPLYING.as_posix()} needs a company and a role")
        return 2
    folder = (root / "documents" / "applications"
              / apply_package.folder_name(meta["company"], meta["role"]))
    (folder / "posting_source").mkdir(parents=True, exist_ok=True)
    meta.update(folder=folder.relative_to(root).as_posix(),
                slug=apply_package.slugify(meta["company"], meta["role"]))
    write_json(root / APPLYING, meta)
    print(f"folder: {meta['folder']}\nslug: {meta['slug']}\n"
          f"company: {meta['company']}\nrole: {meta['role']}"
          + (f"\n\n{body}" if body else ""))
    return 0


def applying(root: Path) -> dict | None:
    try:
        meta = json.loads((root / APPLYING).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        meta = {}
    if not meta.get("folder"):
        print("lite_search: no posting in progress - run --save N or --start first")
        return None
    return meta


def record(root: Path, meta: dict, verdict: str, score, rationale: str) -> None:
    shortlist_row.append({
        "company": meta["company"], "role": meta["role"],
        "location": meta.get("location", ""), "source": meta.get("channel", ""),
        "url": meta.get("url", ""), "score": score or "", "verdict": verdict,
        "rationale": rationale, "deadline": meta.get("deadline", "")},
        root / "shortlist.csv")
    print(f"shortlist: {verdict} - {meta['company']} - {meta['role']}")


def package(root: Path, score, rationale: str) -> int:
    """apply_package.py for the posting in progress, then its `qualified` row."""
    import apply_package
    meta = applying(root)
    if not meta:
        return 2
    folder = root / meta["folder"]
    source = folder / "posting_source"
    if (folder / "job_posting.md").is_file() and not any(source.glob("*")):
        # A pasted or fetched posting: its text is the raw artifact the archive needs.
        shutil.copy(folder / "job_posting.md", source / "posting.md")
    code = apply_package.main([
        "--company", meta["company"], "--role", meta["role"],
        "--cv", f"cv/main_{meta['slug']}.tex",
        "--letter", f"cover_letters/cover_{meta['slug']}.tex",
        "--url", meta.get("url", ""), "--score", str(score or ""),
        "--location", meta.get("location", ""), "--channel", meta.get("channel", ""),
        "--rationale", rationale])
    if code == 0:
        record(root, meta, "qualified", score, rationale)
        mark_seen(root, meta.get("url", ""), "evaluated")
    return code


def applied(root: Path, status: str, match: str = "") -> int:
    """Record a submission (status in_progress) or an outcome. Without `match` it is
    the posting in progress; with it, the one tracker row whose company contains the
    word, so an older application needs no company name typed into a shell."""
    if match:
        rows, _ = tracker_row.read_rows(tracker_row.TRACKER_CSV)
        hits = sorted({(r.get("company", ""), r.get("role", "")) for r in rows
                       if match.lower() in (r.get("company") or "").lower()})
        if len(hits) != 1:
            print(f"lite_search: {len(hits)} tracker rows match '{match}'"
                  + "".join(f"\n  {c} - {r}" for c, r in hits)
                  + ("\nuse a word only one company has" if hits else ""))
            return 1
        meta = {"company": hits[0][0], "role": hits[0][1]}
    else:
        meta = applying(root)
        if not meta:
            return 2
    changes = {"status": status}
    if status == "in_progress":
        today = date.today().isoformat()
        changes.update(submitted_date=today, notes=f"submitted {today}")
    updated = tracker_row.update(meta["company"], meta["role"], changes,
                                 tracker_row.TRACKER_CSV)
    if not updated:
        print("lite_search: no tracker row for it - run --package first")
        return 1
    print(f"tracker: {meta['company']} - {meta['role']}: {status}")
    if not match:
        (root / APPLYING).unlink(missing_ok=True)  # done with; the next posting starts clean
    return 0


def show(args) -> int:
    found = last_row(Path(args.root), args.show)
    if not found:
        return 2
    job, searched = found
    print(f"#{args.show} {str(job['title'])} | {str(job['company'])} | "
          f"{str(job['location'])}   (search of {searched})")
    print(f"posted {job['date'] or '-'}, closes {job['deadline'] or '-'}, title match "
          f"{job['score']} against {str(job['position'])}")
    print(f"url: {str(job['url']) or '-'}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--preferences", help="default: <root>/preferences.yaml")
    parser.add_argument("--state-dir", help="folder holding seen_jobs.json; default "
                        "<root>/job_scraper, the store /rank and /upskill read")
    parser.add_argument("--top", type=int, default=5,
                        help="how many target positions to search (default 5)")
    parser.add_argument("--boards", help="comma-separated portals, e.g. linkedin,jobindex "
                        "(default: every enabled board)")
    parser.add_argument("--limit", type=int, default=10,
                        help="results per query per board (default 10)")
    parser.add_argument("--record", action="store_true",
                        help=f"append the top {RECORD_TOP} to shortlist.csv as not-resolved "
                        "and one run_log.csv row per board")
    parser.add_argument("--show", type=int, metavar="N",
                        help="print row N of the last search and the command for its text")
    parser.add_argument("--save", type=int, metavar="N",
                        help="fetch row N's posting and archive it for /lite apply")
    parser.add_argument("--start", action="store_true",
                        help=f"folder and slug for the posting in {APPLYING.as_posix()}")
    parser.add_argument("--from", dest="from_file", metavar="FILE",
                        help="with --start: archive the posting text in FILE")
    parser.add_argument("--match", metavar="WORD",
                        help="with --applied: the tracker row whose company contains WORD")
    parser.add_argument("--gate-fail", type=int, metavar="N",
                        help="record search row N as gate-fail (with --rationale)")
    parser.add_argument("--verdict", choices=shortlist_row.VERDICTS,
                        help="record the posting in progress with this verdict")
    parser.add_argument("--package", action="store_true",
                        help="build the package for the posting in progress, then record "
                        "it as qualified")
    parser.add_argument("--applied", nargs="?", const="in_progress", metavar="STATUS",
                        help="the posting in progress was submitted today (or set STATUS, "
                        "e.g. rejected)")
    parser.add_argument("--score", help="fit score for --verdict / --package")
    parser.add_argument("--rationale", default="",
                        help="one line in your own words (no quotes, $ or backticks)")
    args = parser.parse_args(argv)
    if args.top < 1 or args.limit < 1:
        parser.error("--top and --limit must be at least 1")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # postings are not ASCII
    root = Path(args.root)
    if args.save is not None:
        return save(args)
    if args.start:
        return start_from(root, args.from_file) if args.from_file else start(root)
    if args.gate_fail is not None:
        found = last_row(root, args.gate_fail)
        if not found:
            return 2
        job = found[0]
        record(root, {"company": job["company"], "role": job["title"],
                      "location": job["location"], "channel": job["board"],
                      "url": job["url"]}, "gate-fail", job.get("score"), args.rationale)
        mark_seen(root, job["url"], "skipped")
        return 0
    if args.verdict:
        meta = applying(root)
        if not meta:
            return 2
        record(root, meta, args.verdict, args.score, args.rationale)
        if args.verdict in ("gate-fail", "not-drafted"):  # nothing more will happen to it
            mark_seen(root, meta.get("url", ""),
                      "skipped" if args.verdict == "gate-fail" else "evaluated")
            (root / APPLYING).unlink(missing_ok=True)
        return 0
    if args.package:
        return package(root, args.score, args.rationale)
    if args.applied:
        return applied(root, args.applied, args.match or "")
    return show(args) if args.show is not None else search(args)


if __name__ == "__main__":
    sys.exit(main())
