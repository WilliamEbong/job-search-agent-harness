"""Candor's local server: the screens, a small JSON API and the task queue.

Listens on 127.0.0.1 only. Every API and file request carries a token that exists only
inside the page this server sent, and the Host header must be this machine, so another
website open in the same browser cannot drive it. Contract: docs/app-build/API.md.

    python -m app.server [--port 8770] [--no-browser]
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import secrets
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from app import APP_NAME, data, engines, tasks

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
VERSION = "0.1.0"
MAX_UPLOAD = 20 * 1024 * 1024
MAX_JSON = 256 * 1024
STATUSES = {"in_progress", "interview_only", "hired", "offer_declined", "rejected",
            "no_response", "withdrawn"}


class Problem(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


class CandorServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, root: Path, port: int):
        self.root = Path(root)
        self.token = secrets.token_urlsafe(24)
        self.last_seen = time.time()
        self.runner = tasks.Runner(self.root, mode=lambda: data.settings(self.root)["mode"])
        super().__init__(("127.0.0.1", port), Handler)


def create_server(root: Path = ROOT, port: int = 8770) -> CandorServer:
    return CandorServer(root, port)


class Handler(BaseHTTPRequestHandler):
    server: CandorServer
    server_version = "Candor"

    def log_message(self, *args) -> None:  # quiet console; the launcher keeps its own log
        pass

    # -- plumbing ------------------------------------------------------------------
    def _send(self, status: int, body: bytes, kind: str, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, payload, status: int = 200) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _local(self) -> bool:
        host = (self.headers.get("Host") or "").lower()
        port = self.server.server_address[1]
        return host in (f"127.0.0.1:{port}", f"localhost:{port}")

    def _authorised(self, query: dict) -> bool:
        given = self.headers.get("X-Candor-Token") or (
            (query.get("t") or [""])[0] if self.path.startswith("/files/") else "")
        return secrets.compare_digest(given, self.server.token)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not 0 <= length <= MAX_JSON:
            raise Problem(413, "That is too much text at once.")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
        except ValueError:
            raise Problem(400, "The request was not readable.") from None
        if not isinstance(payload, dict):
            raise Problem(400, "The request was not readable.")
        return payload

    # -- entry points ------------------------------------------------------------
    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        self._route("GET")

    def do_POST(self) -> None:
        self._route("POST")

    def _route(self, method: str) -> None:
        url = urlparse(self.path)
        path, query = unquote(url.path), parse_qs(url.query)
        try:
            if not self._local():
                raise Problem(403, "Candor only answers this computer.")
            if path == "/api/ping":
                return self._json({"app": "candor"})
            if method == "GET" and (path == "/" or path.startswith("/static/")):
                return self._static(path)
            if not (path.startswith("/api/") or path.startswith("/files/")):
                raise Problem(404, "Not found.")
            if not self._authorised(query):
                raise Problem(403, "This page is out of date. Close Candor and open it again.")
            self.server.last_seen = time.time()
            if path.startswith("/files/"):
                return self._file(path[len("/files/"):])
            handler = ROUTES.get((method, path))
            if handler:
                return self._json(handler(self, query))
            for prefix, (verb, fn) in TASK_ROUTES.items():
                if method == verb and path.startswith("/api/tasks/") and path.endswith(prefix):
                    number = path[len("/api/tasks/"): len(path) - len(prefix)]
                    if number.isdigit():
                        return self._json(fn(self, int(number), query))
            raise Problem(404, "Not found.")
        except Problem as problem:
            self._json({"error": str(problem)}, problem.status)
        except (ValueError, LookupError) as error:
            self._json({"error": str(error)}, 400)
        except Exception as error:  # the page always gets a sentence, never a dropped socket
            self._json({"error": f"Something went wrong inside Candor: {error}"}, 500)

    def _static(self, path: str) -> None:
        if path == "/":
            html = (STATIC / "index.html").read_text(encoding="utf-8")
            body = html.replace("__CANDOR_TOKEN__", self.server.token).encode("utf-8")
            return self._send(200, body, "text/html; charset=utf-8", {
                "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; "
                "style-src 'self' 'unsafe-inline'; frame-src 'self'; object-src 'none'; "
                "base-uri 'none'; form-action 'none'"})
        target = (STATIC / path[len("/static/"):]).resolve()
        if STATIC.resolve() not in target.parents or not target.is_file():
            raise Problem(404, "Not found.")
        kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if target.suffix == ".js":
            kind = "text/javascript; charset=utf-8"
        self._send(200, target.read_bytes(), kind)

    def _file(self, relative: str) -> None:
        target = data.inside(self.server.root, relative)
        if not target or not target.is_file():
            raise Problem(404, "That file is not there any more.")
        suffix = target.suffix.lower()
        if suffix in (".md", ".txt", ".tex", ".csv"):
            kind, disposition = "text/plain; charset=utf-8", "inline"
        elif suffix == ".pdf":
            kind, disposition = "application/pdf", "inline"
        else:
            kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            disposition = "attachment"
        name = target.name.encode("ascii", "replace").decode().replace('"', "")
        self._send(200, target.read_bytes(), kind,
                   {"Content-Disposition": f'{disposition}; filename="{name}"'})


# -- API handlers ------------------------------------------------------------------
def _runner(h: Handler) -> tasks.Runner:
    return h.server.runner


def _require_setup(h: Handler) -> None:
    if not data.setup_state(h.server.root)["onboarded"]:
        raise Problem(409, "Finish setting up your profile first.")


def _engine(h: Handler, kind: str) -> str:
    chosen = data.engine_for(h.server.root, kind)
    if not chosen:
        raise Problem(409, "No AI engine is ready. Settings shows how to install Claude or "
                      "Codex and sign in.")
    return chosen


def get_state(h, _q):
    root = h.server.root
    return {"app": {"name": APP_NAME, "version": VERSION}, **data.state(root),
            "busy": bool(_runner(h).active())}


def get_engines(h, _q):
    found = [engines.status(name) for name in engines.ENGINES]
    usable = {e["name"]: e["installed"] for e in found}
    root = h.server.root
    return {"engines": found, "chosen": data.settings(root)["engine"],
            "resolved": {"apply": data.engine_for(root, "apply", usable),
                         "other": data.engine_for(root, "ask", usable)}}


def get_tasks(h, _q):
    live = sorted(_runner(h).snapshot(), key=lambda t: t.id)
    return {"tasks": [t.view(len(t.events)) | {"events": t.events[-3:]} for t in live
                      if t.status not in ("done", "failed", "cancelled")
                      or time.time() - t.created < 3600],
            "history": data.history(h.server.root)}


def get_task(h, number, q):
    task = _runner(h).tasks.get(number)
    if not task:
        raise Problem(404, "That task has gone. Candor may have restarted.")
    return task.view(int((q.get("since") or ["0"])[0] or 0))


def post_reply(h, number, _q):
    text = str(h._body().get("text", "")).strip()
    if not text:
        raise Problem(400, "Type an answer first.")
    try:
        return {"task": _runner(h).answer(number, text).view()}
    except KeyError:
        raise Problem(404, "That task has gone.") from None
    except ValueError as error:
        raise Problem(409, str(error)) from None


def post_cancel(h, number, _q):
    try:
        return {"task": _runner(h).cancel(number).view()}
    except KeyError:
        raise Problem(404, "That task has gone.") from None


def post_upload(h, q):
    length = int(h.headers.get("Content-Length") or 0)
    if not 0 < length <= MAX_UPLOAD:
        raise Problem(413, "Use a file under 20 MB.")
    body = h.rfile.read(length)
    to = (q.get("to") or ["cv"])[0]
    return {"path": data.save_upload(h.server.root, (q.get("name") or [""])[0], body, to)}


def post_setup(h, _q):
    payload = h._body()
    root = h.server.root
    cv = data.inside(root, str(payload.get("cv", "")))
    if not cv or not cv.is_file():
        raise Problem(400, "Add your CV first.")
    answers = payload.get("answers") or []
    if not isinstance(answers, list) or len(answers) > 5:
        raise Problem(400, "The five answers did not arrive.")
    args = {"cv": cv.relative_to(root).as_posix(),
            "answers": [str(a)[:600] for a in answers] + [""] * (5 - len(answers))}
    task = tasks.Task("setup", args, _engine(h, "setup"))
    return {"task": _runner(h).submit(task).view()}


def post_search(h, _q):
    _require_setup(h)
    root = h.server.root
    payload = h._body()
    prefs = data.settings(root)
    top = data._int(payload.get("top")) or prefs["search_top"]
    screen = data.engine_for(root, "screen") if prefs["screen_after_search"] else None
    task = tasks.Task("search", {"top": max(1, min(top, 20)), "screen": screen or ""}, "script")
    return {"task": _runner(h).submit(task).view()}


def post_apply(h, _q):
    _require_setup(h)
    root = h.server.root
    payload = h._body()
    engine = _engine(h, "apply")
    batch: list[dict] = []
    numbers = payload.get("numbers") or ([payload["number"]] if payload.get("number") else None)
    if isinstance(numbers, list) and numbers:
        if len(numbers) > 10:
            raise Problem(400, "Prepare up to 10 applications at a time.")
        search = data.last_search(root) or {"results": []}
        for number in numbers:
            n = data._int(number)
            if not n or not 1 <= n <= len(search["results"]):
                raise Problem(400, f"Job {number} is not in the last search any more.")
            job = search["results"][n - 1]
            batch.append({"number": n, "company": job["company"], "role": job["title"]})
    elif payload.get("url"):
        url = str(payload["url"]).strip()
        if not tasks.URL.fullmatch(url):
            raise Problem(400, "That does not look like a web link. Paste the whole address.")
        batch.append({"url": url})
    elif payload.get("text"):
        text = str(payload["text"]).strip()
        if len(text) < 80:
            raise Problem(400, "Paste the whole posting, not just the title.")
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(3)
        folder = root / "documents" / "postings"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"pasted-{stamp}.md").write_text(text[:200_000], encoding="utf-8")
        batch.append({"file": f"documents/postings/pasted-{stamp}.md"})
    elif payload.get("file"):
        target = data.inside(root, str(payload["file"]))
        if not target or not target.is_file():
            raise Problem(400, "That file is not there any more. Add it again.")
        relative = target.relative_to(root).as_posix()
        image = target.suffix.lower() in (".png", ".jpg", ".jpeg")
        batch.append({"file": relative} | ({"image": relative} if image else {}))
    else:
        raise Problem(400, "Choose a job, or paste a link or the posting.")
    total = len(batch)
    made = []
    for index, args in enumerate(batch, 1):
        who = f": {args['company']}" if args.get("company") else ""
        title = f"Preparing an application{who}" + (f" ({index} of {total})" if total > 1 else "")
        made.append(_runner(h).submit(tasks.Task("apply", args, engine, title)).view())
    return {"tasks": made}


def post_status(h, _q):
    payload = h._body()
    company, role = str(payload.get("company", "")), str(payload.get("role", ""))
    status = str(payload.get("status", "in_progress"))
    if not company or not role or (not payload.get("sent") and status not in STATUSES):
        raise Problem(400, "Choose an application and an outcome.")
    try:
        data.mark(h.server.root, company, role, status, bool(payload.get("sent")))
    except LookupError as error:
        raise Problem(404, str(error)) from None
    return {"ok": True}


def _agent_task(kind: str, fields: tuple[str, ...], min_text: int = 0):
    def handler(h, _q):
        _require_setup(h)
        payload = h._body()
        args = {key: str(payload.get(key, "")).strip()[:4000] for key in fields}
        if min_text and len(args.get("text", "")) < min_text:
            raise Problem(400, "Write a little more so the assistant knows what you mean.")
        if "company" in fields and not args["company"]:
            raise Problem(400, "Choose an application first.")
        return {"task": _runner(h).submit(tasks.Task(kind, args, _engine(h, kind))).view()}
    return handler


def post_positions(h, _q):
    payload = h._body()
    data.set_position(h.server.root, payload.get("rank"), str(payload.get("status", "")))
    return {"ok": True}


def post_settings(h, _q):
    return {"settings": data.save_settings(h.server.root, h._body())}


def post_open(h, _q):
    target = data.inside(h.server.root, str(h._body().get("path", "")))
    if not target or not target.exists():
        raise Problem(404, "That folder is not there any more.")
    if target.is_file() and target.suffix.lower() not in (".pdf", ".docx", ".md"):
        raise Problem(400, "Candor only opens folders, PDFs and documents.")  # never a script
    if os.name == "nt":
        os.startfile(target)  # noqa: S606 - a path confined to documents/
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(target)])
    return {"ok": True}


def post_doctor(h, _q):
    try:
        proc = subprocess.run([sys.executable, "harness_setup.py", "--doctor"],
                              cwd=h.server.root, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=180,
                              env=engines.environment(),
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        raise Problem(500, "The computer check took too long. Try again.") from None
    return {"output": proc.stdout[-20000:], "ok": proc.returncode == 0}


ROUTES = {
    ("GET", "/api/state"): get_state,
    ("GET", "/api/engines"): get_engines,
    ("GET", "/api/jobs"): lambda h, q: data.jobs(h.server.root),
    ("GET", "/api/applications"): lambda h, q: {"applications": data.applications(h.server.root)},
    ("GET", "/api/profile"): lambda h, q: data.profile(h.server.root),
    ("GET", "/api/tasks"): get_tasks,
    ("POST", "/api/upload"): post_upload,
    ("POST", "/api/setup"): post_setup,
    ("POST", "/api/search"): post_search,
    ("POST", "/api/apply"): post_apply,
    ("POST", "/api/applications/status"): post_status,
    ("POST", "/api/followup"): _agent_task("followup", ("company", "role")),
    ("POST", "/api/interview"): _agent_task("interview", ("company", "role")),
    ("POST", "/api/fact"): _agent_task("fact", ("text",), min_text=8),
    ("POST", "/api/ask"): _agent_task("ask", ("text",), min_text=2),
    ("POST", "/api/positions"): post_positions,
    ("POST", "/api/settings"): post_settings,
    ("POST", "/api/open"): post_open,
    ("POST", "/api/doctor"): post_doctor,
}
TASK_ROUTES = {"/reply": ("POST", post_reply), "/cancel": ("POST", post_cancel),
               "": ("GET", get_task)}


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Run the Candor app server.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("CANDOR_PORT", 8770)))
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    server = create_server(ROOT, args.port)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"{APP_NAME} is running at {url} (Ctrl+C stops it)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
