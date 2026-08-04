# Humanizer — vendored third-party skill

`SKILL.md` and `LICENSE` in this directory are **not original work**. They are
vendored verbatim from an external project.

| | |
|---|---|
| Upstream | **humanizer** by blader — https://github.com/blader/humanizer |
| Version vendored | **2.9.1** |
| Licence | MIT — see `LICENSE` (Copyright (c) 2025 Siqi Chen) |
| Vendored on | 2026-08-04 |
| Source | the installed plugin's own distribution, copied unmodified |

## Why it is vendored rather than installed

The apply pipeline runs the humanizer on every application before final compile.
Making that a plugin install would mean the pipeline behaves differently
depending on whether an optional install succeeded — and it would fail silently,
producing text that reads like a language model wrote it, with nothing to show
that a step was skipped. Vendoring makes the dependency present by construction.

The licence permits it, and `NOTICE.md` credits it.

## Updating

Deliberate re-vendor only, never automatic:

1. Read the upstream release notes for behaviour changes.
2. Copy the new `SKILL.md` and `LICENSE` over these.
3. Update the version and date in this file.
4. Re-run an application end to end and check the fact gate still passes on the
   humanized text.

## How this harness uses it, and the two rules that bound it

The skill is invoked from `.claude/commands/apply-any.md` after revision and
before final compilation. Two constraints are imposed by this project, not by
the skill:

1. **It may never add a fact.** No name, number, date or claim may appear in the
   humanized text that was not already in the draft. The humanizer improves how
   something is said; it has no access to what may be said.
2. **Any wording change forces a re-ground.** Recompile, then re-run
   `/verify-facts` on the final text. Stylistic rewriting is precisely the
   operation that pushes a claim past its evidence — "supported" becomes "led",
   and it reads better, which is why it survives a human proofread.

On Codex, if `@`-invocation of the skill is unavailable, the fallback is to
apply the skill's checklist inline, attributed — never to skip the step.
