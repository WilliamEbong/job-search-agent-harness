# L — Fresh-Install Test (demo candidate)

Run at P9 in a clean directory OUTSIDE this repo (and again by CI where
runnable without conversational steps). Simulates a stranger following the
README.

1. `git clone <repo> fresh-test && cd fresh-test`
2. `python setup.py` → expect: runtimes detected (claude, codex), prereq
   checks with honest results, plugin installs offered and verified, portal
   CLI deps installed, **doctor table** with no silent failures.
3. Copy `documents/demo/` inputs into `documents/` (simulating a user
   dropping career docs).
4. `claude` → `/setup` → onboarding builds `evidence/register.yaml` +
   `preferences.yaml` for the demo candidate (every fact carries `source:`);
   template choice = stock.
5. `/scrape --mode focused --board freehire` → ranked jobs + run-log row +
   cost-posture line printed before the run.
6. `apply <examples/example-posting.md>` → full package: quad-format files,
   archive folder with provenance, tracker row, XLSX regenerated;
   **fact gate ran and passed**; humanize step ran; ATS check passed.
7. Fabrication check (the doc 03 "planted fake" test): edit the demo draft to
   claim an unregistered credential → `/verify-facts` → **red line blocks
   delivery**; resolve by removing the claim; gate passes.
8. `continue` in a fresh session → resumes with nothing redone.
9. Repeat steps 4–6 on Codex via stubs (P8 lane).
10. `git status` shows NO personal/generated files trackable
    (gitignore + guards); `python harness/privacy_sweep.py` → zero hits.

Pass = all 10 steps complete with expected results; every deviation recorded
in BUILD-STATE with cause and fix (never a weakened check).
