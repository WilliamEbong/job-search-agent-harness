"""Tests for setup.py's probes and doctor table.

Every probe is exercised against a *mocked* PATH and mocked subprocess calls,
so the suite asserts the same behaviour on any machine — including CI, which
has no TeX, no Bun and no agent runtime.

The cases worth reading are the ones that pin down defects the build actually
hit, because those are what a future refactor is most likely to undo:

* `test_bun_present_but_panicking_is_degraded` — Bun's stock build installs
  fine on a CPU without AVX2 and then panics on every call. A presence-only
  check reports green on a machine where all six portal CLIs are dead.
* `test_poppler_needs_pdfinfo_too` — Git for Windows ships pdftotext but not
  pdfinfo, so checking pdftotext alone reports poppler present when upstream's
  PDF verification cannot run.
* `test_tool_on_persistent_path_only_says_restart_shell` — a tool installed
  seconds ago is on the registry PATH but not in the running shell; reporting
  MISSING sends the user round in circles re-installing it.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import harness_setup as setup  # noqa: E402  (the path shim above must run first)


def fake_which(available: dict[str, str]):
    """shutil.which stand-in. `available` maps tool name -> fake path."""

    def _which(name, mode=None, path=None):
        # When called with an explicit `path=`, setup is probing the
        # persistent Windows PATH; only tools flagged persistent-only resolve.
        if path is not None:
            return available.get(f"persistent:{name}")
        return available.get(name)

    return _which


def fake_run(results: dict[str, tuple[int, str]], default=(0, "")):
    """setup.run stand-in, keyed on the first argument's basename."""

    def _run(args, timeout=180, cwd=None):
        return results.get(Path(args[0]).stem, default)

    return _run


class BunCheck(unittest.TestCase):
    def test_missing_bun_is_missing(self):
        with mock.patch.object(setup.shutil, "which", fake_which({})), \
             mock.patch.object(setup, "_persistent_path_dirs", return_value=[]):
            check = setup.check_bun()
        self.assertEqual(check.status, setup.MISSING)

    def test_working_bun_is_ok(self):
        with mock.patch.object(setup.shutil, "which",
                               fake_which({"bun": "/fake/bun"})), \
             mock.patch.object(setup, "run", fake_run({"bun": (0, "1.3.14\n")})):
            check = setup.check_bun()
        self.assertEqual(check.status, setup.OK)
        self.assertIn("1.3.14", check.detail)

    def test_bun_present_but_panicking_is_degraded(self):
        """A no-AVX2 CPU: bun exists, resolves, and dies on every call."""
        panic = (3, "Features: no_avx2\npanic: Illegal instruction at address 0x7FF\n")
        with mock.patch.object(setup.shutil, "which",
                               fake_which({"bun": "/fake/bun"})), \
             mock.patch.object(setup, "run", fake_run({"bun": panic})):
            check = setup.check_bun()
        self.assertEqual(check.status, setup.DEGRADED)
        self.assertIn("AVX2", check.detail)
        # The fix must name the baseline package, or the user cannot act on it.
        self.assertIn("Oven-sh.Bun.Baseline", check.fix)

    def test_bun_nonzero_exit_is_degraded_not_ok(self):
        with mock.patch.object(setup.shutil, "which",
                               fake_which({"bun": "/fake/bun"})), \
             mock.patch.object(setup, "run", fake_run({"bun": (1, "some error")})):
            check = setup.check_bun()
        self.assertEqual(check.status, setup.DEGRADED)


class PopplerCheck(unittest.TestCase):
    def test_both_binaries_present_is_ok(self):
        available = {"pdftotext": "/fake/pdftotext", "pdfinfo": "/fake/pdfinfo"}
        with mock.patch.object(setup.shutil, "which", fake_which(available)):
            check = setup.check_poppler()
        self.assertEqual(check.status, setup.OK)

    def test_poppler_needs_pdfinfo_too(self):
        """Git for Windows ships pdftotext only — that is not poppler."""
        with mock.patch.object(setup.shutil, "which",
                               fake_which({"pdftotext": "/git/pdftotext"})), \
             mock.patch.object(setup, "_persistent_path_dirs", return_value=[]):
            check = setup.check_poppler()
        self.assertEqual(check.status, setup.MISSING)
        self.assertIn("pdfinfo", check.detail)
        self.assertIn("Git for Windows", check.detail)

    def test_neither_binary_present_is_missing(self):
        with mock.patch.object(setup.shutil, "which", fake_which({})), \
             mock.patch.object(setup, "_persistent_path_dirs", return_value=[]):
            check = setup.check_poppler()
        self.assertEqual(check.status, setup.MISSING)


