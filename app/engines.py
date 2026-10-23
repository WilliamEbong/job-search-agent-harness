"""The two subscription engines: find the CLI, build its command line, read its events.

Both CLIs run headless in the harness folder with the prompt on stdin (never on a
command line, where a shell could expand it). Their JSON event streams are reduced to
three kinds the app shows: `say` (the assistant's words), `step` (a command or file
change, in plain words) and `session` (the id that lets the person answer a question).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

# The harness's own scripts and tools, the same list harness_setup.py pre-approves.
CLAUDE_TOOLS = [
    "Read", "Write", "Edit", "Glob", "Grep", "TodoWrite",
    "Bash(python harness/*)", "Bash(python3 harness/*)", "Bash(bun run:*)",
    "Bash(lualatex:*)", "Bash(xelatex:*)", "Bash(pandoc:*)", "Bash(pdftotext:*)",
    "Bash(pdftoppm:*)", "Bash(pdfinfo:*)",
]
# A run on the person's subscription must never fall back to a paid API key.
# ...and the settings that would route a run to another, paid backend.
API_KEYS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
            "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "OPENAI_API_KEY",
            "OPENAI_BASE_URL", "CODEX_API_KEY", "AZURE_OPENAI_API_KEY")
ENGINES = ("claude", "codex")
LABELS = {"claude": "Claude", "codex": "Codex"}


def resolve(name: str) -> list[str] | None:
    """The CLI as an argv prefix, avoiding .cmd/.ps1 shims (no shell sees the prompt)."""
    found = shutil.which(name)
    if not found:
        return None
    path = Path(found).resolve()
    if os.name != "nt" or path.suffix.lower() == ".exe":
        return [str(path)]
    if name == "claude":
        native = path.parent / "node_modules/@anthropic-ai/claude-code/bin/claude.exe"
        return [str(native)] if native.is_file() else None
    wrapper = path.parent / "node_modules/@openai/codex/bin/codex.js"
    node = shutil.which("node")
    return [str(Path(node).resolve()), str(wrapper)] if wrapper.is_file() and node else None


def _quiet(argv: list[str], timeout: int = 20) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                              encoding="utf-8", errors="replace", env=environment(),
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        return None


def status(name: str) -> dict:
    """Installed, version and signed-in, as plain facts for the setup and settings screens."""
    command = resolve(name)
    info = {"name": name, "label": LABELS[name], "installed": bool(command),
            "version": "", "signed_in": False}
    if not command:
        return info
    probe = _quiet([*command, "--version"])
    if probe and probe.returncode == 0:
        found = re.search(r"\d+\.\d+\.\d+", probe.stdout)
        info["version"] = found.group() if found else ""
    if name == "claude":
        auth = _quiet([*command, "auth", "status"])
        try:
            found = json.loads(auth.stdout) if auth else {}
        except ValueError:
            found = {}
        logged_in = bool(found.get("loggedIn"))
        info["signed_in"] = logged_in and found.get("authMethod") == "claude.ai"
    else:
        auth = _quiet([*command, "login", "status"])
        text = (auth.stdout + auth.stderr).lower() if auth and auth.returncode == 0 else ""
        logged_in = "logged in" in text
        info["signed_in"] = logged_in and "chatgpt" in text
    # Signed in with an API key bills per use, not the subscription: say so, never run it.
    info["api_key"] = logged_in and not info["signed_in"]
    return info


def environment() -> dict:
    env = {key: value for key, value in os.environ.items() if key.upper() not in API_KEYS}
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def argv(name: str, root: Path, *, session: str = "", network: bool = False) -> list[str]:
    """Command line for one turn. `session` continues an earlier turn with the person's reply."""
    command = resolve(name)
    if not command:
        raise RuntimeError(f"{LABELS[name]} is not installed")
    if name == "claude":
        tools = [*CLAUDE_TOOLS, *(("WebFetch", "WebSearch") if network else ())]
        args = [*command, "-p", "--output-format", "stream-json", "--verbose",
                "--permission-mode", "acceptEdits", "--setting-sources", "project,local",
                "--allowedTools", *tools]
        return [*args, "--resume", session] if session else args
    # Codex: network for this run only (nothing is written to ~/.codex/config.toml).
    config = ["-c", 'sandbox_mode="workspace-write"']
    if network:
        config += ["-c", "sandbox_workspace_write.network_access=true"]
    if session:
        return [*command, "exec", "resume", "--json", "--skip-git-repo-check", *config,
                session, "-"]
    return [*command, "exec", "--json", "--skip-git-repo-check", "-C", str(root), *config, "-"]


