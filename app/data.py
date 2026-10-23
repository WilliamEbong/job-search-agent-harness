"""Read the harness's own files into what the app's screens show, and the few small writes
the app makes without the assistant (marking an application sent, striking a position,
settings). Every other write belongs to the harness scripts and workflows."""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import yaml

HARNESS = Path(__file__).resolve().parent.parent / "harness"
sys.path.insert(0, str(HARNESS))
import archive_applications  # noqa: E402
import status as status_mod  # noqa: E402
import today as today_mod  # noqa: E402
import tracker_row  # noqa: E402

from app import engines, tasks  # noqa: E402

SETTINGS = Path("state") / "app-settings.json"
DEFAULTS = {"engine": "auto", "search_top": 5, "screen_after_search": True}
UPLOAD_TYPES = {".pdf", ".docx", ".doc", ".txt", ".md", ".png", ".jpg", ".jpeg"}
STATUS_LABELS = {
    "interview_only": "Interview", "hired": "Hired", "offer_declined": "Offer declined",
    "rejected": "Rejected", "no_response": "No response", "withdrawn": "Withdrawn",
}


# -- small helpers ---------------------------------------------------------------
def _yaml(path: Path) -> dict | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except (OSError, yaml.YAMLError):
        return None
    return data if isinstance(data, dict) else None


def _csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "cp1252"):  # a file Excel re-saved is often cp1252
        try:
            with path.open(newline="", encoding=encoding) as handle:
                return [{k: (v or "") if isinstance(v, str) else "" for k, v in row.items() if k}
                        for row in csv.DictReader(handle)]
        except UnicodeDecodeError:
            continue
    return []


def _int(value) -> int | None:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def inside(root: Path, relative: str, base: str = "documents") -> Path | None:
    """`relative` resolved under root/base, or None if it escapes (.., drive, link)."""
    if not relative or "\x00" in relative or relative.startswith(("/", "\\")) \
            or Path(relative).is_absolute() or Path(relative).drive:
        return None  # before resolve(): a \\host\share path would make Windows call out
    allowed = (root / base).resolve()
    target = (root / relative).resolve()
    return target if target == allowed or allowed in target.parents else None


# -- settings ----------------------------------------------------------------------
def settings(root: Path) -> dict:
    try:
        saved = json.loads((root / SETTINGS).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        saved = {}
    merged = {**DEFAULTS, **{k: v for k, v in saved.items() if k in DEFAULTS}}
    merged["mode"] = today_mod.usage_mode(root) or "lite"
    if merged["mode"] not in ("lite", "standard"):
        merged["mode"] = "standard"
    return merged


def save_settings(root: Path, changes: dict) -> dict:
    current = settings(root)
    if "engine" in changes:
        if changes["engine"] not in ("auto", *engines.ENGINES):
            raise ValueError("Choose Auto, Claude or Codex.")
        current["engine"] = changes["engine"]
    if "search_top" in changes:
        top = _int(changes["search_top"])
        if top is None or not 1 <= top <= 20:
            raise ValueError("Search between 1 and 20 roles at a time.")
        current["search_top"] = top
    if "screen_after_search" in changes:
        current["screen_after_search"] = bool(changes["screen_after_search"])
    if "mode" in changes:
        if changes["mode"] not in ("lite", "standard"):
            raise ValueError("Mode is lite or standard.")
        prefs = _yaml(root / "preferences.yaml")
        if prefs is None:
            if (root / "preferences.yaml").exists():
                raise ValueError("preferences.yaml could not be read, so it was left as it is.")
            prefs = {}
        usage = prefs.get("usage") if isinstance(prefs.get("usage"), dict) else {}
        # The harness's standard modes are focused | balanced | full; keep one already set.
        if changes["mode"] == "lite":
            usage["mode"] = "lite"
        elif usage.get("mode") in (None, "", "lite"):
            usage["mode"] = "focused"
        prefs["usage"] = usage
        write_preferences(root, prefs)
        current["mode"] = changes["mode"]
    path = root / SETTINGS
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: current[k] for k in DEFAULTS}, indent=2), encoding="utf-8")
    return current


