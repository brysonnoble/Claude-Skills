# Job Application Tracker — [Name]

Prefer this as a plain local CSV (see the skill's "Where things are stored"
section) over a hosted doc/Sheet whenever the run has real file-system
access — it's faster to read and edit reliably at scale, and needs no
browser automation to update.

## Columns
`Date Added, Company, Role, Location / Remote, Status, Notes, Link`

## Status vocabulary (fixed — don't invent new values)
- `shortlisted` — found and ranked, not yet filled
- `filled-pending-review` — form filled, stopped before submit, waiting on
  the user
- `submitted` — actually submitted (by the user, or by an explicit
  auto-submit instruction); verify against real confirmation (e.g. an email)
  before trusting this status for another run's decisions, per the skill's
  Phase 2 verification step
- `skipped-needs-manual` — blocked on something only the user can resolve
  (most commonly: needs an account created on a new portal — name the exact
  company and portal in Notes; also covers a CAPTCHA or anything else that
  stopped autofill partway through)
- `not-a-fit` — evaluated and rejected on merits (title, seniority,
  dealbreaker)
- `excluded-location` — rejected specifically for falling outside the
  location hard rule
- `link-invalid` — the listing URL no longer resolves to a live posting

## Notes column conventions
- The user may write directly in this column between runs — corrections,
  "I already applied to this myself," "don't contact this one again," etc.
  A future run must treat anything here as an instruction that overrides
  its own prior assumptions for that row, and must append rather than
  overwrite when adding its own notes.
- When a row is `skipped-needs-manual` because of an account wall, the note
  should name the company and the portal/platform specifically (e.g.
  "Blocked — needs a Workday account for Acme Corp to continue") so the
  user knows exactly which accounts to go create, and so a future run can
  match and revisit the right open tab once they have.

## Example rows

```csv
Date Added,Company,Role,Location / Remote,Status,Notes,Link
2026-08-13,Acme Corp,Software Engineer I,Remote (US),skipped-needs-manual,"Blocked — needs a Workday account for Acme Corp to continue",https://acme.example.com/careers/12345
2026-08-13,Waymark,New Grad SWE,"Tampa, FL",filled-pending-review,"Left desired-salary field blank — logged in open-questions.md",https://boards.greenhouse.io/waymark/jobs/6789
2026-08-14,Beta Inc,Junior Developer,"Sarasota, FL",submitted,"Confirmed via email from careers@beta.example.com, 'Thanks for applying', received Aug 14",https://beta.example.com/jobs/456
```
