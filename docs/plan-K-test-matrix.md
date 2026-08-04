# K — Test Matrix Across Runtimes

Codex is installed (0.144.6) → **both lanes are live** (reconciliation R5;
doc 01 §14.1 static fallback not needed).

| Layer | What runs | Claude lane | Codex lane |
|---|---|---|---|
| Python unit (`tests/` upstream + `tests_harness/`) | pytest, runtime-independent | CI + local | same suite (runtime-independent — runs once) |
| Portal CLIs | `bun test` per CLI | CI + local | same (runtime-independent) |
| Lint/guards | lint_skills, harness_guards, privacy_sweep | CI | same |
| Onboarding E2E | demo docs → register + preferences + template | live | live (via stubs) |
| Apply E2E | fixture posting → full package (intake→gate→draft→review→humanize→re-ground→ATS→archive→track) | live, Agent-tool reviewer | live, sequential fresh-pass reviewer (RUNTIME-MAP §2) |
| Discovery E2E | focused/balanced/full caps, cost posture, closed-job rejection | live | live (spot: focused mode only — full matrix once; modes logic is shared markdown) |
| Tracker E2E | CSV → 4-tab workbook, archiver moves | live | runtime-independent script — runs once |
| Continuity | interrupted-session recovery; telemetry triggers | live (statusline mirror) | live (milestone cadence; no percentages) |
| Cross-runtime | Claude→Codex and Codex→Claude continuation of a mid-flight application | one drill each direction | ← same drill |
| Plugin installs | ponytail/caveman/humanizer presence + invocation | live | live (incl. humanizer `@`-invocation check — resolves its UNVERIFIED) |
| Fresh install | deliverable L script | live | live (setup detects codex, installs its lane) |

Waiver rule: any cell that cannot run gets an explicit reason in BUILD-STATE,
never a silent skip. Spot-check philosophy on Codex for runtime-independent
layers (they run once by definition); everything conversational runs live on
both.