def write_preferences(root: Path, prefs: dict) -> None:
    """Rewrite preferences.yaml, keeping the previous copy as preferences.yaml.bak.
    ponytail: comments in the file are not kept; the workflows write it without any."""
    path = root / "preferences.yaml"
    if path.exists():
        shutil.copy2(path, path.with_name("preferences.yaml.bak"))
    tmp = path.with_name("preferences.yaml.tmp")
    tmp.write_text(yaml.safe_dump(prefs, sort_keys=False, allow_unicode=True), encoding="utf-8")
    os.replace(tmp, path)


def _positions(prefs: dict) -> list[dict]:
    """target_positions as lite_search reads it: a mapping with `positions`, or a bare list."""
    block = prefs.get("target_positions")
    found = block.get("positions") if isinstance(block, dict) else block
    return [p for p in found if isinstance(p, dict)] if isinstance(found, list) else []


def engine_for(root: Path, kind: str, installed: dict | None = None) -> str | None:
    """Which engine runs a task. Auto: Codex for the long application and screening
    loops when it is installed, Claude for the rest; either one alone runs everything."""
    have = installed if installed is not None else {
        name: bool(engines.resolve(name)) for name in engines.ENGINES}
    chosen = settings(root)["engine"]
    if chosen != "auto":
        return chosen if have.get(chosen) else None
    order = ("codex", "claude") if kind in ("apply", "screen") else ("claude", "codex")
    return next((name for name in order if have.get(name)), None)


# -- screens -----------------------------------------------------------------------
def setup_state(root: Path) -> dict:
    prefs = _yaml(root / "preferences.yaml") or {}
    positions = _positions(prefs)
    cv_dir = root / "documents" / "cv"
    cvs = sorted(p for p in cv_dir.glob("*") if p.suffix.lower() in UPLOAD_TYPES) \
        if cv_dir.is_dir() else []
    has_register = (root / "evidence" / "register.yaml").exists()
    return {"has_register": has_register, "has_preferences": bool(prefs),
            "has_positions": any(str(p.get("status") or "active").strip().lower() == "active"
                                 for p in positions),
            "onboarded": has_register and bool(prefs),
            "cv_files": [p.relative_to(root).as_posix() for p in cvs]}


def state(root: Path) -> dict:
    today = today_mod.collect(root=root)
    jobs = last_search(root)
    apps = applications(root)
    return {
        "setup": setup_state(root),
        "settings": settings(root),
        "today": today,
        "counts": {
            "jobs_new": sum(1 for job in (jobs or {}).get("results", [])
                            if not job["verdict"] and not job["applied"]),
            "applications_open": sum(1 for a in apps if status_mod.is_open(a["status"])),
            "ready_to_send": sum(1 for a in apps if a["status_label"] == "Ready to send"),
        },
    }


