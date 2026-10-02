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
   (its entries fictional), every entry with `source:` (CV path or
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
   entries) and in the header of `cover_letters/cover_example.tex` (name, email, phone,
   links) from the register. Dates `2020-2024`, ASCII hyphen, never `--`. Warn: git
   tracks both files, never push them to a public fork.
4. **Recruiter pass:** follow `.claude/commands/recruiter.md`, judging from register, not
   files it cites in `.claude/skills/`; `because` and `gap` 10 words max each. Show 20,
   user strikes any [you], save `target_positions`.
