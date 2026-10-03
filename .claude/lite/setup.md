# /lite setup - steps (read by `.claude/commands/lite.md`)

Register exists: skip steps 1 and 3's register; write only the missing `preferences.yaml`
keys below (always `usage.mode: lite`; ask only the step-2 questions not yet answered);
then step 4 unless active `target_positions` exist.

1. **CV [you]:** path or paste. Read once.
2. **One message, 5 numbered questions [you]**, default in brackets, "skip" keeps it:
   (1) where they can work and their work authorization: city, region, country, max
   commute [30 km], remote/hybrid/onsite [any]; (2) minimum pay, currency, salary or
   hourly [none: keep every posting]; (3) jobs, industries, shifts, travel refused
   [none]; (4) skills a job must not require, because they lack them [none]; (5) the one
   CV gap that most changes what may be claimed (unstated number, credential status,
   date, tool hands-on vs AI-assisted) [unclaimed].
3. **Write [me]:** `evidence/register.yaml`, shape of `evidence/register.example.yaml`
   (shape only: never copy its entries, names or dates), every entry with `source:` (CV path or
   `owner-confirmed <YYYY-MM-DD>`). `preferences.yaml`: keep every existing key, merging
   into existing mappings (`usage.plan` stays), and add:
   ```yaml
   location: {home: "City, Region, Country", commute_radius_km: 30, arrangements: [hybrid, remote, onsite]}
   work_authorization: {status: "...", sponsorship_required: false}
   compensation: {currency: "<CUR>", basis: salary, minimum: <amount>, missing_compensation: keep}  # only if a minimum was given
   exclusions: {occupations: [], industries: [], schedules: [], travel: {max_percent: 25}}
   hard_skips: [{skill: "...", mandatory_only: true, reason: "..."}]
   presentation: {cv_pages: 2}
   usage: {mode: lite}
   ```
   Fill placeholders left in `cv/main_example.tex` (`\name{[First]}{[Last]}`, contact,
   entries; remove sections the register cannot fill) and in
   `cover_letters/cover_example.tex` (header and `\signature`) from the register. Dates `2020-2024`, ASCII hyphen, never `--`. Warn: git
   tracks both files, never push them to a public fork.
4. **Recruiter pass:** follow `.claude/commands/recruiter.md`, judging from register, not
   files it cites in `.claude/skills/`; no plan line; why, `because` and `gap` 10 words
   max each; 20 or fewer, never padded. User strikes any [you]; save
   `target_positions`.
5. **Codex with network restricted only [you]:** search fails until allowed. One line
   each, user picks [1]: (1) approve each search when asked, nothing changes; (2) on
   for good, `[sandbox_workspace_write]` + `network_access = true` in
   `~/.codex/config.toml`, restart; every Codex shell command can then go online; you
   may edit it: back up, show diff, write on yes, never a second header; (3) one
   session, `codex -c sandbox_workspace_write.network_access=true`.
