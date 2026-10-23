"""Work the app hands to the assistant or to a harness script, one at a time.

A task is a queue entry. The worker runs one at a time, because two runs writing the
same tracker or the same LaTeX files would corrupt each other. Several queued
applications form the batch loop: each runs to the end before the next starts.

An agent task that ends on a question waits with status `question`; the person's reply
continues the same CLI session. Nothing here ever submits an application.
"""

from __future__ import annotations

import itertools
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from app import engines

MAX_SECONDS = 45 * 60  # ponytail: one cap for every run; an apply takes 10-15 minutes
HISTORY = Path("state") / "app-history.jsonl"

PREAMBLE = """You are running inside Candor, a desktop app over this job-search harness.
The person cannot see a terminal, your tool calls or this prompt; they see only your
plain-text messages, in a small panel. So:
- Follow AGENTS.md, CLAUDE.md and the workflow files named below exactly; every rule
  marked "never relaxed" still holds, the fact gate above all.
- Write short, plain messages for someone who is not technical. No slash commands, no
  file paths unless they ask; the app has screens called Today, Jobs, Applications,
  Profile and Settings, so point to those instead.
- Never ask the person to run a command. Run it yourself.
- If you genuinely need an answer from them to continue, end your final message with
  the question(s), numbered, and stop. The app shows them with a reply box.
- Never submit an application, send an email or contact an employer.
"""

URL = re.compile(r"https?://[^\s\"'<>`$]{3,2000}")


def _clean(text: str, limit: int = 4000) -> str:
    """Person-typed text placed in a prompt: no control characters, bounded."""
    return "".join(ch for ch in str(text) if ch == "\n" or ch >= " ")[:limit].strip()


def build_prompt(kind: str, args: dict, mode: str = "lite") -> str:
    """The instruction for one agent task. Posting text never appears here; it is saved
    to a file first, because postings are untrusted input."""
    lite = mode == "lite"
    if kind == "setup":
        answers = "\n".join(f"  ({i}) {_clean(a, 600) or 'skip'}"
                            for i, a in enumerate(args.get("answers") or [], 1))
        return (f"{PREAMBLE}\nTask: first-time setup. Follow `.claude/commands/lite.md` and "
                f"`.claude/lite/setup.md` (/lite setup).\n"
                f"Step 1: the CV is at `{args['cv']}`.\n"
                f"Step 2: the person already answered the five questions in the app; do not "
                f"ask them again (\"skip\" keeps the default):\n{answers}\n"
                "Step 4: save every position as active. The person strikes the ones they do "
                "not want on the Profile screen afterwards, so do not wait for them.\n"
                "Skip step 5; the app gives Codex network access per run.\n"
                f"Set `usage.mode: {mode}` in preferences.yaml.\n"
                "Finish with two lines: how many positions you saved, and the one CV gap "
                "the person should confirm on the Profile screen, if any.")
    if kind == "screen":
        return (f"{PREAMBLE}\nTask: screen the jobs the app just found, step 2 of "
                "/lite search in `.claude/commands/lite.md`. Read "
                "`state/lite-last-search.json` and preferences.yaml once. For each row that "
                "breaks `exclusions`, `hard_skips` or `work_authorization`, run "
                "`python harness/lite_search.py --gate-fail <#> --rationale '<rule broken>'`. "
                "Do not fetch postings. Finish with one line: how many were set aside and "
                "why, and how many look worth a closer look.")
    if kind == "apply":
        if args.get("number"):
            target = f"job #{int(args['number'])} from the last search"
        elif args.get("url"):
            target = f"the posting at {args['url']}"
        else:
            target = f"the posting in the file `{args['file']}`"
        flow = ("Follow `.claude/commands/lite.md` and `.claude/lite/apply.md` (/lite apply)."
                if lite else "Follow `.claude/commands/apply-any.md` (/apply-any).")
        return (f"{PREAMBLE}\nTask: prepare an application package for {target}. {flow}\n"
                "The person pressed Prepare in the app, which answers yes for a fit of "
                "60-79; still stop below 60. Any other point where the workflow says the "
                "person decides (pay below their minimum, a closing date that has passed): "
                "ask, then stop.\n"
                "Finish with the workflow's report, then one line telling the person to read "
                "both PDFs on the Applications screen and send it themselves.")
    if kind == "followup":
        return (f"{PREAMBLE}\nTask: the person wants to follow up on their application to "
                f"{_clean(args['company'], 200)} ({_clean(args.get('role', ''), 200)}). "
                "Follow `.claude/commands/outcome.md` for a follow-up: draft a short, polite "
                "follow-up email they can send themselves, show it in full, and record the "
                "follow-up as that workflow says. Do not send anything.")
    if kind == "interview":
        return (f"{PREAMBLE}\nTask: interview preparation for "
                f"{_clean(args['company'], 200)} ({_clean(args.get('role', ''), 200)}). "
                "Follow `.claude/commands/interview.md`. Keep the answer readable on a "
                "small panel: the likely questions, and for each, the evidence to use.")
    if kind == "fact":
        return (f"{PREAMBLE}\nTask: the person wants to record a fact about their career. "
                "Follow `.claude/commands/fact.md`. What they said:\n"
                f"<<<\n{_clean(args['text'])}\n>>>\nIf it is unclear what exactly may be "
                "claimed, ask one question and stop.")
    if kind == "ask":
        route = "Lite mode is on: route through `/lite` where it applies. " if lite else ""
        return (f"{PREAMBLE}\nTask: the person typed this into the app's \"Ask\" box. "
                f"{route}Route it as CLAUDE.md's plain-language table says, then do it.\n"
                f"<<<\n{_clean(args['text'])}\n>>>")
    raise ValueError(f"unknown task kind {kind!r}")


