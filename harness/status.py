#!/usr/bin/env python3
"""The one place that decides what an application's status means.

Three writers and two readers disagreed about this vocabulary, and every
disagreement was silent:

* `/outcome` (upstream) instructs writing `applied` → `interview` → `offer` →
  `hired`/`rejected`/`no response`/`offer declined`/`withdrawn`.
* `/apply-any` writes `in_progress`.
* `tracker_xlsx.py` recognised only six values; anything else counted as
  neither Open nor Closed, so those rows **vanished from the funnel** with no
  warning.
* `/html-report` (upstream) has no mapping for `in_progress` — the status
  `/apply-any` actually writes — and classifies `interview_only` as
  Rejected/Closed while the workbook counts it Open.

So the two dashboards disagreed with each other and both disagreed with the
writers. This module ends that: writers emit canonical values, readers
normalise on the way in, and unknown values still classify sensibly rather than
falling into a hole.

The upstream command files are never edited (they must stay byte-identical for
clean tag merges), so this is the harness-side fix: normalise on read.
"""

from __future__ import annotations

# The canonical six. These are upstream's own `documents/README.md` vocabulary
# and what `tracker_xlsx.py` has always coloured and counted.
IN_PROGRESS = "in_progress"
INTERVIEW_ONLY = "interview_only"
HIRED = "hired"
OFFER_DECLINED = "offer_declined"
REJECTED = "rejected"
NO_RESPONSE = "no_response"
# Kept as itself rather than force-mapped. A candidate who withdrew was not
# rejected; collapsing the two would quietly corrupt the funnel it feeds.
WITHDRAWN = "withdrawn"

CANONICAL = frozenset({IN_PROGRESS, INTERVIEW_ONLY, HIRED, OFFER_DECLINED,
                       REJECTED, NO_RESPONSE, WITHDRAWN})

# Everything the other writers actually emit, mapped onto the canonical set.
SYNONYMS = {
    "applied": IN_PROGRESS,
    "in progress": IN_PROGRESS,
    "active": IN_PROGRESS,
    "drafted": IN_PROGRESS,
    "interview": INTERVIEW_ONLY,
    "interviewing": INTERVIEW_ONLY,
    "interview only": INTERVIEW_ONLY,
    # An outstanding offer is still a live conversation, so it is open. The
    # distinction from interview_only is carried in the notes, not the status.
    "offer": INTERVIEW_ONLY,
    "offer received": INTERVIEW_ONLY,
    "no response": NO_RESPONSE,
    "no reply": NO_RESPONSE,
    "ghosted": NO_RESPONSE,
    "offer declined": OFFER_DECLINED,
    "declined": OFFER_DECLINED,
    "accepted": HIRED,
    "withdrew": WITHDRAWN,
}

# Days of silence before a follow-up is due. One number, shared by the
# workbook and the daily brief — they used to hold two literals and a comment
# claiming they were consolidated.
FOLLOWUP_DAYS = 10

# Live conversations. A folder whose row is open must never be archived.
OPEN = frozenset({IN_PROGRESS, INTERVIEW_ONLY})
CLOSED = frozenset({HIRED, OFFER_DECLINED, REJECTED, NO_RESPONSE, WITHDRAWN})
# The employer replied at all — the denominator question a funnel answers.
RESPONDED = frozenset({HIRED, OFFER_DECLINED, REJECTED, INTERVIEW_ONLY})
REACHED_INTERVIEW = frozenset({INTERVIEW_ONLY, HIRED, OFFER_DECLINED})


def normalize(value: str | None) -> str:
    """Map any writer's status onto the canonical vocabulary.

    An unrecognised value is returned lowercased and underscored rather than
    dropped, so a new status shows up in the workbook as itself instead of
    disappearing. `is_open()` treats unknowns as open — see why there.
    """
    text = (value or "").strip().lower()
    if not text:
        return ""
    if text in CANONICAL:
        return text
    if text in SYNONYMS:
        return SYNONYMS[text]
    underscored = text.replace(" ", "_").replace("-", "_")
    if underscored in CANONICAL:
        return underscored
    return SYNONYMS.get(underscored, underscored)


def is_open(value: str | None) -> bool:
    """Is this application still a live conversation?

    Unknown statuses count as OPEN. This is the safe direction: `is_open` gates
    whether the archiver may delete a folder, and mistakenly keeping a finished
    application costs disk space, while mistakenly deleting a live one destroys
    the documents `/interview` prepares from.
    """
    status = normalize(value)
    if not status:
        return False
    return status not in CLOSED


def is_closed(value: str | None) -> bool:
    return normalize(value) in CLOSED


def responded(value: str | None) -> bool:
    return normalize(value) in RESPONDED


def reached_interview(value: str | None) -> bool:
    return normalize(value) in REACHED_INTERVIEW


def demo() -> None:
    """Runnable check: the disagreements that motivated this module."""
    # /outcome's vocabulary lands in the right buckets.
    assert normalize("applied") == IN_PROGRESS
    assert normalize("interview") == INTERVIEW_ONLY
    assert normalize("no response") == NO_RESPONSE
    assert normalize("offer declined") == OFFER_DECLINED
    # /apply-any's value is already canonical.
    assert normalize("in_progress") == IN_PROGRESS
    # An `applied` row used to count as neither Open nor Closed.
    assert is_open("applied") and not is_closed("applied")
    # interview_only is open, contradicting html-report's Rejected/Closed bucket.
    assert is_open("interview_only")
    assert responded("interview_only")
    # withdrawn stays itself and is closed, but is NOT a rejection.
    assert normalize("withdrawn") == WITHDRAWN
    assert is_closed("withdrawn") and not responded("withdrawn")
    # Unknown statuses are kept and treated as open (safe for the archiver).
    assert normalize("awaiting_panel") == "awaiting_panel"
    assert is_open("awaiting_panel")
    # Blank is neither.
    assert not is_open("") and not is_closed("")
    # Reaching interview is not the same as merely responding: a rejection is a
    # response, and an interview that ended in one still counts as reached.
    assert reached_interview("interview_only") and reached_interview("hired")
    assert not reached_interview("rejected") and not reached_interview("no_response")
    print("status: OK")


if __name__ == "__main__":
    demo()