class StalePathCheck(unittest.TestCase):
    def test_tool_on_persistent_path_only_says_restart_shell(self):
        available = {"persistent:pandoc": "/fake/pandoc"}
        with mock.patch.object(setup.shutil, "which", fake_which(available)), \
             mock.patch.object(setup, "_persistent_path_dirs", return_value=["/fake"]):
            check = setup.check_simple("pandoc", "pandoc", ["--version"],
                                       required=False)
        self.assertEqual(check.status, setup.STALE_PATH)
        self.assertIn("reopen", check.fix.lower())

    def test_find_tool_prefers_the_live_shell_path(self):
        available = {"bun": "/live/bun", "persistent:bun": "/registry/bun"}
        with mock.patch.object(setup.shutil, "which", fake_which(available)):
            path, stale = setup.find_tool("bun")
        self.assertEqual(path, "/live/bun")
        self.assertFalse(stale)


class TexCheck(unittest.TestCase):
    def test_missing_engines_are_reported_individually(self):
        with mock.patch.object(setup.shutil, "which", fake_which({})), \
             mock.patch.object(setup, "_persistent_path_dirs", return_value=[]):
            checks = setup.check_tex(quick=True)
        names = {c.name: c.status for c in checks}
        self.assertEqual(names["lualatex"], setup.MISSING)
        self.assertEqual(names["xelatex"], setup.MISSING)

    def test_quick_mode_marks_compiles_unverified_not_ok(self):
        """--quick must never claim a compile passed that never ran."""
        available = {"lualatex": "/fake/lualatex", "xelatex": "/fake/xelatex"}
        with mock.patch.object(setup.shutil, "which", fake_which(available)), \
             mock.patch.object(setup, "run", fake_run({}, default=(0, "TeX 1.0"))):
            checks = setup.check_tex(quick=True)
        compiles = [c for c in checks if c.name.endswith("compile")]
        self.assertEqual(len(compiles), 2)
        for check in compiles:
            self.assertEqual(check.status, setup.UNVERIFIED)

    def test_failed_compile_is_degraded_with_the_latex_error(self):
        log = "This is LuaTeX\n! LaTeX Error: File `moderncv.cls' not found.\n"
        with mock.patch.object(setup, "run", fake_run({}, default=(1, log))), \
             mock.patch.object(Path, "is_file", return_value=True):
            check = setup._test_compile("/fake/lualatex", "lualatex", Path("cv"),
                                        "main_example.tex", "CV template")
        self.assertEqual(check.status, setup.DEGRADED)
        self.assertIn("moderncv.cls", check.fix)


class PluginVerification(unittest.TestCase):
    """An install is not done until the runtime lists it."""

    def setUp(self):
        self.runtime = setup.Runtime(name="claude", exe="/fake/claude",
                                     install_verb="install")

    def test_install_verified_by_relisting(self):
        with mock.patch.object(setup, "run", return_value=(0, "ok")), \
             mock.patch.object(setup, "installed_plugins",
                               return_value="ponytail@ponytail enabled"):
            check = setup.install_plugin(self.runtime, "DietrichGebert/ponytail",
                                         "ponytail")
        self.assertEqual(check.status, setup.OK)

    def test_silent_install_failure_is_unverified_not_ok(self):
        """Exit 0 with the plugin absent from `plugin list` is not success."""
        with mock.patch.object(setup, "run", return_value=(0, "ok")), \
             mock.patch.object(setup, "installed_plugins", return_value="(none)"):
            check = setup.install_plugin(self.runtime, "DietrichGebert/ponytail",
                                         "ponytail")
        self.assertEqual(check.status, setup.UNVERIFIED)

    def test_marketplace_failure_reports_missing(self):
        with mock.patch.object(setup, "run", return_value=(1, "network error")):
            check = setup.install_plugin(self.runtime, "JuliusBrussee/caveman",
                                         "caveman")
        self.assertEqual(check.status, setup.MISSING)