TITLES = {
    "setup": "Building your profile", "screen": "Checking the new jobs against your rules",
    "apply": "Preparing an application", "followup": "Drafting a follow-up",
    "interview": "Interview preparation", "fact": "Recording a fact", "ask": "Answering you",
    "search": "Searching job boards",
}
NETWORK = {"apply", "ask", "followup", "interview", "setup"}


class Task:
    _ids = itertools.count(1)

    def __init__(self, kind: str, args: dict, engine: str, title: str = ""):
        self.id = next(self._ids)
        self.kind, self.args, self.engine = kind, args, engine
        self.title = title or TITLES.get(kind, kind)
        self.status = "queued"  # queued, running, question, done, failed, cancelled
        self.events: list[dict] = []
        self.session = ""
        self.created = time.time()
        self.process: subprocess.Popen | None = None
        self.reply: str | None = None

    def add(self, kind: str, text: str) -> None:
        if kind == "step" and self.events and self.events[-1] == {"kind": "step", "text": text}:
            return  # the same check run twice reads as one step
        self.events.append({"kind": kind, "text": text, "at": time.time()})

    def view(self, since: int = 0) -> dict:
        return {"id": self.id, "kind": self.kind, "title": self.title, "status": self.status,
                "engine": self.engine, "args": {k: v for k, v in self.args.items()
                                                if k in ("number", "company", "role", "url")},
                "events": self.events[since:], "count": len(self.events)}


