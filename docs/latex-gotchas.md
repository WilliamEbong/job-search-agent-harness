# LaTeX gotchas

Compile failures and layout defects that cost real time in live use, with the fix that
actually works. Ported from operational notes; each entry is here because it happened,
not because it might.

The meta-lesson, which is worth more than any single entry: **"it looks right in the
`.tex`" is not evidence.** LaTeX page-break decisions are not predictable from the
source. Compile it, open the PDF, and look.

---

## Compilation

### Use lualatex for the CV and xelatex for the cover letter

Not interchangeable.

- **CV → `lualatex`.** `pdflatex` fails on modern MiKTeX with font-expansion errors from
  `fontawesome5`. The error text points at font metrics and reads like a missing package;
  it is not.
- **Cover letter → `xelatex`.** `cover.cls` needs `fontspec`, which `pdflatex` cannot
  provide.

If a custom template is registered via `/add-template`, use the compile command that
template declares instead.

### Compile from the template's own directory

`cover.cls` resolves its bundled Raleway fonts **relative to the current working
directory**. Compiling from the repository root produces a font-not-found error that
looks like a broken TeX installation and is not.

```
cd cover_letters && xelatex -interaction=nonstopmode -halt-on-error cover_<slug>.tex
```

Use `-output-directory` to keep `.aux`/`.log` litter out of the source tree; the working
directory still has to be the template's.

### First compile on a fresh MiKTeX is slow and may look hung

MiKTeX downloads packages on demand. The first `lualatex` run against the stock CV can
take minutes and produce no output while it fetches. That is not a hang. `harness_setup.py`'s
doctor allows a long timeout for exactly this reason and reports a timeout honestly
rather than as a compile failure.

### Read the log, not just the exit code

A run can exit 0 and still have produced a broken document. Grep the log for lines
starting with `!` — upstream's CI does this, and so should any local check.

---

## Layout

### `\needspace` before every `\cventry`

Without it, a job title lands at the bottom of a page with its bullets on the next one.
Nothing errors; the PDF is simply embarrassing.

```latex
\needspace{5\baselineskip}
\cventry{...}{...}{...}{...}{}{...}
```

### `\enlargethispage` to rescue a section that *just* spills

When a trailing section pushes two lines onto a third page:

```latex
\enlargethispage{3\baselineskip}
```

Use it to rescue a near-miss, not to compress a genuinely three-page CV into two. If the
content does not fit, cut content.

### Exact page counts are a requirement, not a preference

The CV is exactly 2 pages; the cover letter is exactly 1. Verify with `pdfinfo` or
upstream's `tools/verify_pdf.py --pages`, and iterate until it is true. A cover letter
whose signature block has slipped onto page 2 is the single most common defect in this
pipeline.

---

## The cover-letter bullet trap

This one is worth reading carefully, because both obvious fixes are wrong.

`\lettercontent{}` **cannot wrap** an `itemize` block: the command's trailing `\\` errors
on `\end{itemize}`. The obvious response — move the list outside `\lettercontent{}` —
compiles, and silently loses the Raleway font, so the bullets render in a different
typeface from the body. It looks like a design choice. It is a bug.

The pattern that works: close `\lettercontent{}`, then wrap the list with the font
re-applied explicitly.

```latex
\lettercontent{Here is how my experience maps to your requirements:}

{\raggedright\fontspec[Path = OpenFonts/fonts/raleway/]{Raleway-Medium}%
\fontsize{11pt}{13pt}\selectfont
\begin{itemize}
  \item \textbf{Label:} the point.
\end{itemize}\par}
```

Consequence for the Markdown mirror: `harness/tex_to_md.py` extracts bullets separately
from `\lettercontent` paragraphs precisely because they live outside it, and re-inserts
them after the paragraph that introduces them.

---

## Escaping and content

### `\%` for every literal percent

`20\%` renders as "20%". A bare `%` starts a comment and silently eats the rest of the
line — including, on one occasion, the remainder of a bullet about a metric. The fact
checker folds `20 %`, `20%` and `20 percent` onto the same claim, so the escaped form
costs nothing.

### `\mbox{}` to stop an awkward break

Keeps a short token from being split or stranded:

```latex
Microsoft 365, Teams and \mbox{SharePoint}
```

Note for the Markdown mirror: nested macros like `\textbf{... \mbox{X}}` need more than
one pass to unwrap, because the inner braces block the outer pattern. `tex_to_md.py`
loops until stable and asserts nothing is left — a regression test pins it.

### Placeholder tokens must not reach a compiled document

`@@KEY@@`-style placeholders and `[YOUR_NAME]` compile perfectly happily and are visible
in the PDF. Upstream's CI checks the shipped templates still contain their placeholders
(proving no personal data was committed); the opposite check matters for generated
documents. Read the compiled PDF.

---

## Before presenting any package

1. Compiled with the right engine, from the right directory, log free of `!` lines.
2. CV exactly 2 pages; cover letter exactly 1.
3. No `\cventry` title orphaned at a page foot.
4. Cover-letter bullets in the body font.
5. Text layer extracts cleanly: `pdftotext -layout`, no `(cid:NN)` markers, email and
   phone present as literal text, reading order matching the visual order.
6. `/verify-facts` green **on the final text**, after any humanizer edit.