class CavemanOffer(unittest.TestCase):
    """plan-M test 39: explained, lite recommended, decline leaves it out."""

    def setUp(self):
        self.runtime = setup.Runtime(name="claude", exe="/fake/claude",
                                     install_verb="install")

    def test_explanation_states_what_it_does_and_recommends_lite(self):
        text = setup.CAVEMAN_EXPLANATION.lower()
        self.assertIn("optional", text)
        self.assertIn("lite", text)
        # It must promise not to touch user-facing application prose.
        self.assertIn("cover letter", text)

    def test_declining_leaves_caveman_uninstalled(self):
        with mock.patch.object(setup, "installed_plugins", return_value=""), \
             mock.patch.object(setup, "confirm", return_value=False), \
             mock.patch.object(setup, "install_plugin") as installer, \
             mock.patch("builtins.print"):
            checks = setup.offer_plugins(self.runtime)
        installer.assert_not_called()
        caveman = [c for c in checks if "caveman" in c.name]
        self.assertEqual(caveman[0].status, setup.OPTIONAL)

    def test_accepting_installs_and_verifies(self):
        installed = setup.Check("caveman (claude)", setup.OK, "installed and listed")
        with mock.patch.object(setup, "installed_plugins", return_value=""), \
             mock.patch.object(setup, "confirm", return_value=True), \
             mock.patch.object(setup, "install_plugin",
                               return_value=installed) as installer, \
             mock.patch("builtins.print"):
            setup.offer_plugins(self.runtime)
        repos = [call.args[1] for call in installer.call_args_list]
        self.assertIn("JuliusBrussee/caveman", repos)

    def test_lite_mode_defaults_to_the_reply_shortening_plugins(self):
        defaults = {}

        def remember(question, default=True):
            defaults[question.split()[1]] = default
            return False

        with mock.patch.object(setup, "installed_plugins", return_value=""), \
             mock.patch.object(setup, "confirm", side_effect=remember), \
             mock.patch("builtins.print"):
            setup.offer_plugins(self.runtime, "lite")
            lite = dict(defaults)
            setup.offer_plugins(self.runtime, "standard")
        self.assertTrue(lite["Caveman"] and lite["i-have-adhd"])
        self.assertFalse(defaults["Caveman"] or defaults["i-have-adhd"])

    def test_codex_gets_the_ref_the_adhd_repo_asks_for(self):
        codex = setup.Runtime(name="codex", exe="/fake/codex", install_verb="add")
        with mock.patch.object(setup, "run", return_value=(0, "")) as run, \
             mock.patch.object(setup, "installed_plugins", return_value="i-have-adhd"):
            setup.install_plugin(codex, "ayghri/i-have-adhd", "i-have-adhd", codex_ref="main")
        self.assertEqual(["/fake/codex", "plugin", "marketplace", "add",
                          "ayghri/i-have-adhd", "--ref", "main"], run.call_args_list[0].args[0])


