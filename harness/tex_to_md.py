#!/usr/bin/env python3
"""Convert a generated moderncv CV or cover.cls letter into its Markdown mirror.

Every application ships in four formats: .tex, .pdf, .md and .docx. The .md is
the pandoc source for the .docx, so it has to say exactly what the .tex says.
Writing it by hand means two copies of the same prose drifting apart the first
time a fact is corrected in one and not the other — which is not hypothetical;
it happened in the system this was ported from.

    python harness/tex_to_md.py cv/main_acme_analyst.tex          > out.md
    python harness/tex_to_md.py cover_letters/cover_acme.tex      > out.md
    python harness/tex_to_md.py --self-check

Contact details come from `evidence/register.yaml`'s `meta:` block — the same
register that governs every other fact — so this script contains no personal
data and needs no editing to work for a different person.

Scope: the two stock templates this repo generates, nothing else. It is a text
transformer, not a LaTeX engine.

ponytail: regex transform over a known-regular generated template; if templates
ever diverge enough to break it, the fix is pandoc with a custom reader, not
more regexes.
"""

from __future__ import annotations

import os
import re
import sys

HARNESS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HARNESS_DIR)
REGISTER = os.path.join(ROOT, "evidence", "register.yaml")

# --- inline markup, applied to any body text ------------------------------
INLINE = [
    (r"\\textbf\{([^{}]*)\}", r"**\1**"),
    (r"\\textit\{([^{}]*)\}", r"*\1*"),
    (r"\\emph\{([^{}]*)\}", r"*\1*"),
    (r"\\mbox\{([^{}]*)\}", r"\1"),
    (r"\\href\{([^{}]*)\}\{([^{}]*)\}", r"\2: \1"),
    (r"\\url\{([^{}]*)\}", r"\1"),
    (r"\\%", "%"),
    (r"\\&", "&"),
    (r"\\_", "_"),
    (r"\\#", "#"),
    (r"\\\$", "$"),
    (r"~", " "),
    (r"--", "-"),  # en-dash source form; keeps the .md em-dash-free
]


def inline(text: str) -> str:
    # Macros nest: \textbf{Teams and \mbox{SharePoint}}. The {[^{}]*} patterns
    # cannot span an inner brace group, so a single pass leaves the OUTER macro
    # untouched. Repeat until stable: the inner one resolves first, after which
    # the outer matches. Bounded so a pattern that never converges cannot spin —
    # convert()'s assert catches whatever is left.
    for _ in range(5):
        before = text
        for pattern, replacement in INLINE:
            text = re.sub(pattern, replacement, text)
        if text == before:
            break
    return re.sub(r"[ \t]+", " ", text).strip()


def strip_comments(tex: str) -> str:
    # A % starts a comment unless escaped. Do this before anything else.
    return re.sub(r"(?<!\\)%.*$", "", tex, flags=re.M)


def convert_cv(body: str) -> list[str]:
    r"""moderncv: \section{X}, \cventry{dates}{title}{org}{loc}{}{...}, itemize."""
    out: list[str] = []
    for raw in body.split("\n"):
        line = raw.strip()
        if not line:
            out.append("")
            continue
        if line.startswith("\\section{"):
            out.append("")
            out.append("## " + inline(line[len("\\section{"):].rstrip("}")))
            out.append("")
            continue
        match = re.match(
            r"\\item\{?\\cventry\{([^{}]*)\}\{([^{}]*)\}\{([^{}]*)\}\{([^{}]*)\}", line
        )
        if match:
            dates, title, org, loc = (inline(g) for g in match.groups())
            out.append("")
            out.append("### " + title)
            out.append("")
            bits = [b for b in (org, loc) if b]
            out.append(
                "**" + bits[0] + "**"
                + (", " + bits[1] if len(bits) > 1 else "")
                + ". " + dates + "."
            )
            out.append("")
            continue
        if line.startswith("\\item"):
            out.append("- " + inline(line[len("\\item"):]))
            continue
        if line.startswith("\\") or line in ("}}", "}", "{"):
            continue
        out.append(inline(line))
    return out


def convert_cover(body: str) -> list[str]:
    r"""cover.cls: \lettercontent{...} paragraphs, an itemize block, \closing/\signature."""
    out: list[str] = []
    for para in re.findall(r"\\lettercontent\{(.*?)\}\s*$", body, flags=re.S | re.M):
        out.append(inline(re.sub(r"\s+", " ", para)))
        out.append("")
    # The bullet block lives OUTSIDE \lettercontent (a template pitfall — see
    # docs/latex-gotchas.md), so pull it separately.
    items = re.findall(r"\\item\s+(.*?)(?=\\item|\\end\{itemize\})", body, flags=re.S)
    if items:
        bullets = ["- " + inline(re.sub(r"\s+", " ", i)) for i in items]
        # Insert after the paragraph that introduces them (the one ending in ':').
        idx = next((n for n, line in enumerate(out) if line.endswith(":")), len(out) - 1)
        out = out[: idx + 2] + bullets + [""] + out[idx + 2:]
    match = re.search(r"\\closing\{([^{}]*)\}", body)
    if match:
        out.append(inline(match.group(1)))
        out.append("")
    match = re.search(r"\\signature\{([^{}]*)\}", body)
    if match:
        out.append(inline(match.group(1)))
    return out