class Runner:
    """The queue and its single worker thread."""

    def __init__(self, root: Path, mode=lambda: "lite"):
        self.root = Path(root)
        self.mode = mode
        self.tasks: dict[int, Task] = {}
        self.queue: list[Task] = []
        self.lock = threading.Condition()
        threading.Thread(target=self._work, daemon=True).start()

    # -- public --------------------------------------------------------------
    def submit(self, task: Task) -> Task:
        with self.lock:
            self.tasks[task.id] = task
            self.queue.append(task)
            self.lock.notify_all()
        return task

    def answer(self, task_id: int, text: str) -> Task:
        task = self.tasks[task_id]
        with self.lock:
            if task.status not in ("question", "done") or not task.session or task.kind == "search":
                raise ValueError("That task is not waiting for an answer.")
            task.add("you", _clean(text))
            task.reply = _clean(text)
            task.status = "queued"
            self.queue.insert(0, task)  # an answer continues before anything else starts
            self.lock.notify_all()
        return task

    def cancel(self, task_id: int) -> Task:
        task = self.tasks[task_id]
        with self.lock:
            if task in self.queue:
                self.queue.remove(task)
            if task.status in ("queued", "question"):
                task.status = "cancelled"
                task.add("note", "Cancelled.")
                self._record(task)
            elif task.status == "running" and task.process:
                task.status = "cancelling"
                _kill(task.process)
        return task

    def active(self) -> list[Task]:
        return [t for t in self.tasks.values()
                if t.status in ("queued", "running", "question", "cancelling")]

    # -- worker --------------------------------------------------------------
    def _work(self) -> None:
        while True:
            with self.lock:
                while not self.queue:
                    self.lock.wait()
                task = self.queue.pop(0)
                task.status = "running"
            try:
                if task.kind == "search":
                    self._script(task)
                else:
                    self._agent(task)
            except Exception as error:  # a crashed run must never take the worker down
                task.add("error", f"Something went wrong: {error}")
                task.status = "failed"
            if task.status in ("done", "failed", "cancelled"):
                self._record(task)
            if task.kind == "search" and task.status == "done" and task.args.get("screen"):
                engine = task.args["screen"]
                self.submit(Task("screen", {}, engine))

    def _script(self, task: Task) -> None:
        """Job search is a script, not the assistant: no subscription use, no tokens."""
        argv = [sys.executable, "harness/lite_search.py", "--top", str(task.args.get("top", 5)),
                "--record"]
        task.add("step", "Searching every enabled job board")
        proc = subprocess.Popen(argv, cwd=self.root, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                errors="replace", env=engines.environment(),
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        task.process = proc
        lines = [line.rstrip() for line in proc.stdout]
        proc.wait()
        proc.stdout.close()
        if task.status == "cancelling":
            task.status = "cancelled"
            task.add("note", "Cancelled.")
            return
        failures = [line for line in lines if line.startswith(("lite_search:", "WARNING"))
                    or "could not be searched" in line or "failed" in line.lower()]
        for line in failures[:4]:
            task.add("note", line.removeprefix("lite_search: "))
        if proc.returncode == 0:
            task.add("done", "Search finished. The Jobs screen shows what was found.")
            task.status = "done"
        else:
            task.add("error", failures[0].removeprefix("lite_search: ") if failures
                     else "The search could not run.")
            task.status = "failed"

    def _agent(self, task: Task) -> None:
        reply, task.reply = task.reply, None
        prompt = reply if reply else build_prompt(task.kind, task.args, self.mode())
        if task.args.get("image") and not reply:
            prompt += f"\nThe posting is a picture at `{task.args['image']}`: read it."
        argv = engines.argv(task.engine, self.root, session=task.session if reply else "",
                            network=task.kind in NETWORK)
        if not reply:
            task.add("note", f"Working with {engines.LABELS[task.engine]}.")
        proc = subprocess.Popen(argv, cwd=self.root, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                encoding="utf-8", errors="replace", env=engines.environment(),
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        task.process = proc
        stderr: list[str] = []
        threading.Thread(target=lambda: stderr.extend(proc.stderr), daemon=True).start()
        timer = threading.Timer(MAX_SECONDS, lambda: _kill(proc))
        timer.start()
        try:
            proc.stdin.write(prompt)
            proc.stdin.close()
        except OSError:
            pass
        last_say, failed = "", ""
        for line in proc.stdout:
            for event in engines.parse(task.engine, line):
                if event["kind"] == "session":
                    task.session = task.session or event["text"]
                elif event["kind"] == "say":
                    last_say = event["text"]
                    task.add("say", event["text"])
                elif event["kind"] == "step":
                    task.add("step", event["text"])
                elif event["kind"] == "error":
                    failed = event["text"]
                elif event["kind"] == "done" and event["text"] and event["text"] != last_say:
                    last_say = event["text"]
                    task.add("say", event["text"])
        proc.wait()
        proc.stdout.close()
        timer.cancel()
        if task.status == "cancelling":
            task.status = "cancelled"
            task.add("note", "Cancelled. Anything already saved stays saved.")
        elif failed or proc.returncode:
            detail = failed or _first_error(stderr) or f"exit code {proc.returncode}"
            task.add("error", explain(detail, task.engine))
            task.status = "failed"
        elif last_say.rstrip().endswith("?") and task.session:
            task.status = "question"
        else:
            task.status = "done"

    def _record(self, task: Task) -> None:
        says = [e["text"] for e in task.events if e["kind"] in ("say", "done", "error")]
        entry = {"at": datetime.now().isoformat(timespec="seconds"), "title": task.title,
                 "kind": task.kind, "status": task.status, "engine": task.engine,
                 "summary": (says[-1] if says else "")[:600]}
        path = self.root / HISTORY
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass  # history is a convenience; the harness files are the record


def _first_error(lines: list[str]) -> str:
    for line in lines:
        line = line.strip()
        if line and ("error" in line.lower() or "not logged" in line.lower()):
            return line[:300]
    return ""


def explain(detail: str, engine: str) -> str:
    """Engine failures in words that say what to do next."""
    label = engines.LABELS.get(engine, engine)
    low = detail.lower()
    if any(word in low for word in ("login", "logged in", "auth", "401", "credential")):
        return (f"{label} is not signed in. Open Settings, then Engine, and follow the "
                "sign-in steps.")
    if any(word in low for word in ("rate limit", "usage limit", "quota", "429")):
        return (f"Your {label} plan has hit its usage limit for now. Try again later, or "
                "switch engines in Settings.")
    if "not installed" in low:
        return f"{label} is not installed. Settings, then Engine, shows how to install it."
    return f"{label} stopped with an error: {detail[:300]}"


def _kill(proc: subprocess.Popen) -> None:
    """Stop the CLI and every command it started (a LaTeX build, a board search)."""
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    else:
        proc.kill()
