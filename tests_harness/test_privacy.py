"""Tests for the two privacy guards, and for the continuity layer's contracts.

The guards are deliberately two separate tools with different failure modes,
and these tests pin that split:

* `tools/harness_guards.py` is structural — ignore rules present, nothing
  personal tracked. It cannot see a phone number pasted into a README.
* `harness/privacy_sweep.py` is content — it scans what files actually say. It
  cannot see a deleted gitignore rule.

Merging them would lose one of those, which is why `test_the_two_guards_check_
different_things` exists.

The sweep's allow-list is the part most likely to be loosened under pressure, so
several tests assert it still catches the things it is for.
"""

from __future__ import annotations

import importlib
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))

privacy_sweep = importlib.import_module("privacy_sweep")


def flat(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8").lower())


class GuardsPassOnThisRepo(unittest.TestCase):
    def test_harness_guards_pass(self):
        proc = subprocess.run([sys.executable, str(ROOT / "tools" / "harness_guards.py")],
                              capture_output=True, text=True, cwd=str(ROOT))
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    def test_privacy_sweep_reports_no_blocking_hits(self):
        proc = subprocess.run([sys.executable, str(ROOT / "harness" / "privacy_sweep.py")],
                              capture_output=True, text=True, cwd=str(ROOT))
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("no personal data found", proc.stdout)

    def test_upstream_security_guards_still_pass(self):
        """The harness must never have weakened upstream's own guard."""
        proc = subprocess.run([sys.executable, str(ROOT / "tools" / "security_guards.py")],
                              capture_output=True, text=True, cwd=str(ROOT))
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)


class SweepStillCatchesRealData(unittest.TestCase):
    """The allow-list must not have become an everything-list."""

    def scan_text(self, text: str) -> list:
        """Re-implements the scan loop, but must call `is_allowed` the way
        production does — with the label.

        It used to omit the third argument, so `label` defaulted to "" and the
        CONTACT_LABELS branch (the whole point of the split: a placeholder
        elsewhere on a line must not excuse a real email) was unreachable in
        every test in this class. Deleting that branch left them all green.
        """
        hits = []
        for line_no, line in enumerate(text.splitlines(), 1):
            for label, pattern in privacy_sweep.BLOCKING_PATTERNS:
                for match in pattern.finditer(line):
                    if privacy_sweep.is_allowed(match.group(0), line, label):
                        continue
                    hits.append((line_no, label, match.group(0)))
        return hits

    def test_a_placeholder_on_the_line_does_not_excuse_a_real_email(self):
        """REGRESSION: one `your-` anywhere on a line excused every match on it.

        The line-level placeholder check ran above the contact-label split, so
        a template-looking line carrying one real address shipped clean — the
        exact hole the split was written to close.
        """
        hits = self.scan_text(
            "your-config example: jane.doe@realcompany.co.uk")
        self.assertTrue(any(label == "email" for _, label, _ in hits), hits)

    def test_a_placeholder_inside_the_match_is_still_excused(self):
        self.assertEqual([], self.scan_text("email: your.email@example.com"))

    def test_catches_a_real_email(self):
        hits = self.scan_text("Contact me at jane.doe@realcompany.co.uk about the role.")
        self.assertTrue(any(label == "email" for _, label, _ in hits))

    def test_catches_a_real_phone_number(self):
        hits = self.scan_text("Call 604-555-9182 for details.")
        self.assertTrue(any(label == "phone" for _, label, _ in hits))

    def test_catches_a_canadian_postal_code(self):
        hits = self.scan_text("Mail it to R3C 4T2 before Friday.")
        self.assertTrue(any("postal" in label for _, label, _ in hits))

    def test_catches_an_api_key(self):
        hits = self.scan_text("token: ghp_abcdefghijklmnopqrstuvwxyz0123456789")
        self.assertTrue(any("key" in label or "token" in label for _, label, _ in hits))

    def test_catches_a_real_linkedin_profile(self):
        hits = self.scan_text("Profile: linkedin.com/in/jane-doe-8891")
        self.assertTrue(any("linkedin" in label for _, label, _ in hits))

    def test_allows_the_demo_candidate(self):
        hits = self.scan_text(
            "Riley Chen, riley.chen@example.com, +1 555-0142"
        )
        self.assertEqual([], hits)

    def test_allows_placeholder_tokens(self):
        hits = self.scan_text(
            "Email: [YOUR_EMAIL] · linkedin.com/in/your-profile · @@CONTACT@@"
        )
        self.assertEqual([], hits)

    def test_github_urls_are_advisory_not_blocking(self):
        """Attribution links must not fail the build.

        The first version of the sweep blocked on these and produced 71 hits,
        essentially all of them required licence attribution in upstream's own
        CONTRIBUTING.md and CHANGELOG.md. A gate that has to be waived every run
        is not a gate.
        """
        labels = {label for label, _ in privacy_sweep.BLOCKING_PATTERNS}
        self.assertNotIn("github url", labels)
        advisory = {label for label, _ in privacy_sweep.ADVISORY_PATTERNS}
        self.assertIn("github url", advisory)

    def test_strict_mode_promotes_advisory_to_blocking(self):
        """The category is kept, not deleted — the owner can still demand it."""
        blocking, advisory = privacy_sweep.scan(strict=True)
        self.assertEqual([], advisory)