def contact_block(register_path: str = REGISTER) -> list[str]:
    """Build the Markdown contact header from the register's `meta:` block.

    Deliberately not hardcoded. The version this was ported from carried the
    author's real name, phone number and profile URLs as a module constant,
    which is both a privacy problem and the reason it only ever worked for one
    person.
    """
    try:
        import yaml
    except ImportError:
        sys.exit("tex_to_md: PyYAML is required. Run: pip install -r requirements.txt")
    if not os.path.exists(register_path):
        sys.exit(
            f"tex_to_md: no evidence register at {register_path}. "
            "Run /setup-harness first — the Markdown mirror takes its contact "
            "details from the register so they cannot disagree with the CV."
        )
    with open(register_path, encoding="utf-8") as handle:
        meta = (yaml.safe_load(handle) or {}).get("meta", {}) or {}

    lines = [f"# {meta.get('owner', '')}".rstrip(), ""]
    if meta.get("location"):
        lines += [str(meta["location"]), ""]
    contact = " | ".join(
        str(meta[key]) for key in ("phone", "email") if meta.get(key)
    )
    if contact:
        lines += [contact, ""]
    links = meta.get("links", {}) or {}
    rendered = " | ".join(
        f"{label.capitalize()}: {url}" for label, url in links.items() if url
    )
    if rendered:
        lines += [rendered, ""]
    return lines


def convert(path: str, register_path: str = REGISTER) -> str:
    with open(path, encoding="utf-8") as handle:
        tex = strip_comments(handle.read())
    is_cover = "\\lettercontent" in tex
    match = re.search(r"\\begin\{document\}(.*?)\\end\{document\}", tex, flags=re.S)
    body = match.group(1) if match else tex

    contact = contact_block(register_path)
    if is_cover:
        # The letter head is name + one contact line, not the full block.
        head = contact[:2] + [line for line in contact[2:6] if "|" in line] + [""]
        lines = head + convert_cover(body)
    else:
        body = body.split("\\makecvtitle", 1)[-1]
        lines = contact + convert_cv(body)

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    assert "\\" not in text, "unconverted LaTeX macro left in output"
    assert "\u2014" not in text, "em dash leaked into the .md mirror"
    return text


def _convert_snippet(tex_text: str, register_path: str) -> str:
    """Convert an in-memory snippet; used by the self-check only."""
    import tempfile

    handle, path = tempfile.mkstemp(suffix=".tex")
    with os.fdopen(handle, "w", encoding="utf-8") as fh:
        fh.write(tex_text)
    try:
        return convert(path, register_path)
    finally:
        os.remove(path)


def self_check() -> None:
    """One runnable check covering every transform this file performs."""
    register = os.path.join(ROOT, "evidence", "register.example.yaml")

    cv = r"""
\begin{document}\makecvtitle
Profile line with \textbf{bold} and 20\% and a \mbox{Word}.
\section{Core Competencies}
\item \textbf{Label}: value here.
\item{\cventry{Aug 2020--Sep 2022}{The Title}{The Org}{Somewhere, MB}{}{
\item Did a thing.
}}
\end{document}"""
    out = _convert_snippet(cv, register)
    assert "## Core Competencies" in out, out
    assert "- **Label**: value here." in out, out
    assert "### The Title" in out, out
    assert "**The Org**, Somewhere, MB. Aug 2020-Sep 2022." in out, out
    assert "20%" in out, out
    assert "Word" in out, out
    # Contact comes from the register, not from a constant in this file.
    assert "Riley Chen" in out, out
    assert "riley.chen@example.com" in out, out

    # REGRESSION: nested macros. \textbf{...\mbox{X}} left the outer \textbf
    # unconverted on a single pass and tripped convert()'s assert on a real CV.
    nested = r"""
\begin{document}\makecvtitle
\item \textbf{Office 365, Teams and \mbox{SharePoint}}, with Excel in daily use.
\end{document}"""
    out = _convert_snippet(nested, register)
    assert "**Office 365, Teams and SharePoint**" in out, out

    cover = r"""
\begin{document}
\lettercontent{Dear Team,}
\lettercontent{Here is how it maps:}
\begin{itemize}
    \item \textbf{One:} first point.
    \item \textbf{Two:} second point.
\end{itemize}
\lettercontent{Closing thought.}
\closing{Kind regards,}
\signature{Riley Chen}
\end{document}"""
    out = _convert_snippet(cover, register)
    assert "Dear Team," in out, out
    assert "- **One:** first point." in out, out
    assert "- **Two:** second point." in out, out
    assert "Kind regards," in out and out.rstrip().endswith("Riley Chen"), out

    print("tex_to_md self-check: OK")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        # Without this, `--help` fell into the read-a-file branch below and
        # died with FileNotFoundError: '--help'.
        sys.exit(__doc__)
    if len(sys.argv) == 2 and sys.argv[1] == "--self-check":
        self_check()
    elif len(sys.argv) == 2:
        sys.stdout.write(convert(sys.argv[1]))
    elif len(sys.argv) == 4 and sys.argv[2] == "--register":
        # Lets a caller (and the tests) mirror against a named register rather
        # than only the one at the repo root.
        sys.stdout.write(convert(sys.argv[1], sys.argv[3]))
    else:
        sys.exit(__doc__)
