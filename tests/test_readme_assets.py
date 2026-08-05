"""Every local image referenced by README.md must exist in the repo.

A broken header image on the repo landing page is a silent, high-visibility
failure; this guard turns it into a red CI run instead.

Harness divergence (owner-approved, 2026-08-04): upstream also asserted the
README references *at least one* local image, which encoded its mascot header.
This repository removed the mascot deliberately — it is upstream's identity,
not this project's — and the owner chose a text-only README, so that assertion
is gone. The useful half, that any referenced image must exist, is unchanged.
This is the only edited upstream-owned file; see NOTICE.md.
"""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
README = REPO / "README.md"

IMG_SRC = re.compile(r'<img[^>]+src="([^"]+)"')
MD_IMG = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")


class ReadmeImageReferences(unittest.TestCase):
    def _local_refs(self):
        text = README.read_text(encoding="utf-8")
        refs = IMG_SRC.findall(text) + MD_IMG.findall(text)
        return [r for r in refs if not r.startswith(("http://", "https://"))]

    def test_all_local_image_references_resolve(self):
        for ref in self._local_refs():
            with self.subTest(ref=ref):
                self.assertTrue((REPO / ref).is_file(), f"README references missing file: {ref}")


if __name__ == "__main__":
    unittest.main()
