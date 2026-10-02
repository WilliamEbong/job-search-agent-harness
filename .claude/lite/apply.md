# /lite apply - steps (read by `.claude/commands/lite.md`)

1. **Posting.** A number: `python harness/lite_search.py --save <#>` fetches and archives
   it and prints folder, slug, company, role and the text: skip step 2. Exit 1: fetch the
   URL it names instead. A URL: one fetch. Text or file: as given. Blocked or thin: ask
   for a paste [you].
2. **Archive** (URL, text or file only). Write `state/lite-apply.json`:
   `{"company": "...", "role": "...", "url": "...", "location": "...", "channel": "...", "deadline": "YYYY-MM-DD or empty"}`,
   then `python harness/lite_search.py --start` prints folder `<F>` and `<slug>`. Write
   `<F>/job_posting.md` (header + full posting, never a pointer) and `<F>/provenance.md`
   (date, input, source, URL, `posting_state: verified | unverified`).
3. **Gate.** `exclusions`, `hard_skips` (merely preferred skills never block),
   location/commute, work authorization. Fail:
   `python harness/lite_search.py --verdict gate-fail --rationale '<rule broken>'`; stop.
   Stated pay below `compensation.minimum`: both numbers, user decides [you]; no minimum
   set: say pay was not checked. Closing date passed: say so, user decides [you].
4. **Keywords.** `cv/main_<slug>.keywords.txt`, posting's exact words, one per line:
   `required: term | synonym` or `preferred: term`. Baseline:
   `python harness/ats_check.py --cv cv/main_example.tex --posting <F>/job_posting.md --keywords cv/main_<slug>.keywords.txt --brief`.
5. **Fit.** 0-100, register vs posting (`evidence/register.yaml`, once per session), 3
   lines: best match, main gap, verdict. 80+: draft. 60-79: ask [you]. <60 or no draft:
   `python harness/lite_search.py --verdict not-drafted --score <n> --rationale '<why>'`;
   stop.
6. **Draft.** Read `cv/main_example.tex` and `cover_letters/cover_example.tex` once per
   session; write `cv/main_<slug>.tex` and `cover_letters/cover_<slug>.tex` as new files
   from them. Change content only (profile, emphasis, order, posting's exact terms where
   true); cut to page target, never shrink fonts/margins. Letter: capability first,
   never a gap; plain verbs, no "leverage"/"passionate"; no em dashes, no padded
   triplets; company facts only from posting; never raise travel, salary, accommodation.
7. **Check.**
   `python harness/latex_build.py cv/main_<slug>.tex cover_letters/cover_<slug>.tex --pages <n>`:
   one line per PDF; act on each `fix:` and on a page count off target (cut content).
   Rebuild until clean, then one look at each PDF (rule 4). Then
   `python harness/ats_check.py --cv cv/main_<slug>.pdf --posting <F>/job_posting.md --keywords cv/main_<slug>.keywords.txt --brief`:
   synonym-only terms → posting's exact term where true; missing terms register
   supports → add; never one it does not. Rebuild, re-check once.
8. **Facts, package.**
   `python harness/fact_check.py cv/main_<slug>.tex cover_letters/cover_<slug>.tex --posting <F>/job_posting.md`
   must print OK; fix draft until it does. Any edit after step 7: redo 7, then 8. Then
   `python harness/lite_search.py --package --score <fit> --rationale '<one line>'`
   builds the package, tracker row and `qualified` shortlist row; non-zero exit: fix what
   it names, re-run.
9. **Report**, 12 lines max:

   ```
   <Company> - <Role>: fit <n>/100, <reason>
   ATS: <before>% -> <after>%; honest gaps: <terms or none>
   Fact gate: OK
   Package: <F>/
   ```
