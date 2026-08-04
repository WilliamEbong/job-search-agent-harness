# NOTICE

Job Search Agent Harness is a fork-derivative of
**ai-job-search** by MadsLorentzen (https://github.com/MadsLorentzen/ai-job-search),
MIT licence. The apply pipeline (drafter/reviewer, PDF compile and inspection,
ATS text-layer checks), portal-CLI architecture, application archives, tracker,
template and portal registration commands, security guards, and test suites
originate there. This project would not exist without it.

Bundled or installed third-party components:

- **Humanizer** by blader (https://github.com/blader/humanizer), MIT —
  vendored skill at version 2.9.1. See `.claude/skills/humanizer/LICENSE` and
  `.claude/skills/humanizer/PROVENANCE.md`.
- **Ponytail** by DietrichGebert (https://github.com/DietrichGebert/ponytail),
  MIT — installed at setup as a development/runtime discipline plugin.
- **Caveman** by JuliusBrussee (https://github.com/JuliusBrussee/caveman),
  MIT — offered at setup (optional) for internal-channel compression.

Python dependencies, used normally and not bundled: PyYAML (MIT), openpyxl
(MIT), pypdf (BSD-3-Clause). The Raleway fonts shipped with upstream's cover
letter class are under the SIL Open Font Licence and are inherited unchanged.

## Original contributions of this project (MIT)

- Claude Code / Codex portability layer — `RUNTIME-MAP.md`, `.codex/` adapters,
  the `AGENTS.md` harness block.
- Cross-runtime session-continuity engine — `state/`, the HANDOFF format,
  `/continue`, and the statusline telemetry mirror.
- Deterministic truth tier — the evidence register schema and
  `harness/fact_check.py`, generalized so its lexicon and positioning-constraint
  patterns are configuration rather than code, and a constraint family runs only
  when a user's own register declares it.
- Multimodal posting-intake ladder with provenance and `unverified` marking.
- Conversational preference engine with hard-constraint gating, including the
  mandatory-versus-preferred distinction on skill skips.
- Companies-of-interest engine and company-page search.
- Five search scopes and the usage-mode system with cost posture.
- Location-aware portal expansion; the `jobbank-ca-search` portal CLI.
- Generated four-tab owner tracker workbook, the application archiver, and the
  shared folder matcher they both use.
- Quad-format application packaging and the drift-proof Markdown mirror.
- CV-first onboarding with in-command interview controls, and the career review.
- One-command `setup.py` installer and doctor.
- Fictional demo candidate, fixtures, and the privacy guards
  (`tools/harness_guards.py`, `harness/privacy_sweep.py`).

## On the boundary

Where this project reuses upstream's work, it reuses it in place rather than
reimplementing it: `/apply`, `/rank`, `/add-portal`, `/add-template`, `/outcome`,
`/interview`, the templates, the guards and the tests are upstream's files, run
unchanged. The harness adds wrappers and new files alongside them.

That is deliberate, and it is also the honest description: the hardest and most
valuable part of this system was written by someone else.
