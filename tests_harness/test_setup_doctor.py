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

import setup  # noqa: E402  (the path shim above must run first)


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


if __name__ == "__main__":
    unittest.main()
