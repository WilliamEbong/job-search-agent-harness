#!/usr/bin/env python3
"""One-command setup and doctor for the Job Search Agent Harness.

    python harness_setup.py            # check, offer installs, print the doctor table
    python harness_setup.py --doctor   # check and report only; change nothing
    python harness_setup.py --yes      # take the recommended answer to every prompt
    python harness_setup.py --quick    # skip the stock-template test compiles

Design rules this file follows, and why:

* **Stdlib only.** harness_setup.py runs *before* dependencies exist, so it cannot
  import them. That is also why it parses nothing from requirements.txt beyond
  handing the file to pip.
* **Never assume an install worked.** Every install is followed by the check
  that would have caught its failure: plugins are re-listed and matched by
  name, TeX is asked to compile a real document, Python packages are imported.
  A step that cannot be verified is reported as unverified, not as success.
* **The doctor never lies to make the table look green.** A tool that is
  present but broken reports DEGRADED with the reason, which is a worse-
  looking and far more useful result than MISSING.
* **No secrets are read, stored, or echoed.** The optional Firecrawl API key
  is passed by *name* to the runtime (an env-var reference), never by value.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Statuses.
DEGRADED = "DEGRADED"  # present but broken — the dangerous one
MISSING = "MISSING"
UNVERIFIED = "UNVERIFIED"
STALE_PATH = "RESTART SHELL"
OPTIONAL = "OPTIONAL"
OK = "OK"

REQUIRED_BAD = {DEGRADED, MISSING}

# Prompt behaviour, overridden by --yes / --doctor. Module-level so the tests
# can substitute them without driving a real terminal.
AUTO_YES = False
DOCTOR_ONLY = False


@dataclass
class Check:
    """One row of the doctor table."""

    name: str
    status: str
    detail: str = ""
    fix: str = ""
    required: bool = True


@dataclass
class Runtime:
    """An agent CLI we can install plugins into."""

    name: str  # "claude" | "codex"
    exe: str
    # Codex installs plugins with `plugin add`, Claude with `plugin install`.
    install_verb: str
    checks: list[Check] = field(default_factory=list)


CAVEMAN_EXPLANATION = """\
  Caveman is OPTIONAL. It compresses the agent's *internal* chatter — status
  updates, search summaries, notes between sub-agents — into a terser style,
  which cuts output tokens on chatty tasks and makes long runs easier to skim.

  What it never touches: your CVs, cover letters, recruiter messages, or any
  other text that reaches a human. Those are hard-fenced off in this harness,
  so installing Caveman cannot affect the quality of an application.

  Honest note on savings: the token reduction is real on chatty work, but
  Ponytail's own benchmark measured Caveman as roughly cost-neutral on build
  tasks. Treat it as readability control, with savings as a bonus.

  Recommended for this harness: LITE mode (say `/caveman lite` in a session).
  Lite keeps the compression on internal chatter without the heavier stylistic
  rewriting. You can remove the plugin at any time; nothing depends on it."""


# --------------------------------------------------------------------------
# process + PATH helpers
# --------------------------------------------------------------------------


def run(args: list[str], timeout: int = 180, cwd: Path | None = None) -> tuple[int, str]:
    """Run a command, never raise. Returns (exit code, combined output)."""
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd) if cwd else None,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return 127, f"{args[0]}: not found"
    except subprocess.TimeoutExpired:
        return 124, f"{args[0]}: timed out after {timeout}s"
    except OSError as exc:  # permissions, exec format, ...
        return 126, f"{args[0]}: {exc}"
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _persistent_path_dirs() -> list[str]:
    """Directories on Windows' *persistent* PATH (registry), not this shell's.

    An installer that just ran has updated the registry, but every already-open
    shell still holds the old PATH. Without this, the doctor reports a tool the
    user just installed as MISSING and sends them round in circles.
    """
    if os.name != "nt":
        return []
    try:
        import winreg
    except ImportError:  # pragma: no cover - Windows only
        return []
    keys = (
        (winreg.HKEY_CURRENT_USER, "Environment"),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ),
    )
    dirs: list[str] = []
    for root, sub in keys:
        try:
            with winreg.OpenKey(root, sub) as key:
                raw, _ = winreg.QueryValueEx(key, "Path")
        except OSError:
            continue
        dirs += [os.path.expandvars(p) for p in str(raw).split(os.pathsep) if p.strip()]
    return dirs


def find_tool(name: str) -> tuple[str | None, bool]:
    """Locate an executable. Returns (path, only_on_persistent_path)."""
    found = shutil.which(name)
    if found:
        return found, False
    extra = _persistent_path_dirs()
    if extra:
        found = shutil.which(name, path=os.pathsep.join(extra))
        if found:
            return found, True
    return None, False


def confirm(question: str, default: bool = True) -> bool:
    """Ask a yes/no question. Honours --yes and --doctor without prompting."""
    if DOCTOR_ONLY:
        return False
    if AUTO_YES:
        print(f"{question} [auto: {'yes' if default else 'no'}]")
        return default
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"{question} {suffix} ").strip().lower()
    except EOFError:
        # Piped stdin (CI, a wrapper script). Take the default rather than
        # crashing, and say so — silence here would look like a real answer.
        print(f"{question} {suffix} (no input available, using default)")
        return default
    if not answer:
        return default
    return answer.startswith("y")


def section(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def step(message: str) -> None:
    """Say what is about to happen, before a step that takes a while.

    `run()` captures output, so several steps here are silent for minutes —
    installing dependencies for seven job-board CLIs, and MiKTeX downloading
    packages on its first compile. With no signal at all, the reasonable
    conclusion is that it has hung.
    """
    print(f"  {message}", flush=True)


def offer_express() -> bool:
    """Ask once whether to take every recommended answer.

    The per-item prompts are 7 on one runtime and 13 on two, which is a lot of
    decisions to ask someone before they have seen the thing work.
    """
    if DOCTOR_ONLY or AUTO_YES:
        return AUTO_YES
    print("\nTwo ways to do this:")
    print("  express - take the recommended answer to everything (1 question)")
    print("  custom  - decide each item yourself (8 questions, or 12 if you use")
    print("            both Claude Code and Codex)")
    print("\nExpress installs: the Python packages, the job-board tools, Ponytail,")
    print("the Playwright and Firecrawl browser tools, and the statusline. The only")
    print("thing it declines for you is Caveman.")
    return confirm("\nUse express setup?", default=True)


# --------------------------------------------------------------------------
# prerequisite checks
# --------------------------------------------------------------------------


def check_python() -> Check:
    major, minor, patch = sys.version_info[:3]
    version = f"{major}.{minor}.{patch}"
    if (major, minor) < (3, 10):
        return Check(
            "Python",
            MISSING,
            f"{version} — upstream requires 3.10+",
            "Install Python 3.10 or newer and re-run this script with it.",
        )
    return Check("Python", OK, version)


def check_simple(label: str, exe: str, args: list[str], required: bool = True) -> Check:
    """Present-and-runnable check for a tool whose only job is to exist."""
    path, stale = find_tool(exe)
    if not path:
        return Check(label, MISSING if required else OPTIONAL, "not on PATH",
                     required=required)
    if stale:
        return Check(label, STALE_PATH, "installed, but not in this shell's PATH",
                     "Close and reopen your terminal, then re-run setup.",
                     required=required)
    code, out = run([path] + args, timeout=120)
    if code != 0:
        return Check(label, DEGRADED, f"found at {path} but exited {code}",
                     out.strip().splitlines()[0] if out.strip() else "",
                     required=required)
    first = next((ln.strip() for ln in out.splitlines() if ln.strip()), "")
    return Check(label, OK, first[:60], required=required)


def check_bun() -> Check:
    """Bun, executed rather than merely located.

    The stock Bun build requires AVX2. On a CPU without it, `bun` installs
    perfectly and then panics with an illegal instruction on every call — so a
    presence-only check reports green on a machine where all six portal CLIs
    are dead. Verified on the build machine: exit 3, `Features: no_avx2`.
    """
    path, stale = find_tool("bun")
    if not path:
        return Check("Bun", MISSING, "not on PATH",
                     "winget install --id Oven-sh.Bun   "
                     "(if it then crashes, see the AVX2 note below)")
    if stale:
        return Check("Bun", STALE_PATH, "installed, but not in this shell's PATH",
                     "Close and reopen your terminal, then re-run setup.")
    code, out = run([path, "--version"], timeout=120)
    low = out.lower()
    if "panic" in low or "illegal instruction" in low:
        return Check(
            "Bun",
            DEGRADED,
            "installed but crashes on startup (this CPU has no AVX2)",
            "Install the baseline build instead: "
            "winget uninstall --id Oven-sh.Bun && "
            "winget install --id Oven-sh.Bun.Baseline",
        )
    if code != 0:
        return Check("Bun", DEGRADED, f"exited {code}", out.strip()[:200])
    first = next((ln.strip() for ln in out.splitlines() if ln.strip()), "present")
    return Check("Bun", OK, first[:40])


def check_poppler() -> Check:
    """poppler must provide BOTH pdftotext and pdfinfo.

    Git for Windows ships pdftotext but not pdfinfo, so a check for pdftotext
    alone reports poppler present on a machine where upstream's PDF page-count
    verification cannot run.
    """
    missing = [name for name in ("pdftotext", "pdfinfo") if not find_tool(name)[0]]
    if missing:
        hint = ""
        if missing == ["pdfinfo"]:
            hint = " (pdftotext alone is not poppler — Git for Windows ships it)"
        return Check(
            "poppler",
            MISSING,
            f"missing: {', '.join(missing)}{hint}",
            "winget install --id oschwartz10612.Poppler   "
            "(or: apt install poppler-utils)",
        )
    return Check("poppler", OK, "pdftotext + pdfinfo")


TEST_COMPILES = (
    ("lualatex", Path("cv"), "main_example.tex", "CV template"),
    ("xelatex", Path("cover_letters"), "cover_example.tex", "cover-letter template"),
)


def check_tex(quick: bool = False) -> list[Check]:
    """Verify both engines exist and — unless --quick — actually compile.

    "lualatex --version succeeds" is not evidence that a CV will build: the
    stock templates need fontspec, moderncv and the bundled Raleway fonts, and
    a missing package surfaces only at compile time. So the honest check
    compiles the real templates.
    """
    checks: list[Check] = []
    for engine, subdir, texfile, label in TEST_COMPILES:
        path, stale = find_tool(engine)
        if not path:
            checks.append(Check(
                engine, MISSING, "not on PATH",
                "Install MiKTeX (winget install --id MiKTeX.MiKTeX) or TeX Live. "
                "Both engines are needed: lualatex for CVs, xelatex for letters.",
            ))
            continue
        if stale:
            checks.append(Check(engine, STALE_PATH,
                                "installed, but not in this shell's PATH",
                                "Close and reopen your terminal, then re-run setup."))
            continue
        code, out = run([path, "--version"], timeout=120)
        if code != 0:
            checks.append(Check(engine, DEGRADED, f"exited {code}", out.strip()[:200]))
            continue
        banner = next((ln.strip() for ln in out.splitlines() if ln.strip()),
                      "present")
        checks.append(Check(engine, OK, banner[:50]))
        if quick:
            checks.append(Check(
                f"{engine} compile", UNVERIFIED, "skipped (--quick)",
                "Re-run without --quick to test-compile the stock templates.",
                required=False,
            ))
            continue
        checks.append(_test_compile(path, engine, subdir, texfile, label))
    return checks


def _test_compile(exe: str, engine: str, subdir: Path, texfile: str,
                  label: str) -> Check:
    source = ROOT / subdir / texfile
    if not source.is_file():
        return Check(f"{engine} compile", UNVERIFIED,
                     f"{subdir.as_posix()}/{texfile} not present", required=False)
    with tempfile.TemporaryDirectory(prefix="harness-texcheck-") as tmp:
        # cwd MUST be the template's own directory: cover.cls resolves its
        # bundled OpenFonts path relative to the current directory, and
        # compiling from elsewhere fails with a font-not-found error that
        # looks nothing like the real cause.
        step(f"compiling the stock {label} with {engine} - on a fresh TeX "
             f"install this downloads packages and can take several minutes")
        code, out = run(
            [exe, "-interaction=nonstopmode", "-halt-on-error",
             f"-output-directory={tmp}", texfile],
            timeout=900,
            cwd=ROOT / subdir,
        )
        produced = Path(tmp) / (Path(texfile).stem + ".pdf")
        if code == 0 and produced.is_file() and produced.stat().st_size > 0:
            return Check(f"{engine} compile", OK,
                         f"{label} built ({produced.stat().st_size // 1024} KB)")
        reason = next(
            (ln.strip() for ln in out.splitlines() if ln.startswith("!")),
            out.strip().splitlines()[-1][:120] if out.strip() else f"exit {code}",
        )
        return Check(
            f"{engine} compile", DEGRADED, f"{label} failed to build",
            f"{reason}\n"
            f"      Run this once by hand to let TeX finish downloading:\n"
            f"        cd {subdir.as_posix()} && {engine} {texfile}",
        )


def check_python_deps() -> Check:
    """Import what requirements.txt pins. Importable is the only proof."""
    missing = []
    for module, package in (("yaml", "PyYAML"), ("openpyxl", "openpyxl"),
                            ("pypdf", "pypdf")):
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if missing:
        return Check("Python packages", MISSING,
                     f"not importable: {', '.join(missing)}",
                     f"{sys.executable} -m pip install -r requirements.txt")
    return Check("Python packages", OK, "PyYAML, openpyxl, pypdf")


# --------------------------------------------------------------------------
# runtimes, plugins, MCP
# --------------------------------------------------------------------------


def detect_runtimes() -> list[Runtime]:
    found: list[Runtime] = []
    for name, verb in (("claude", "install"), ("codex", "add")):
        path, _ = find_tool(name)
        if path:
            found.append(Runtime(name=name, exe=path, install_verb=verb))
    return found


def installed_plugins(runtime: Runtime) -> str:
    code, out = run([runtime.exe, "plugin", "list"], timeout=180)
    return out if code == 0 else ""


def install_plugin(runtime: Runtime, repo: str, plugin: str) -> Check:
    """Add the marketplace, install, then prove it by re-listing.

    Both runtimes accept the same two-step marketplace flow (verified on
    claude 2.1.x and codex-cli 0.144.6); only the install verb differs.
    """
    label = f"{plugin} ({runtime.name})"
    code, out = run([runtime.exe, "plugin", "marketplace", "add", repo], timeout=300)
    if code != 0 and "already" not in out.lower():
        return Check(label, MISSING, "marketplace add failed", out.strip()[:200],
                     required=False)
    code, out = run([runtime.exe, "plugin", runtime.install_verb, f"{plugin}@{plugin}"],
                    timeout=300)
    if code != 0 and "already" not in out.lower():
        return Check(label, MISSING, "install failed", out.strip()[:200], required=False)
    # The verification that matters: does the runtime itself list it now?
    if plugin in installed_plugins(runtime):
        return Check(label, OK, "installed and listed", required=False)
    return Check(label, UNVERIFIED,
                 "install reported success but the plugin is not in `plugin list`",
                 f"Run `{runtime.name} plugin list` yourself before relying on it.",
                 required=False)


def offer_plugins(runtime: Runtime) -> list[Check]:
    checks: list[Check] = []
    listing = installed_plugins(runtime)

    if "ponytail" in listing:
        checks.append(Check(f"ponytail ({runtime.name})", OK, "already installed",
                            required=False))
    elif confirm(f"Install Ponytail for {runtime.name}? (recommended — keeps "
                 f"generated code and prose minimal)"):
        checks.append(install_plugin(runtime, "DietrichGebert/ponytail", "ponytail"))
    else:
        checks.append(Check(f"ponytail ({runtime.name})", OPTIONAL, "declined",
                            required=False))

    if "caveman" in listing:
        checks.append(Check(f"caveman ({runtime.name})", OK, "already installed",
                            required=False))
    else:
        print(f"\n{CAVEMAN_EXPLANATION}\n")
        if confirm(f"Install Caveman for {runtime.name}?", default=False):
            checks.append(install_plugin(runtime, "JuliusBrussee/caveman", "caveman"))
            print("  Installed. Say `/caveman lite` in a session to use the "
                  "recommended lite mode.")
        else:
            checks.append(Check(f"caveman ({runtime.name})", OPTIONAL,
                                "declined — nothing depends on it", required=False))
    return checks


FIRECRAWL_URL = "https://mcp.firecrawl.dev/v2/mcp"
FIRECRAWL_KEY_VAR = "FIRECRAWL_API_KEY"

STATUSLINE_COMMAND = "python harness/telemetry_statusline.py"

# The harness scripts an application run invokes. Without these pre-approved,
# a single /apply-any raises six to eight separate "allow this command?"
# dialogs, several of them inside a multi-minute compile loop.
HARNESS_PERMISSIONS = [
    "Bash(python harness/apply_package.py:*)",
    "Bash(python harness/fact_check.py:*)",
    "Bash(python harness/tracker_row.py:*)",
    "Bash(python harness/tracker_xlsx.py:*)",
    "Bash(python harness/archive_applications.py:*)",
    "Bash(python harness/run_log.py:*)",
    "Bash(python harness/rotate_backup.py:*)",
    "Bash(python harness/today.py:*)",
    "Bash(python harness/tex_to_md.py:*)",
    "Bash(lualatex:*)",
    "Bash(xelatex:*)",
    "Bash(pandoc:*)",
    # The ATS text-layer check in the Verification Checklist is not optional,
    # so this fires on every application; without it the seeded list still
    # leaves one dialog per run.
    "Bash(pdftotext:*)",
]


def _read_local_settings(settings: Path):
    """Parse .claude/settings.local.json, or return None if unusable."""
    import json

    if not settings.is_file():
        return {}
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _write_local_settings(settings: Path, data) -> bool:
    import json

    try:
        settings.parent.mkdir(parents=True, exist_ok=True)
        temporary = settings.with_name(settings.name + ".tmp")
        temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, settings)
    except OSError:
        return False
    return True


def offer_permissions() -> Check:
    """Pre-approve the harness's own scripts in settings.local.json.

    Never .claude/settings.json: that file is frozen by upstream's security
    guard, and a permissions file the setup script edits is a permissions file
    an attacker can edit through the setup script.
    """
    settings = ROOT / ".claude" / "settings.local.json"
    data = _read_local_settings(settings)
    if data is None:
        return Check("permissions", UNVERIFIED,
                     f"{settings.name} is not readable JSON - left alone",
                     required=False)

    permissions = data.setdefault("permissions", {})
    allow = permissions.setdefault("allow", [])
    missing = [entry for entry in HARNESS_PERMISSIONS if entry not in allow]
    if not missing:
        return Check("permissions", OK, "harness scripts already approved",
                     required=False)

    print("\n  Without this, every application run stops to ask permission for")
    print("  each script it uses - six to eight prompts, some mid-compile.")
    print("  These would be pre-approved, in your local settings only:")
    for entry in missing:
        print(f"    {entry}")
    if not confirm("\n  Pre-approve the harness's own commands?"):
        return Check("permissions", OPTIONAL,
                     "declined - expect a prompt per script", required=False)

    allow.extend(missing)
    if not _write_local_settings(settings, data):
        return Check("permissions", UNVERIFIED, f"could not write {settings.name}",
                     required=False)
    return Check("permissions", OK,
                 f"{len(missing)} command(s) approved in {settings.name}",
                 required=False)


def offer_statusline() -> Check:
    """Register the telemetry statusline (Claude only).

    This is the only channel through which the running agent can see how full
    its context window is — hooks receive no usage fields. Without it the
    continuity engine still works, but on milestone cadence alone.

    Writes `.claude/settings.local.json`. Never `.claude/settings.json`, which
    upstream's security guard freezes: a permissions file that setup edits is a
    permissions file an attacker can edit through setup.
    """
    settings = ROOT / ".claude" / "settings.local.json"
    existing = _read_local_settings(settings)
    if existing is None:
        return Check("statusline", UNVERIFIED,
                     f"{settings.name} is unreadable or not a JSON object",
                     required=False)

    current = (existing.get("statusLine") or {}).get("command")
    if current == STATUSLINE_COMMAND:
        return Check("statusline", OK, "already registered", required=False)
    if current:
        return Check("statusline", OPTIONAL,
                     "a different statusline is already configured — left alone",
                     f"To use the harness telemetry mirror instead, set "
                     f"statusLine.command to: {STATUSLINE_COMMAND}", required=False)

    if not confirm("Register the harness statusline? (optional — mirrors context and "
                   "rate-limit usage so long tasks can hand off before they run out)"):
        return Check("statusline", OPTIONAL,
                     "declined — continuity falls back to milestone cadence",
                     required=False)

    existing["statusLine"] = {"type": "command", "command": STATUSLINE_COMMAND}
    # Via the atomic helper: this rewrites the whole file, and the earlier
    # permissions step has usually already written to it. A bare write_text
    # interrupted partway (Ctrl-C during a long guided setup is the normal
    # case) left the user with a truncated settings file and no allow-list.
    if not _write_local_settings(settings, existing):
        return Check("statusline", UNVERIFIED, f"could not write {settings.name}",
                     required=False)
    return Check("statusline", OK, f"registered in {settings.name}", required=False)


def mcp_listing(runtime: Runtime) -> str:
    code, out = run([runtime.exe, "mcp", "list"], timeout=180)
    return out if code == 0 else ""


def offer_mcp(runtime: Runtime) -> list[Check]:
    """Offer the two optional MCP servers. Both degrade cleanly when absent.

    Playwright gives posting intake a real browser for JavaScript shells and
    cookie walls; Firecrawl gives it structured extraction for career pages
    and boards with no CLI. Without either, intake still works — a posting it
    cannot read is marked `unverified` rather than guessed at.
    """
    checks: list[Check] = []
    listing = mcp_listing(runtime)

    if "playwright" in listing:
        checks.append(Check(f"playwright MCP ({runtime.name})", OK,
                            "already configured", required=False))
    elif confirm(f"Add the Playwright MCP server to {runtime.name}? (optional — lets "
                 f"job-posting intake read JavaScript-rendered pages)"):
        code, out = run([runtime.exe, "mcp", "add", "playwright", "--",
                         "npx", "@playwright/mcp@latest"], timeout=300)
        ok = code == 0 and "playwright" in mcp_listing(runtime)
        checks.append(Check(
            f"playwright MCP ({runtime.name})", OK if ok else UNVERIFIED,
            "configured" if ok else "add command ran but the server is not listed",
            "" if ok else out.strip()[:200], required=False))
    else:
        checks.append(Check(f"playwright MCP ({runtime.name})", OPTIONAL,
                            "declined — blocked pages will be marked `unverified`",
                            required=False))

    if "firecrawl" in listing or "fcrawl" in listing:
        checks.append(Check(f"firecrawl MCP ({runtime.name})", OK,
                            "already configured", required=False))
    elif confirm(f"Add the Firecrawl MCP server to {runtime.name}? (optional — "
                 f"structured extraction for career pages and non-CLI boards)"):
        has_key = bool(os.environ.get(FIRECRAWL_KEY_VAR))
        # The key is referenced by variable NAME, never read or written here.
        # Without one, the keyless tier still provides search/scrape/parse.
        if runtime.name == "claude":
            cmd = [runtime.exe, "mcp", "add", "--transport", "http",
                   "firecrawl", FIRECRAWL_URL]
            if has_key:
                cmd += ["--header", f"Authorization: Bearer ${{{FIRECRAWL_KEY_VAR}}}"]
        else:
            cmd = [runtime.exe, "mcp", "add", "firecrawl", "--url", FIRECRAWL_URL]
            if has_key:
                cmd += ["--bearer-token-env-var", FIRECRAWL_KEY_VAR]
        code, out = run(cmd, timeout=300)
        ok = code == 0 and "firecrawl" in mcp_listing(runtime)
        tier = "authenticated" if has_key else "keyless tier (rate-limited)"
        checks.append(Check(
            f"firecrawl MCP ({runtime.name})", OK if ok else UNVERIFIED,
            tier if ok else "add command ran but the server is not listed",
            "" if ok else out.strip()[:200], required=False))
        if not has_key:
            print(f"  Using the keyless tier. A free account at https://firecrawl.dev "
                  f"gives more quota — no payment needed. Set {FIRECRAWL_KEY_VAR} in "
                  f"your environment and re-run setup — setup passes the variable "
                  f"name to the runtime and never reads or stores the key itself.")
    else:
        checks.append(Check(f"firecrawl MCP ({runtime.name})", OPTIONAL, "declined",
                            required=False))
    return checks


# --------------------------------------------------------------------------
# dependency installs
# --------------------------------------------------------------------------


def install_python_deps() -> Check:
    req = ROOT / "requirements.txt"
    if not req.is_file():
        return Check("Python packages", MISSING, "requirements.txt not found")
    step("installing the Python packages (pyyaml, openpyxl, pypdf)")
    code, out = run([sys.executable, "-m", "pip", "install", "-r", str(req)],
                    timeout=900)
    if code != 0:
        return Check("Python packages", MISSING, "pip install failed",
                     out.strip()[-300:])
    return check_python_deps()  # prove it by importing, not by pip's exit code


def portal_cli_dirs() -> list[Path]:
    return sorted(p for p in ROOT.glob(".agents/skills/*/cli") if p.is_dir())


def install_portal_deps() -> list[Check]:
    bun, stale = find_tool("bun")
    dirs = portal_cli_dirs()
    if not dirs:
        return [Check("Portal CLIs", UNVERIFIED, "no CLI directories found",
                      "Expected .agents/skills/*/cli — has the tree moved?")]
    if not bun or stale:
        return [Check("Portal CLIs", MISSING,
                      f"{len(dirs)} CLIs cannot be prepared without a working Bun",
                      "Fix the Bun row above, then re-run setup.")]
    failed: list[str] = []
    step(f"installing dependencies for {len(dirs)} job-board tools "
         f"- this takes a few minutes")
    for index, cli in enumerate(dirs, 1):
        step(f"  [{index}/{len(dirs)}] {cli.parent.name}")
        code, out = run([bun, "install"], timeout=600, cwd=cli)
        if code != 0:
            # `@types/bun` pulls in the `bun` npm package, whose postinstall
            # downloads a platform binary and fails on Windows the first time
            # ("Failed to find package @oven/bun-windows-x64-baseline"). The
            # packages themselves are already extracted by then, so the second
            # install completes. Measured: 4 of 7 CLIs fail on a clean clone
            # and all 7 pass on a re-run, which is the loop this removes.
            step("      first attempt failed, retrying once")
            code, out = run([bun, "install"], timeout=600, cwd=cli)
        if code != 0:
            tail = out.strip().splitlines()[-1][:80] if out.strip() else "failed"
            failed.append(f"{cli.parent.name}: {tail}")
    if failed:
        return [Check("Portal CLIs", DEGRADED, f"{len(failed)} of {len(dirs)} failed",
                      "; ".join(failed)[:300])]
    return [Check("Portal CLIs", OK, f"{len(dirs)} CLIs, dependencies installed")]


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------


def print_doctor(checks: list[Check]) -> int:
    section("Doctor")
    width = max((len(c.name) for c in checks), default=10)
    for check in checks:
        print(f"  {check.name.ljust(width)}  {check.status.ljust(13)}  {check.detail}")
    problems = [c for c in checks if c.required and c.status in REQUIRED_BAD]
    advisories = [c for c in checks if c not in problems and c.fix]
    if advisories:
        print("\n  Notes:")
        for check in advisories:
            print(f"    - {check.name}: {check.fix}")
    if problems:
        print(f"\n  {len(problems)} required item(s) need attention:")
        for check in problems:
            print(f"    - {check.name}: {check.detail}")
            if check.fix:
                print(f"      fix: {check.fix}")
        print("\n  The harness will not work correctly until these are resolved.")
    else:
        # A tool on the persistent PATH but not this shell's is not a failure,
        # but it is not an all-clear either: the job-board install reads the
        # shell's PATH and fails on exactly this state. Saying "all in place"
        # above the restart note contradicts it.
        stale = [c for c in checks if c.status == STALE_PATH]
        if stale:
            print(f"\n  {len(stale)} tool(s) are installed but not visible to this "
                  f"shell. Close and reopen your terminal, then re-run setup — "
                  f"anything that needs them is skipped until you do.")
        else:
            print("\n  All required prerequisites are in place.")
    return len(problems)


def main(argv: list[str] | None = None) -> int:
    global AUTO_YES, DOCTOR_ONLY

    parser = argparse.ArgumentParser(
        description="Set up the Job Search Agent Harness and report what is missing."
    )
    parser.add_argument("--doctor", action="store_true",
                        help="check and report only; install and change nothing")
    parser.add_argument("--yes", action="store_true",
                        help="take the recommended answer to every prompt")
    parser.add_argument("--quick", action="store_true",
                        help="skip the stock-template test compiles (faster, less proof)")
    args = parser.parse_args(argv)

    AUTO_YES = args.yes
    DOCTOR_ONLY = args.doctor

    print("Job Search Agent Harness — setup")
    print(f"Repository: {ROOT}")
    if DOCTOR_ONLY:
        print("Mode: doctor only. Nothing will be installed or changed.")
    elif offer_express():
        AUTO_YES = True
        print("\nExpress setup: taking the recommended answer to each item.")

    checks: list[Check] = []

    section("Prerequisites")
    checks.append(check_python())
    checks.append(check_simple("Node", "node", ["--version"]))
    checks.append(check_bun())
    checks.extend(check_tex(quick=args.quick))
    checks.append(check_poppler())
    checks.append(check_simple("pandoc", "pandoc", ["--version"], required=False))
    for check in checks:
        detail = f" — {check.detail}" if check.detail else ""
        print(f"  {check.name}: {check.status}{detail}")

    section("Python packages")
    deps = check_python_deps()
    if deps.status != OK and not DOCTOR_ONLY and confirm(
        "Install the pinned Python packages from requirements.txt?"
    ):
        deps = install_python_deps()
    print(f"  {deps.name}: {deps.status} — {deps.detail}")
    checks.append(deps)

    section("Job-board CLIs")
    if DOCTOR_ONLY:
        found = portal_cli_dirs()
        checks.append(Check("Portal CLIs", UNVERIFIED,
                            f"{len(found)} found; dependencies not checked in "
                            f"doctor mode", required=False))
        print(f"  {len(found)} CLI directories found (not prepared in doctor mode)")
    elif confirm(f"Install dependencies for the {len(portal_cli_dirs())} "
                 f"job-board CLIs?"):
        portal = install_portal_deps()
        for check in portal:
            print(f"  {check.name}: {check.status} — {check.detail}")
        checks.extend(portal)
    else:
        checks.append(Check("Portal CLIs", OPTIONAL,
                            "declined — job search will not run", required=False))

    section("Agent runtimes")
    runtimes = detect_runtimes()
    if not runtimes:
        print("  No agent runtime found on PATH (looked for `claude` and `codex`).")
        checks.append(Check("Agent runtime", MISSING,
                            "neither claude nor codex found",
                            "Install Claude Code or the Codex CLI — the harness runs "
                            "inside one of them."))
    else:
        print(f"  Found: {', '.join(r.name for r in runtimes)}")
        for runtime in runtimes:
            checks.append(Check(f"runtime: {runtime.name}", OK, runtime.exe))

    if runtimes and not DOCTOR_ONLY:
        for runtime in runtimes:
            section(f"Plugins for {runtime.name}")
            checks.extend(offer_plugins(runtime))
            section(f"Optional MCP servers for {runtime.name}")
            checks.extend(offer_mcp(runtime))
            if runtime.name == "claude":
                section("Permissions")
                checks.append(offer_permissions())
                section("Session continuity")
                checks.append(offer_statusline())

    failures = print_doctor(checks)
    if not DOCTOR_ONLY:
        if failures:
            # Guidance matters MORE when something failed, not less. The
            # previous version printed the next step only on a clean run, so
            # the user who most needed direction got a list of complaints and
            # nothing to do about it.
            print("\nNext step: fix the item(s) above, then run this again:")
            print(f"    {sys.executable} harness_setup.py")
        else:
            print("\nNext step: open this folder in your agent and run "
                  "/setup-harness to build your evidence bank and preferences.")
            print("Then /today will tell you what to do each morning.")
    return failures


if __name__ == "__main__":
    sys.exit(main())