class PlanAndMode(unittest.TestCase):
    """Setup recommends lite below ChatGPT Pro / Claude Max and records the choice."""

    def pick(self, answer: str):
        with mock.patch("builtins.input", return_value=answer), \
             mock.patch("builtins.print"):
            return setup.ask_plan()

    def test_recommendation_follows_the_plan(self):
        self.assertEqual(("chatgpt-plus", "lite"), self.pick("1"))
        self.assertEqual(("chatgpt-pro", "standard"), self.pick("2"))
        self.assertEqual(("claude-pro", "lite"), self.pick("3"))
        self.assertEqual(("claude-max", "standard"), self.pick("4"))

    def test_no_answer_takes_the_cheapest_safe_choice(self):
        self.assertEqual(("other", "lite"), self.pick(""))
        self.assertEqual(("other", "lite"), self.pick("9"))

    def test_choice_is_recorded_once_and_never_overwrites(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup.seed_preferences("claude-pro", "lite", root)
            text = (root / "preferences.yaml").read_text(encoding="utf-8")
            self.assertIn("mode: lite", text)
            self.assertIn("plan: claude-pro", text)
            setup.seed_preferences("claude-max", "standard", root)
            self.assertEqual(text, (root / "preferences.yaml").read_text(encoding="utf-8"))

    def test_standard_is_recorded_as_the_focused_usage_mode(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            setup.seed_preferences("claude-max", "standard", Path(tmp))
            self.assertIn("mode: focused",
                          (Path(tmp) / "preferences.yaml").read_text(encoding="utf-8"))


class FirecrawlSecrets(unittest.TestCase):
    """The API key is referenced by name, never copied into a config."""

    def setUp(self):
        self.runtime = setup.Runtime(name="claude", exe="/fake/claude",
                                     install_verb="install")

    def test_keyless_when_no_env_var(self):
        captured: list[list[str]] = []

        def record(args, timeout=180, cwd=None):
            captured.append(args)
            return 0, "firecrawl"

        with mock.patch.object(setup, "mcp_listing", side_effect=["", "firecrawl"]), \
             mock.patch.object(setup, "confirm", side_effect=[False, True]), \
             mock.patch.object(setup, "run", record), \
             mock.patch.dict(setup.os.environ, {}, clear=True), \
             mock.patch("builtins.print"):
            setup.offer_mcp(self.runtime)
        flat = " ".join(" ".join(a) for a in captured)
        self.assertIn(setup.FIRECRAWL_URL, flat)
        self.assertNotIn("Authorization", flat)

    def test_key_is_passed_as_a_variable_reference_not_a_value(self):
        captured: list[list[str]] = []

        def record(args, timeout=180, cwd=None):
            captured.append(args)
            return 0, "firecrawl"

        secret = "fc-secret-value-that-must-never-be-written"
        with mock.patch.object(setup, "mcp_listing", side_effect=["", "firecrawl"]), \
             mock.patch.object(setup, "confirm", side_effect=[False, True]), \
             mock.patch.object(setup, "run", record), \
             mock.patch.dict(setup.os.environ,
                             {setup.FIRECRAWL_KEY_VAR: secret}, clear=True), \
             mock.patch("builtins.print"):
            setup.offer_mcp(self.runtime)
        flat = " ".join(" ".join(a) for a in captured)
        self.assertNotIn(secret, flat)
        self.assertIn(setup.FIRECRAWL_KEY_VAR, flat)


class DoctorTable(unittest.TestCase):
    def test_exit_code_counts_only_required_failures(self):
        checks = [
            setup.Check("Python", setup.OK, "3.14.3"),
            setup.Check("Bun", setup.DEGRADED, "crashes"),
            setup.Check("lualatex", setup.MISSING, "not on PATH"),
            setup.Check("pandoc", setup.MISSING, "not on PATH", required=False),
            setup.Check("caveman", setup.OPTIONAL, "declined", required=False),
        ]
        with mock.patch("builtins.print"):
            failures = setup.print_doctor(checks)
        self.assertEqual(failures, 2)

    def test_all_green_returns_zero(self):
        checks = [setup.Check("Python", setup.OK, "3.14.3"),
                  setup.Check("pandoc", setup.OPTIONAL, "declined", required=False)]
        with mock.patch("builtins.print"):
            self.assertEqual(setup.print_doctor(checks), 0)

    def test_unverified_is_not_counted_as_pass_or_fail(self):
        """UNVERIFIED must stay visible rather than silently becoming OK."""
        checks = [setup.Check("lualatex compile", setup.UNVERIFIED,
                              "skipped (--quick)", required=False)]
        with mock.patch("builtins.print"):
            self.assertEqual(setup.print_doctor(checks), 0)
        self.assertNotEqual(checks[0].status, setup.OK)


class ConfirmBehaviour(unittest.TestCase):
    def tearDown(self):
        setup.AUTO_YES = False
        setup.DOCTOR_ONLY = False

    def test_doctor_mode_never_installs(self):
        setup.DOCTOR_ONLY = True
        self.assertFalse(setup.confirm("Install something?", default=True))

    def test_yes_mode_takes_the_default(self):
        setup.AUTO_YES = True
        with mock.patch("builtins.print"):
            self.assertTrue(setup.confirm("Recommended thing?", default=True))
            self.assertFalse(setup.confirm("Opt-in thing?", default=False))

    def test_piped_stdin_falls_back_to_default(self):
        with mock.patch("builtins.input", side_effect=EOFError), \
             mock.patch("builtins.print"):
            self.assertFalse(setup.confirm("Install Caveman?", default=False))


class PortalInstallRetry(unittest.TestCase):
    """A clean clone fails `bun install` once and succeeds on the second run.

    `@types/bun` pulls in the `bun` npm package, whose postinstall downloads a
    platform binary; on Windows it exits 1 with "Failed to find package
    @oven/bun-windows-x64-baseline". Measured on a clean clone of 2a4772b: 4 of
    7 CLIs failed, setup exited 1 telling the user the harness would not work,
    and a plain re-run fixed all 7 without any other change.
    """

    POSTINSTALL_FAILURE = (1, 'error: postinstall script from "bun" exited with 1')

    def _install(self, outcomes):
        """Run install_portal_deps against two fake CLI dirs. `outcomes` is the
        sequence of (code, output) pairs returned per `bun install` call."""
        calls: list[Path] = []

        def _run(args, timeout=180, cwd=None):
            calls.append(cwd)
            return outcomes[min(len(calls) - 1, len(outcomes) - 1)]

        dirs = [Path("/fake/a/cli"), Path("/fake/b/cli")]
        with mock.patch.object(setup.shutil, "which",
                               fake_which({"bun": "/fake/bun"})), \
             mock.patch.object(setup, "portal_cli_dirs", return_value=dirs), \
             mock.patch.object(setup, "run", _run), \
             mock.patch("builtins.print"):
            return setup.install_portal_deps(), calls

    def test_first_attempt_failure_is_retried_and_clears(self):
        checks, calls = self._install([self.POSTINSTALL_FAILURE, (0, "ok")])
        self.assertEqual(checks[0].status, setup.OK)
        # Two attempts on the first directory, one on the second.
        self.assertEqual(len(calls), 3)

    def test_a_failure_that_survives_the_retry_is_still_reported(self):
        checks, calls = self._install([self.POSTINSTALL_FAILURE])
        self.assertEqual(checks[0].status, setup.DEGRADED)
        self.assertIn("2 of 2 failed", checks[0].detail)
        self.assertEqual(len(calls), 4)  # never more than one retry each


class SetupShim(unittest.TestCase):
    """setup.py is a compatibility shim over harness_setup.py.

    A root setup.py is a contract with pip: `pip install .` executes it with
    setuptools command arguments, which here used to mean an interactive
    installer running inside a package build. The shim keeps `python setup.py`
    working for humans and refuses the packaging invocations.
    """

    def _run(self, *args: str):
        import subprocess
        return subprocess.run(
            [sys.executable, str(Path(setup.__file__).parent / "setup.py"),
             *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120,
        )

    def test_pip_style_invocation_is_refused(self):
        result = self._run("egg_info")
        self.assertEqual(result.returncode, 1)
        self.assertIn("harness_setup.py", result.stderr)

    def test_human_invocation_still_reaches_the_installer(self):
        result = self._run("--doctor", "--quick")
        self.assertIn("Doctor", result.stdout)


class SeededPermissions(unittest.TestCase):
    def test_the_ats_text_extraction_is_pre_approved(self):
        """`pdftotext -layout` is a mandatory step of the Verification
        Checklist, so leaving it out costs one dialog on every application."""
        self.assertIn("Bash(pdftotext:*)", setup.HARNESS_PERMISSIONS)

    def test_scripts_every_search_and_package_runs_are_pre_approved(self):
        for script in ("ats_check", "lite_search", "shortlist_row"):
            self.assertIn(f"Bash(python harness/{script}.py:*)", setup.HARNESS_PERMISSIONS)


class CodexNetworkCheck(unittest.TestCase):
    """Codex's workspace-write sandbox has no network unless the user enables
    it, and a board CLI that cannot connect looks like a quiet board."""

    def check(self, config: str | None):
        import tempfile
        with tempfile.TemporaryDirectory() as home:
            if config is not None:
                (Path(home) / "config.toml").write_text(config, encoding="utf-8")
            return setup.check_codex_network(Path(home))

    def test_no_config_means_the_default_which_is_off(self):
        check = self.check(None)
        self.assertEqual(check.status, setup.OPTIONAL)
        self.assertIn("network_access = true", check.fix)
        self.assertFalse(check.required)

    def test_network_enabled_for_workspace_write_is_ok(self):
        check = self.check('[sandbox_workspace_write]\nnetwork_access = true\n')
        self.assertEqual(check.status, setup.OK)

    def test_full_access_sandbox_is_ok(self):
        self.assertEqual(self.check('sandbox_mode = "danger-full-access"\n').status, setup.OK)

    def test_profiles_are_not_guessed_at(self):
        self.assertEqual(self.check('profile = "work"\n').status, setup.UNVERIFIED)

    def test_unreadable_config_is_unverified_not_ok(self):
        self.assertEqual(self.check("this is = = not toml").status, setup.UNVERIFIED)


if __name__ == "__main__":
    unittest.main()
