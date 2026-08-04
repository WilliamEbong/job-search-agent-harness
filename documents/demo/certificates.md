# Riley Chen — Credentials and Certificates

<!--
FICTIONAL. See documents/demo/cv_riley_chen.md.

This file exists to exercise one specific failure the harness must never allow:
an in-progress credential rendering as if it were earned. That is the
fabrication test in the owner's guide, and plan-M test 17.
-->

## Completed

### WHMIS 2015 — Workplace Hazardous Materials Information System
- Issuer: Government of Canada
- Completed: September 2020
- Context: Required before laboratory bench work at Northwind Analytical Services.
- Status: **completed** — may be claimed without qualification.

## In progress

### Google Data Analytics Professional Certificate
- Issuer: Google, delivered through Coursera
- Started: January 2026
- Status: **in progress** — roughly two thirds complete, no completion date set.
- Qualifier required: **"in progress"**

  This one matters. Written on a CV as "Google Data Analytics Professional
  Certificate" with no qualifier, it reads as earned — and Riley would have to
  defend that in an interview with nothing to show. The register records it with
  `status: in-progress` and `qualifier_required: in progress`, and
  `harness/fact_check.py` blocks any document that renders the name without the
  qualifier nearby.

  Acceptable renderings:
    - "Google Data Analytics Professional Certificate (in progress)"
    - "currently completing the Google Data Analytics Professional Certificate"

  Blocked rendering:
    - "Google Data Analytics Professional Certificate" listed under Credentials
      with no qualifier.

## Considered and not held

Listed here so onboarding does not have to ask twice, and so nothing on this list
is ever mistaken for a credential Riley holds:

- P.Eng — not an engineer, not pursuing.
- PMP — considered, not started.
- AWS certifications — none. Riley does not work in cloud infrastructure.