def last_search(root: Path) -> dict | None:
    try:
        data = json.loads((root / "state" / "lite-last-search.json").read_text(encoding="utf-8-sig"))
        rows = data["results"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    verdicts = {row.get("url"): row for row in _csv(root / "shortlist.csv") if row.get("url")}
    tracked = {row.get("source") for row in tracker_row.read_rows(root / "job_search_tracker.csv")[0]}
    results = []
    for number, job in enumerate(rows, 1):
        if not isinstance(job, dict):
            continue
        listed = verdicts.get(job.get("url")) or {}
        verdict = listed.get("verdict", "")
        results.append({
            "number": number, "title": str(job.get("title", "")),
            "company": str(job.get("company", "")), "location": str(job.get("location", "")),
            "url": str(job.get("url", "")), "date": str(job.get("date", "")),
            "deadline": str(job.get("deadline", "")), "board": str(job.get("board", "")),
            "score": _int(job.get("score")),
            "verdict": "" if verdict == "not-resolved" else verdict,
            "rationale": listed.get("rationale", "") if verdict != "not-resolved" else "",
            "applied": bool(job.get("url")) and job.get("url") in tracked,
        })
    return {"date": data.get("date", ""), "home": data.get("home", ""),
            "positions": data.get("positions") or [], "results": results}


def jobs(root: Path) -> dict:
    history = _csv(root / "shortlist.csv")
    for row in history:
        row["score"] = _int(row.get("score"))
    return {"search": last_search(root), "history": history[::-1]}


def _file_kind(name: str) -> str:
    low = name.lower()
    if low.startswith("resume & cover letter"):
        return "combined"
    if low.startswith("resume"):
        return "cv"
    if low.startswith("cover letter"):
        return "letter"
    if low.startswith("job_posting"):
        return "posting"
    if low.startswith("ats"):
        return "ats"
    return "other"


def _folders(root: Path) -> dict[str, Path]:
    base = root / "documents" / "applications"
    found = {}
    for parent in (base, base / "applied"):
        if parent.is_dir():
            for folder in parent.iterdir():
                if folder.is_dir() and folder.name not in archive_applications.RESERVED:
                    found[folder.name] = folder
    return found


def applications(root: Path) -> list[dict]:
    rows, _ = tracker_row.read_rows(root / "job_search_tracker.csv")
    merged: dict[tuple, dict] = {}
    for row in rows:  # one application can have several rows; later rows win, blanks don't
        key = ((row.get("company") or "").strip().lower(), (row.get("role") or "").strip().lower())
        if not key[0]:
            continue
        entry = merged.setdefault(key, {})
        entry.update({k: v for k, v in row.items() if (v or "").strip()})
    folders = _folders(root)
    today = date.today()
    out = []
    for entry in merged.values():
        company, role = entry.get("company", ""), entry.get("role", "")
        status = status_mod.normalize(entry.get("status")) or "in_progress"
        submitted = entry.get("submitted_date", "")
        name = archive_applications.match_folder(company, role, list(folders)) or ""
        folder = folders.get(name)
        files = []
        if folder:
            for path in sorted(folder.iterdir()):
                if path.is_file() and path.suffix.lower() in (".pdf", ".md", ".docx"):
                    files.append({"name": path.name, "path": path.relative_to(root).as_posix(),
                                  "kind": _file_kind(path.name), "ext": path.suffix[1:].lower()})
        if status == "in_progress":
            label = "Sent, waiting" if submitted else "Ready to send"
        else:
            label = STATUS_LABELS.get(status, status.replace("_", " ").capitalize())
        stages = ["found"]
        if folder or entry.get("cv_file"):
            stages.append("drafted")
        if submitted or status != "in_progress":
            stages.append("sent")
        if status in ("interview_only", "hired", "offer_declined"):
            stages.append("interview")
        if status in ("hired", "offer_declined"):
            stages.append("offer")
        stages += {"hired": ["hired"], "rejected": ["rejected"], "no_response": ["no_response"],
                   "withdrawn": ["withdrawn"], "offer_declined": ["declined"]}.get(status, [])
        out.append({
            "id": name or f"{company}_{role}", "company": company, "role": role,
            "status": status, "status_label": label, "fit": _int(entry.get("fit_rating")),
            "date": entry.get("date", ""), "submitted_date": submitted,
            "location": entry.get("location", ""), "source": entry.get("source", ""),
            "rationale": entry.get("rationale", ""),
            "followups_sent": today_mod.followups_sent(entry),
            "days_quiet": today_mod.days_quiet(entry, today), "stages": stages,
            "folder": folder.relative_to(root).as_posix() if folder else "", "files": files,
        })
    for number, entry in enumerate(sorted(out, key=lambda a: a["date"]), 1):
        entry["number"] = number  # oldest first, so a number never changes as new ones arrive
    out.sort(key=lambda a: (a["submitted_date"] or a["date"]), reverse=True)
    return out


def mark(root: Path, company: str, role: str, status: str, sent: bool) -> None:
    """The person's own report: they sent it, or an outcome came back. Goes through the
    harness's tracker script, then lets the archiver move a sent package to applied/."""
    if not role.strip():
        raise ValueError("Choose an application first.")
    if not sent:
        status = status_mod.normalize(status)
        if status not in status_mod.CANONICAL:
            raise ValueError("Unknown status.")
    path = root / "job_search_tracker.csv"
    rows, _ = tracker_row.read_rows(path)
    key = (company.strip().lower(), role.strip().lower())
    hits = [row for row in rows if ((row.get("company") or "").strip().lower(),
                                     (row.get("role") or "").strip().lower()) == key]
    if not hits:  # exact match only: "Data Analyst" must never also mark "Senior Data Analyst"
        raise LookupError("That application is not in the tracker.")
    today = date.today().isoformat()
    for row in hits:
        if sent:
            notes = (row.get("notes") or "").strip()  # keep "followed up" history
            row.update(status="in_progress", submitted_date=today,
                       notes=f"{notes}; submitted {today}" if notes else f"submitted {today}")
        else:
            row["status"] = status
    tracker_row.write_rows(rows, path)
    if root.resolve() == HARNESS.parent:  # the archiver works on the live tree only
        archive_applications.move_applied()


def profile(root: Path) -> dict:
    reg = _yaml(root / "evidence" / "register.yaml")
    register = None
    if reg:
        meta = reg.get("meta") or {}

        def items(key):
            value = reg.get(key)
            return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []

        register = {
            "owner": meta.get("owner", ""), "location": meta.get("location", ""),
            "email": meta.get("email", ""), "phone": str(meta.get("phone", "")),
            "employers": [{"name": e.get("name", ""), "titles": [
                {"title": t.get("title", ""), "start": str(t.get("start", "")),
                 "end": str(t.get("end", ""))} for t in e.get("titles") or [] if isinstance(t, dict)]}
                for e in items("employers")],
            "education": [{"degree": e.get("degree", ""), "institution": e.get("institution", ""),
                           "status": e.get("status", "")} for e in items("education")],
            "credentials": [{"name": c.get("name", ""), "status": c.get("status", ""),
                             "qualifier": c.get("qualifier_required", "")}
                            for c in items("credentials")],
            "technologies": [{"name": t.get("name", ""), "ceiling": str(t.get("claim_ceiling", ""))}
                             for t in items("technologies")],
            "metrics": [{"value": str(m.get("value", "")), "claim": m.get("claim", "")}
                        for m in items("metrics")],
            "entries": sum(len(v) for v in reg.values() if isinstance(v, list)),
        }
    prefs = _yaml(root / "preferences.yaml") or {}
    positions = [{k: p.get(k) for k in ("rank", "title", "fit", "tier", "because", "gap")}
                 | {"status": p.get("status", "active")} for p in _positions(prefs)]
    location = prefs.get("location") if isinstance(prefs.get("location"), dict) else {}
    pay = prefs.get("compensation") if isinstance(prefs.get("compensation"), dict) else {}
    excl = prefs.get("exclusions") if isinstance(prefs.get("exclusions"), dict) else {}
    exclusions = [str(x) for key in ("occupations", "industries", "schedules")
                  for x in (excl.get(key) or []) if isinstance(excl.get(key), list)]
    return {"register": register, "positions": positions, "preferences": {
        "home": location.get("home", ""), "commute_km": location.get("commute_radius_km"),
        "arrangements": location.get("arrangements") or [],
        "minimum_pay": " ".join(str(pay[k]) for k in ("minimum", "currency", "basis") if pay.get(k)),
        "exclusions": exclusions,
        "hard_skips": [str((s or {}).get("skill", s)) if isinstance(s, dict) else str(s)
                       for s in prefs.get("hard_skips") or []],
        "cv_pages": (prefs.get("presentation") or {}).get("cv_pages", 2)
        if isinstance(prefs.get("presentation"), dict) else 2,
        "mode": settings(root)["mode"]}}


def set_position(root: Path, rank, new_status: str) -> None:
    if new_status not in ("active", "dropped"):
        raise ValueError("A position is active or dropped.")
    prefs = _yaml(root / "preferences.yaml")
    hit = [p for p in _positions(prefs or {}) if _int(p.get("rank")) == _int(rank)]
    if not hit:
        raise LookupError("No position with that number.")
    hit[0]["status"] = new_status
    write_preferences(root, prefs)


def save_upload(root: Path, name: str, body: bytes, to: str = "cv") -> str:
    clean = re.sub(r"[^\w .()-]", "", Path(name or "").name).strip(" .") or "upload"
    suffix = Path(clean).suffix.lower()
    if suffix not in UPLOAD_TYPES:
        raise ValueError("Use a PDF, Word, text or image file.")
    folder = root / "documents" / ("postings" if to == "posting" else "cv")
    folder.mkdir(parents=True, exist_ok=True)
    target, n = folder / clean, 2
    while target.exists():
        target = folder / f"{Path(clean).stem} ({n}){suffix}"
        n += 1
    target.write_bytes(body)
    return target.relative_to(root).as_posix()


def history(root: Path, limit: int = 30) -> list[dict]:
    path = root / tasks.HISTORY
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
    except OSError:
        return []
    out = []
    for line in reversed(lines):
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out
