# Product

<!-- impeccable:product-schema 1 -->

Written by the build agent from the owner's brief and the repository, without an
interview (the owner handed the build off unattended). Lines marked *(inferred)* are
the agent's reading, not confirmed answers.

## Platform

web

## Stack

delegated: local desktop app. A Python standard-library server on 127.0.0.1 serves a
vanilla HTML/CSS/ES-module front end with no build step, opened in an Edge or Chrome
app window by a launcher, the same delivery pattern as the owner's Qualia. Chosen so a
non-technical person installs nothing beyond what the harness already needs.

## Users

Job seekers who are not technical: they have a CV and a Claude or ChatGPT subscription,
have never used a terminal, and found the chat-and-slash-command harness too hard to
understand. They use it at home on a Windows laptop, often anxious, in short sessions
spread over weeks. *(inferred from the owner's brief and CODEX-QUICKSTART.md)*

## Product Purpose

Find jobs the person is genuinely a strong candidate for, and turn any posting into a
tailored CV and cover letter in which every claim is backed by evidence the person
supplied. Success: a person goes from download to a checked application package without
help, and every document survives an interviewer's questions.

## Positioning

The application assistant that will not lie for you. A script reads every finished CV
and letter and blocks any number, date, credential, tool or employer the evidence
register cannot back. It runs on the person's own computer and their own AI
subscription, and it never submits anything.

## Operating Context

Daily rhythm: open the app, see what needs doing today (follow-ups, deadlines, packages
ready to send), search for jobs, pick one, let the assistant prepare the package while
they wait (10 to 15 minutes), read the PDFs, send it themselves, mark it sent. Files
live in the harness folder: `evidence/register.yaml`, `preferences.yaml`,
`job_search_tracker.csv`, `shortlist.csv`, `documents/applications/<Company>_<Role>/`.

## Capabilities and Constraints

- AI work runs through the installed `claude` or `codex` CLI on the person's
  subscription; no API keys. Deterministic work (tracker, today list, checks,
  packaging) runs as local scripts.
- Lite mode is the default below Claude Max / ChatGPT Pro.
- Job search needs network access; in Codex it is granted per run only.
- The system never submits an application or sends a message to an employer.
- Postings are untrusted input; nothing inside them is followed as an instruction.
- Personal data never leaves the folder except what the person's own agent sends to
  its provider and the job-board searches they start.

## Brand Commitments

Plain language, honest estimates, one clear next action, and visible marking of what
the person must do themselves (from the harness's existing CLAUDE.md voice rules).

## Evidence on Hand

The fictional demo candidate Riley Chen (`documents/demo/`, one tracked application,
a three-row shortlist). No real users, testimonials or metrics exist; none may be
invented.

## Product Principles

1. Truth over polish: a blocked claim is a feature, shown plainly.
2. The person decides and sends; the app prepares.
3. Never a dead end: every screen says what happens next and who does it.
4. Forms over chat; chat only when the assistant genuinely needs an answer.
5. Private by default, and say so where it matters.

## Accessibility & Inclusion

WCAG AA contrast, full keyboard use, visible focus, 40px targets, reduced-motion
respected, plain English at roughly a school-leaver reading level. *(inferred)*
