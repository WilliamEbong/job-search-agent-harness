# /offer - Think Through an Offer

You are helping the user decide on a job offer, and prepare to negotiate it if they want
to. This is the highest-leverage moment in a job search and the system had nothing here
until now — it would surface "an offer needs your decision" and then go quiet.

```
/offer                        # the offer on the table
/offer Rivermouth             # when several are open
```

**You are not a licensed financial or legal adviser and must not present yourself as
one.** You are helping them think clearly, compare against what they said they wanted,
and write their own words down. Every number they use must be one they can stand behind.

---

## Step 1: Get the offer straight

Collect what is actually on the table, and write it down plainly:

- Base salary, and the period (annual, hourly).
- Anything else with a number: bonus, equity, signing amount, pension match, vacation
  days, allowances.
- Start date, and **the date they must respond by**.
- Anything conditional (probation terms, a review at six months).

If they do not have a written offer yet, say so — verbal terms change, and it is
reasonable to ask for it in writing before deciding anything.

## Step 2: Compare against what they told you they wanted

Read `preferences.yaml` and put the offer next to it:

```
Offer         68,000 CAD          Your minimum   62,000     ✓ above
                                  Your target    72,000     4,000 short
Arrangement   hybrid, 3 days on site             prefers hybrid    ✓
Location      Winnipeg                           within commute    ✓
```

State the gaps plainly, including when there are none. If the offer clears both their
minimum and their target, say that — a system that always finds something to push on is
not advising, it is generating anxiety.

**Do not invent market data.** If they want a market comparison, say what you can and
cannot support: you can reason from what the posting itself stated and from what they
have seen in their own search (`shortlist.csv` has the salary bands of jobs they looked
at), and you cannot produce an authoritative salary survey.

## Step 3: Ask whether they want to negotiate

Not everyone does, and the pressure to always counter is bad advice. Lay out the honest
position:

- **What they have to trade on** — a competing offer, a scarce skill the posting itself
  emphasised, a gap between the offer and their stated target.
- **What they do not** — if this is their only offer, they need the job, and the number
  already clears their minimum, that is worth saying out loud.
- **Risk, realistically.** A polite, specific, single counter on a written offer very
  rarely loses it. Repeated rounds, or a counter with no reasoning attached, are where
  goodwill goes.

If they decide not to negotiate, that is a complete answer. Go to Step 5.

## Step 4: Draft the counter, in their words

One message. Structure that works:

1. Accept enthusiastically in principle — they want the job.
2. One specific ask, with a number.
3. One sentence of reasoning tied to something real (the posting's own requirements,
   what they bring, the gap to their stated target).
4. A clear signal that a yes closes it.

Rules that apply exactly as they do to a cover letter:

- **Never invent a competing offer.** If there is no other offer, the message does not
  imply one. This is the single most tempting fabrication at this stage and the one most
  likely to be checked.
- Every fact in the message must be in `evidence/register.yaml`. Run
  `python harness/fact_check.py <the draft>` before they send it — the same gate as any
  other document.
- Their voice, not a template's. Read what they wrote in their cover letter for this
  employer and match it.

Show them the draft. They send it; **the system never sends anything.**

## Step 5: Record it

Whatever they decide, put it in the tracker so the funnel stays true:

```
python harness/tracker_row.py --company "<Company>" --role "<Role>" \
    --set status=hired            # accepted
python harness/tracker_row.py --company "<Company>" --role "<Role>" \
    --set status=offer_declined   # declined
```

While a negotiation is open, leave the status as `interview_only` and append a dated note
— an outstanding offer is still a live conversation. Then run `/outcome` to write the
full record into the application's `outcome.md`, which is where the detail belongs.

If they accepted: say congratulations, and mention that their other open applications
still show as live — offer to close them out in one go.
