"""Codex runs harness workflows through thin pointer skills in `.agents/skills/`.

Codex never loads a project `.codex/prompts/` (custom prompts are deprecated and
read only from the Codex home); it discovers `.agents/skills/<name>/SKILL.md` and
runs it on `$name`. These tests pin the mechanism that works: every workflow has
a pointer, each pointer names a spec file that exists, and none can be mistaken
for a job portal, because portal discovery globs `.agents/skills/*-search/SKILL.md`.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MARKER = "Harness workflow pointer"
# `apply` redirects to /apply-any and `setup` runs inside /setup-harness
# (RUNTIME-MAP.md §1), so neither gets a pointer.
NO_POINTER = {"apply", "setup"}
# Pointers whose spec is not a command file, or is being written alongside them.
ALSO_REQUIRED = {"upskill", "lite", "recruiter"}


def pointers() -> dict[str, tuple[dict, str]]:
    found = {}
    for path in sorted((ROOT / ".agents" / "skills").glob("*/SKILL.md")):
        head, body = path.read_text(encoding="utf-8")[4:].split("\n---", 1)
        if MARKER in body:
            found[path.parent.name] = (yaml.safe_load(head), body)
    return found


class CodexPointerSkills(unittest.TestCase):
    def setUp(self):
        self.pointers = pointers()

    def test_every_workflow_has_a_pointer(self):
        commands = {p.stem for p in (ROOT / ".claude" / "commands").glob("*.md")}
        for name in sorted((commands - NO_POINTER) | ALSO_REQUIRED):
            self.assertIn(name, self.pointers, name)

    def test_name_matches_directory_and_description_stays_short(self):
        for directory, (meta, _) in self.pointers.items():
            self.assertEqual(directory, meta["name"])
            # Codex puts every skill description in context each session.
            self.assertLessEqual(len(str(meta["description"]).split()), 30, directory)

    def test_the_spec_a_pointer_names_exists(self):
        for directory, (_, body) in self.pointers.items():
            spec = re.search(r"`(\.claude/(?:commands|skills)/[^`]+\.md)`", body)
            self.assertIsNotNone(spec, directory)
            self.assertTrue((ROOT / spec.group(1)).is_file(), spec.group(1))

    def test_no_pointer_looks_like_a_job_portal(self):
        for directory in self.pointers:
            self.assertFalse(directory.endswith("-search"), directory)

    def test_agents_md_fits_the_codex_project_doc_cap(self):
        self.assertLess((ROOT / "AGENTS.md").stat().st_size, 32 * 1024)


if __name__ == "__main__":
    unittest.main()