class GuardSeparation(unittest.TestCase):
    def test_the_two_guards_check_different_things(self):
        structural = (ROOT / "tools" / "harness_guards.py").read_text(encoding="utf-8")
        content = (ROOT / "harness" / "privacy_sweep.py").read_text(encoding="utf-8")
        # Structural guard reads git's index; content scan reads file bodies.
        self.assertIn("git", structural)
        self.assertIn("ls-files", structural)
        self.assertIn("read_text", content)
        # Each explains why it is not the other.
        self.assertIn("privacy_sweep", structural)
        self.assertIn("harness_guards", content)

    def test_guard_lists_the_harness_ignore_families(self):
        sys.path.insert(0, str(ROOT / "tools"))
        guards = importlib.import_module("harness_guards")
        for rule in ("evidence/register.yaml", "preferences.yaml", "companies.yaml",
                     "state/"):
            self.assertIn(rule, guards.REQUIRED_IGNORE_RULES)


class ContinuityContracts(unittest.TestCase):
    """P7: the handoff ritual and the honesty rules around telemetry."""

    def setUp(self):
        self.text = flat(ROOT / ".claude" / "commands" / "continue.md")

    def test_filesystem_outranks_the_handoff(self):
        self.assertIn("the filesystem is right", self.text)

    def test_handoff_names_an_exact_next_step(self):
        self.assertIn("exact next step", self.text)

    def test_do_not_redo_list_exists(self):
        self.assertIn("do not redo", self.text)

    def test_session_confirmed_facts_are_not_treated_as_evidence(self):
        self.assertIn("holding pen, not a truth store", self.text)

    def test_codex_never_prints_a_percentage(self):
        self.assertIn("never print a percentage on codex", self.text)

    def test_cross_runtime_expectation_is_set_honestly(self):
        self.assertIn("the state carries fully, the conversation does not", self.text)


class TelemetryMirror(unittest.TestCase):
    def test_extracts_the_documented_fields(self):
        sys.path.insert(0, str(ROOT / "harness"))
        module = importlib.import_module("telemetry_statusline")
        record = module.extract({
            "context_window": {"used_percentage": 81.5},
            "rate_limits": {"five_hour": {"used_percentage": 40},
                            "seven_day": {"used_percentage": 12}},
            "model": {"display_name": "Opus"},
        })
        self.assertEqual(81.5, record["context_pct"])
        self.assertEqual(40, record["five_hour_pct"])
        self.assertEqual(12, record["seven_day_pct"])
        self.assertTrue(record["caveats"])

    def test_missing_fields_become_null_not_guesses(self):
        module = importlib.import_module("telemetry_statusline")
        record = module.extract({})
        self.assertIsNone(record["context_pct"])
        self.assertIsNone(record["five_hour_pct"])

    def test_caveats_travel_with_the_numbers(self):
        """A percentage without its caveats invites planning around a lie."""
        module = importlib.import_module("telemetry_statusline")
        joined = " ".join(module.CAVEATS).lower()
        self.assertIn("input tokens only", joined)
        self.assertIn("compact", joined)

    def test_render_never_invents_a_value(self):
        module = importlib.import_module("telemetry_statusline")
        self.assertEqual("harness", module.render(module.extract({})))


