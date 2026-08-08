# Build history

How this repository was designed and built. **Nothing here is needed to use the
harness** — it is kept because the reasoning behind several non-obvious
decisions lives in it, and because the test matrix records what was and was not
verified.

If you are looking for how to *use* the system, you want
[USER-GUIDE.md](../../USER-GUIDE.md).

| File | What it is |
|---|---|
| `BUILD-STATE.md` | The build ledger: every phase, its gate, the 40-test results table, and the written waivers |
| `IMPLEMENTATION-PLAN.md` | The contract the build followed |
| `plan-A` … `plan-N` | Design deliverables: system audit, capability audit, reuse matrix, repo structure, state model, runtime map, phases, file responsibilities, pinning, licensing, test matrix, install test, e2e list, simplification audit |
| `PLAN-STATE.md`, `OPUS-KICKOFF.txt` | Planning-stage progress file and the build kickoff prompt |

If you are changing the code, the live authority on what may be edited is
**`docs/REVIEW-HANDOFF.md` §4 and §4.1**, not this folder.
`plan-D-repo-structure.md` was that authority and has gone stale; it is kept as
the record of the original plan and carries a banner saying so.

Still accurate and worth reading:

- **`plan-E-state-model.md`** — one owner per data family, and which files are
  views that can always be regenerated.