def _short(text: str, limit: int = 140) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def step_text(command: str) -> str:
    """A tool call in words a job seeker understands; unknown commands stay short."""
    for flag, words in (("--package", "Packaging the application"),
                        ("--save", "Saving the posting"), ("--start", "Saving the posting"),
                        ("--verdict", "Updating the shortlist"),
                        ("--gate-fail", "Setting aside a job that breaks your rules"),
                        ("--applied", "Updating the tracker")):
        if "lite_search.py" in command and flag in command:
            return words
    plain = {
        "lite_search.py": "Searching job boards", "latex_build.py": "Building the PDFs",
        "ats_check.py": "Checking how screening software reads the CV",
        "fact_check.py": "Checking every claim against your evidence",
        "apply_package.py": "Packaging the application", "tracker_row.py": "Updating the tracker",
        "today.py": "Reading today's list", "pdftoppm": "Looking at the finished pages",
        "tex_to_md.py": "Making the Word and text copies", "archive_applications.py":
        "Tidying the applications folder",
    }
    for key, words in plain.items():
        if key in command:
            return words
    wrapped = re.search(r"-Command\s+(['\"])(.*)\1\s*$", command, re.S)  # Codex's PowerShell
    inner = (wrapped.group(2) if wrapped else command).strip()
    if re.match(r"(Get-Content|Get-ChildItem|Select-String|cat|type|ls|dir|rg|grep|head|sed)\b",
                inner, re.I):
        return "Reading your files"
    return "Running " + _short(inner, 80)


def parse(name: str, line: str) -> list[dict]:
    """One line of CLI output to zero or more app events."""
    try:
        event = json.loads(line)
    except ValueError:
        return []
    if not isinstance(event, dict):
        return []
    kind = event.get("type")
    if name == "claude":
        if kind == "system" and event.get("subtype") == "init":
            return [{"kind": "session", "text": str(event.get("session_id", ""))}]
        if kind == "assistant":
            out = []
            for block in (event.get("message") or {}).get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text" and block.get("text", "").strip():
                    out.append({"kind": "say", "text": block["text"].strip()})
                elif block.get("type") == "tool_use":
                    data = block.get("input") or {}
                    tool = block.get("name", "")
                    if tool == "Bash":
                        out.append({"kind": "step", "text": step_text(data.get("command", ""))})
                    elif tool in ("Write", "Edit"):
                        out.append({"kind": "step", "text": "Writing "
                                    + Path(str(data.get("file_path", ""))).name})
                    elif tool == "WebFetch":
                        out.append({"kind": "step", "text": "Reading the posting online"})
                    elif tool == "Read":
                        out.append({"kind": "step", "text": "Reading "
                                    + Path(str(data.get("file_path", ""))).name})
            return out
        if kind == "result":
            if event.get("is_error"):
                return [{"kind": "error", "text": str(event.get("result") or event.get("subtype")
                                                      or "The engine reported an error.")}]
            return [{"kind": "done", "text": str(event.get("result") or "")}]
        return []
    if kind == "thread.started":
        return [{"kind": "session", "text": str(event.get("thread_id", ""))}]
    if kind in ("turn.failed", "error"):
        error = event.get("error")
        message = (error.get("message") if isinstance(error, dict) else error) \
            if kind == "turn.failed" else event.get("message")
        return [{"kind": "error", "text": str(message or "The engine reported an error.")}]
    if kind == "turn.completed":
        return [{"kind": "done", "text": ""}]
    if kind in ("item.started", "item.completed"):
        item = event.get("item") or {}
        itype = item.get("type")
        if kind == "item.completed" and itype == "agent_message" and item.get("text", "").strip():
            return [{"kind": "say", "text": item["text"].strip()}]
        if kind == "item.started" and itype == "command_execution":
            return [{"kind": "step", "text": step_text(item.get("command", ""))}]
        if kind == "item.completed" and itype == "file_change":
            names = [Path(str(change.get("path", ""))).name for change in item.get("changes") or []]
            return [{"kind": "step", "text": "Writing " + ", ".join(names)}] if names else []
        if kind == "item.started" and itype == "web_search":
            return [{"kind": "step", "text": "Searching the web"}]
    return []
