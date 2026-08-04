# J — Licensing & Attribution

## J.1 Checklist per bundled/derived component

| Component | Licence (verified) | Relationship | Obligations met by |
|---|---|---|---|
| ai-job-search (MadsLorentzen) | MIT (LICENSE in repo, 2026-08-03) | fork-derivative; git history retained | LICENSE kept; NOTICE credits; README attribution front-and-center; never presented as original |
| Ponytail (DietrichGebert) | MIT | installed plugin, not bundled | NOTICE credits; install commands documented |
| Caveman (JuliusBrussee) | MIT (verify LICENSE file at P0 install — noted UNVERIFIED until then) | installed plugin, not bundled | NOTICE credits; verify licence file during P0, stop if not MIT-compatible (handoff §4 stopping condition) |
| Humanizer (blader) | MIT (LICENSE inspected in installed plugin 2.9.1) | **vendored** SKILL.md | LICENSE copy alongside vendored skill + provenance header + NOTICE credits |
| openpyxl / pyyaml / pypdf | MIT / MIT / BSD-3 | pip dependencies | requirements.txt; standard use, no bundling |
| Raleway fonts (via upstream cover.cls OpenFonts) | OFL (ships with upstream) | inherited | upstream already complies; unchanged |
| Demo candidate content | original (this project) | ships | MIT like the repo |

## J.2 NOTICE.md text (draft, lands at P10)

```markdown
# NOTICE

Job Search Agent Harness is a fork-derivative of
**ai-job-search** by MadsLorentzen (https://github.com/MadsLorentzen/ai-job-search),
MIT licence. The apply pipeline (drafter/reviewer, PDF compile and inspection,
ATS text-layer checks), portal-CLI architecture, application archives, tracker,
template and portal registration commands, security guards, and test suites
originate there. This project would not exist without it.

Bundled or installed third-party components:
- **Humanizer** by blader (https://github.com/blader/humanizer), MIT —
  vendored skill (see .claude/skills/humanizer/LICENSE).
- **Ponytail** by DietrichGebert (https://github.com/DietrichGebert/ponytail),
  MIT — installed at setup as a development/runtime discipline plugin.
- **Caveman** by JuliusBrussee (https://github.com/JuliusBrussee/caveman),
  MIT — installed at setup for internal-channel compression.

Original contributions of this project (MIT):
Claude Code / Codex portability layer (RUNTIME-MAP.md, .codex adapters,
AGENTS.md completion) · cross-runtime session-continuity engine (state/,
HANDOFF, /continue, statusline telemetry mirror) · multimodal posting-intake
ladder · conversational preference engine with hard-constraint gating ·
location-aware portal expansion · usage-mode system with cost posture ·
evidence-vs-template separation with the deterministic truth tier
(evidence register + fact_check gate) · generated owner tracker workbook ·
onboarding flow · one-command setup/doctor · demo candidate · privacy guards
extension.
```

## J.3 Rules

- Attribution appears in README's first screen, not a footer.
- The private system's personal content is never referenced, quoted, or
  shipped; only sanitized mechanisms (doc 01 §12).
- Any new bundled asset at build time gets a row in J.1 before merging
  (licence conflict = stopping condition per handoff §4).