class RuntimeMap(unittest.TestCase):
    def setUp(self):
        self.text = flat(ROOT / "RUNTIME-MAP.md")

    def test_states_the_never_fork_rule(self):
        self.assertIn("never two implementations of a workflow", self.text)

    def test_codex_reviewer_is_a_sequential_fresh_pass(self):
        self.assertIn("sequential fresh pass", self.text)

    def test_codex_telemetry_absence_is_explicit(self):
        self.assertIn("never print a percentage", self.text)

    def test_lists_what_must_not_be_forked(self):
        self.assertIn("explicitly identical", self.text)

    def test_codex_stubs_exist_for_every_harness_workflow(self):
        stubs = {p.stem for p in (ROOT / ".codex" / "prompts").glob("*.md")}
        for workflow in ("setup-harness", "scrape", "apply-any", "verify-facts",
                         "fact", "tracker", "continue", "companies",
                         "career-review", "discover"):
            self.assertIn(workflow, stubs)


class Attribution(unittest.TestCase):
    """plan-M 32: attribution on the first screen, NOTICE complete."""

    def test_readme_credits_upstream_in_the_first_screen(self):
        lines = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()
        first_screen = " ".join(lines[:40]).lower()
        self.assertIn("ai-job-search", first_screen)
        self.assertIn("madslorentzen", first_screen)
        self.assertIn("mit", first_screen)

    def test_notice_credits_every_bundled_component(self):
        text = flat(ROOT / "NOTICE.md")
        for name in ("ai-job-search", "humanizer", "ponytail", "caveman",
                     "pyyaml", "openpyxl", "pypdf"):
            self.assertIn(name, text)

    def test_notice_separates_original_from_inherited(self):
        text = flat(ROOT / "NOTICE.md")
        self.assertIn("original contributions of this project", text)
        self.assertIn("would not exist without it", text)


class UserGuide(unittest.TestCase):
    """plan-M 40: the root guide covers every shipped feature."""

    def setUp(self):
        self.text = flat(ROOT / "USER-GUIDE.md")

    def test_covers_every_harness_command(self):
        for command in ("/setup-harness", "/career-review", "/companies", "/scrape",
                        "/apply-any", "/verify-facts", "/fact", "/tracker",
                        "/continue", "/outcome", "/interview"):
            self.assertIn(command, self.text)

    def test_documents_the_interview_controls(self):
        self.assertIn("speed up", self.text)
        self.assertIn("that's enough", self.text)

    def test_documents_all_five_scopes_and_three_modes(self):
        # `--scope board <name>` is the real fifth scope. The guide used to show
        # a bare `--board` flag, which `/scrape` has never implemented, and this
        # test pinned it — so the sweep that removed the phantom flag from the
        # command file left the copy users actually type from untouched.
        for scope in ("--scope companies", "--scope boards", "--scope all",
                      "--scope company", "--scope board"):
            self.assertIn(scope, self.text)
        for mode in ("focused", "balanced", "full"):
            self.assertIn(mode, self.text)

    def test_does_not_document_flags_scrape_never_implemented(self):
        self.assertNotIn("--board ", self.text)
        self.assertNotIn("--limit", self.text)

    def test_documents_the_doctor_statuses_including_degraded(self):
        for status in ("degraded", "restart shell", "unverified"):
            self.assertIn(status, self.text)

    def test_documents_the_three_legitimate_gate_resolutions(self):
        self.assertIn("fix the draft", self.text)
        self.assertIn("do not edit the register to silence it", self.text)


if __name__ == "__main__":
    unittest.main()
