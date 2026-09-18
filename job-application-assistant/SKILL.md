# Job Application Assistant

This skill turns a resume and a short set of criteria into a repeatable job
search: find listings that fit, keep a log so nothing is searched or applied
to twice, and optionally fill out (but not necessarily submit) application
forms in the user's browser. It is meant to be installed by different
people, so treat every person's resume, criteria, and application history as
private to them — never copy another user's data into this skill file
itself.

The workflow has three phases. Figure out which one the user is in before
doing anything else:

1. **First-time setup** — no criteria doc exists yet, or the user is asking
   to get started.
2. **A search/apply run** — criteria doc exists; the user wants matches, a
   digest, or forms filled out.
3. **Scheduling** — the user wants this to happen automatically on a
   cadence, without them asking each time.

## Where things are stored

Two durable documents make this workflow repeatable instead of a one-off:

- **The criteria doc** (`references/context-doc-template.md` is the
  template) — the user's target roles, locations, salary floor, dealbreakers,
  EEO/work-authorization/self-ID answers used for autofill, and their default
  preference for auto-submitting applications.
- **The application tracker** (`references/application-log-template.md` is
  the template) — every listing seen or applied to, with a small fixed
  status vocabulary, so a scheduled run never re-surfaces or re-applies to
  the same job and always knows what's still open.

**Prefer a plain local file (CSV) over a hosted doc for the tracker whenever
the run has real file-system access** — a Project's working directory, or a
folder on the user's own computer reached through the device bridge. A
CSV is fast to read and edit with the Read/Edit tools, has no per-request
size ceiling, and needs no browser automation to update. Hosted docs (a
claude.ai Project doc, a Google Sheet) are the fallback only when there's no
local file access at all — e.g. a scheduled run with no device bridge and no
attached Project. This preference exists because large tables in a hosted
doc or Sheet routinely exceed tool output limits on read, and editing them
either requires slow, error-prone browser automation or a full rewrite each
time. Once a user has a working local tracker, don't propose moving it to a
hosted doc or Sheet — that's a regression, not an upgrade.

If neither a local file nor a Project is available, fall back to the working
directory and tell the user plainly that this data will not persist once the
session ends — offer to attach a Project, connect their computer, or have
them save the files somewhere durable.

Resumes are never fabricated or edited by this skill — only read for
matching and for autofilling forms.

## Phase 1: First-time setup

Run this the first time a user invokes the workflow, or whenever no criteria
doc is found.

1. **Get the resume.** Check for an already-uploaded resume (a Project file,
   or a file attached to the conversation). If none exists, ask the user to
   attach or upload one — PDF or docx both work. Read it to understand their
   experience, titles held, seniority, and skills; this context is what
   later steps rank listings against, so actually read it, don't skim the
   filename.

2. **Interview the user for the criteria doc.** Use `AskUserQuestion` (or,
   if unavailable, plain conversational questions) to gather the standard
   set below. Ask in a few batched questions rather than one at a time if
   using AskUserQuestion — it supports multiple questions per call. Cover:
   - Target job titles / roles (a few variants — people search different
     terms for the same role), and whether adjacent/stretch titles (e.g. the
     next level up) should be included if the user clearly meets the stated
     minimum qualifications.
   - **Location, as a structured hard rule, not a loose preference.** Ask
     separately for remote, hybrid, and onsite tolerances, since they're
     rarely the same distance — e.g. "fully remote: no limit," "hybrid:
     within N hours of [base location]," "onsite: within N hours of [base
     location]." Get an explicit list of which cities/metro areas count for
     the onsite/hybrid radius rather than leaving it to be inferred each
     run, and confirm whether the radius is a hard exclusion (never
     shortlist outside it, regardless of fit) or a soft preference.
   - Minimum acceptable salary (optional but improves filtering)
   - Industries or company types to include or explicitly avoid, and which
     should be weighted highest if there aren't enough top-choice listings
     to fill a run
   - Years of experience to represent (usually inferable from the resume,
     confirm rather than re-derive from scratch)
   - Work authorization / sponsorship needs, if relevant to the user
   - **EEO / voluntary self-identification answers**, if the user wants
     these autofilled rather than left blank on every form: citizenship/work
     authorization status, security clearance held (if any), disability
     status, veteran status, race/ethnicity/gender if the user chooses to
     share them for self-ID questions. Make clear this is optional and only
     used to answer forms that ask — never inferred or guessed if the user
     doesn't provide it.
   - Dealbreakers (anything that should auto-exclude a listing)
   - Which sources to search: LinkedIn, Indeed, specific company career
     pages, or all of the above — and which of those the user is already
     signed into in their browser (this matters later for the
     accounts/credentials rule in Phase 2).
   - Default behavior when an application is ready: **stop and let the user
     review before submitting**, or **submit automatically**. Default to
     "stop and review" unless the user clearly asks for full automation —
     autofilled forms can contain a wrong guess, and a submitted application
     is hard to take back.

   Write the criteria doc as soon as the interview is done, following
   `references/context-doc-template.md`. Don't wait until every other setup
   step is finished to save it.

3. **Create an empty application tracker** from
   `references/application-log-template.md` so the first real run has
   somewhere to write. Prefer a local CSV per "Where things are stored"
   above.

4. **Confirm with the user** what was captured (a short summary, not a full
   reprint of the doc) and ask if anything needs correcting before the first
   real run.

## Phase 2: A search / apply run

1. **Load context.** Read the criteria doc, the application tracker, and (if
   not already in context) the resume.

2. **Pre-run pass over the tracker — do this before any new searching or
   filling.** The user may edit the tracker directly between runs (correct a
   status, leave a note, mark something "I already applied to this myself").
   Read every row, including the Notes column, and treat anything the user
   has written there as an instruction that overrides your own prior
   assumptions for that row — append new notes rather than deleting theirs.
   Never overwrite a row's existing content wholesale or revert a manual
   correction. Every listing URL already in the tracker is "seen" — don't
   re-search, re-shortlist, or re-fill it unless step 5 below gives a
   specific reason to revisit it.

3. **Verify status claims, don't just trust them.** For rows currently
   marked `submitted`, `filled-pending-review`, or `skipped-needs-manual`,
   check for real confirmation of that status before relying on it for
   another run's decisions — e.g. search the user's email (if a Gmail/email
   tool is available) for an actual confirmation message from that company
   referencing the role. If genuine confirmation is found, note the evidence
   in that row. If a row is already marked `submitted` by the user's own
   note or a prior run and no confirmation is found, don't flip the status
   back — append a note that confirmation wasn't found this run rather than
   overwriting what's there. Never mark something `submitted` purely by
   inference. If the verification source errors out or isn't connected, say
   so in the final report and skip verification for the run rather than
   guessing.

4. **Search.** For each configured source:
   - Prefer a plain web search (`WebSearch`/`WebFetch`) for discovery when
     possible — it doesn't require the user's browser or a logged-in
     session, which matters a lot for a *scheduled, unattended* run.
   - Use Chrome automation (load the `claude-in-chrome` skill first, then
     the `mcp__claude-in-chrome__*` tools) when a source needs a logged-in
     session to see full results or listing details — e.g., LinkedIn Jobs
     often does. This only works when the user's Chrome is connected, so it
     is not reliable inside an unattended scheduled run; note that limit to
     the user during setup rather than discovering it mid-run.
   - Company career pages: search or navigate directly, since these are
     usually public.

5. **Revisit tabs that were previously blocked, if Chrome is connected.**
   Before searching for anything new, check for open tabs matching
   `skipped-needs-manual` rows (match by URL). If the user has since signed
   in or created the account that blocked it, finish filling that
   application per step 7's rules and update its status. This is what
   closes the loop on the accounts/credentials rule below — a listing that
   was blocked isn't a dead end, it's a row that gets revisited every run
   until it's resolved.

6. **Filter and rank.** Drop anything already in the tracker (compare by
   listing URL or by company + title + posted date). Drop anything that
   fails a stated dealbreaker or falls outside the location hard rule. Rank
   what's left by fit against the resume — title match, seniority match,
   location/remote match, and any explicit must-haves. Don't just return
   everything that matched a keyword search; the value of this skill is the
   filtering.

7. **Present the results, or fill applications when asked.**
   - If this is an unattended/scheduled digest-only run, give the user a
     short ranked list — company, title, location, why it's a fit, link —
     and stop there.
   - When filling is in scope (the criteria doc's default, or an explicit
     instruction for this run): open each application in Chrome and fill
     every field using the resume and criteria doc as the source of truth,
     including any EEO/self-ID/clearance answers the user provided.
   - For free-text screening questions, answer truthfully from what's
     actually in the resume/criteria doc. If a question needs information
     the skill doesn't have (e.g., "why do you want to work here"), don't
     invent an answer — draft something clearly marked as a draft and flag
     it for the user to review, or leave it blank and say it needs their
     input.
   - Upload the resume file using the form's native file-upload control
     where one exists; don't paste resume text into a free-text box unless
     there's genuinely no upload control.
   - **Accounts/credentials — hard rule.** Never assume a listing needs an
     account before trying it — open the application and attempt to fill it
     first; plenty of "looks like it needs a login" listings don't. Never
     enter or store a password, and never click through an account
     creation/signup flow yourself. Only stop once you actually hit a wall
     that can't be gotten past with a session the user is already
     authenticated in. When that happens: fill everything accessible before
     the wall, leave the tab open, mark the row `skipped-needs-manual`, and
     name the exact company and portal in the notes (e.g. "Blocked — needs a
     Workday account for Acme Corp to continue") so the user knows precisely
     which accounts to go create. Don't drop the row or silently exclude it
     from the run's count for this reason — it's tracked and gets revisited
     per step 5 above once the user has signed in.
   - **Stop before the final submit** unless the criteria doc's default (or
     an explicit instruction for this run) says to auto-submit, and never
     click it even on a multi-step flow's last screen. When stopping, tell
     the user the application is filled and ready for their review. Never
     close a tab you opened or filled, whether it's complete or blocked.
   - Either way — filled, submitted, or blocked — record it in the tracker
     immediately, so a future run never repeats the work.

8. **Track reusable info gaps.** When a form asks something the criteria doc
   doesn't cover and the kind of thing likely to recur across applications
   (desired salary, start date, notice period, relocation specifics, a
   portfolio/GitHub link, reference availability, a recurring EEO-style
   question not already captured) — don't guess. Leave the field blank in
   that application, and log the gap once (check first whether it's already
   logged) so the user can decide whether to add it to the criteria doc.
   One-off, listing-specific narrative questions aren't reusable gaps —
   answer those as best you can or leave them blank, but don't log them.

9. **Final report.** Lead with anything that needs the user's own timely
   action (a timed assessment invite, an expiring offer). Then: how many
   applications were filled this run vs. any stated floor; what was verified
   via the status-check step; anything notable in the user's own tracker
   notes that was seen and acted on; how many rows remain blocked on manual
   handling, broken out by which ones are blocked specifically on account
   creation (company + portal) so the user knows exactly what to go set up;
   whether Chrome was connected; and any open reusable-info questions for
   the user.

## Phase 3: Scheduling

Scheduled runs must use the session's scheduled-task tools — never a local/
in-process cron tool, since anything scheduled that way is lost the moment
this session ends. Tool availability varies by session: some sessions only
expose a way to *create* a scheduled task, with no corresponding list/update/
delete tools available to Claude directly. Check what's actually present
before promising an action:
- If create-only tools are available, create with a complete standalone
  prompt (below) and tell the user plainly that changing it later may
  require them to edit it themselves in the app, since this session may not
  be able to reach back into an existing scheduled task.
- If list/update/delete tools are available, prefer `update_trigger` (or
  equivalent) on the existing task's ID over delete-and-recreate — it
  preserves run history.
- If the user needs a change made to a scheduled task and no tool in this
  session can reach it, don't guess or claim it's done — give the user the
  complete, ready-to-paste replacement prompt text and tell them exactly
  where to paste it (the task's settings in the app).

Recommended default: **a daily digest with no auto-apply**, unless the user
explicitly asks for auto-fill on a schedule. The scheduled prompt should
tell the fresh session to read the criteria doc and tracker, search sources,
filter against the tracker, and message the user a ranked digest —
explicitly *not* to fill out or submit anything. This is the safe default
because a scheduled run is unattended by definition, and autofilling or
submitting without anyone reviewing it is exactly the kind of irreversible
action that should wait for a person.

When writing the scheduled prompt:
- Write it as a complete, standalone instruction — the fresh session that
  runs it has no memory of this conversation. It should name this skill (or
  restate its rules inline), name exactly where the criteria doc/tracker
  live (file paths, and which Project if any), and state clearly what it
  should and shouldn't do without asking (see "Working unattended" below).
- A daily cadence is typical; use a cron expression at a reasonable hour in
  the user's timezone (convert to UTC). Don't schedule more often than daily
  unless the user asks — job boards don't refresh fast enough to justify it,
  and it burns their scheduled-run budget.
- If the user wants scheduled runs to also *fill* applications, that only
  works reliably if their Chrome (or device bridge) stays connected at fire
  time — say so plainly, and suggest they treat auto-fill as something to
  trigger manually right after reviewing a digest unless they've confirmed
  the browser bridge is reliably available on that schedule.
- Never set the trigger to auto-submit applications without an explicit,
  clear request from the user to do so — confirm it back to them in plain
  language before creating or updating the trigger that way.
- Include the accounts/credentials hard rule from Phase 2 explicitly in the
  prompt text (don't just reference this skill by name) if there's any
  chance the fresh scheduled session won't have this skill loaded — a
  scheduled run that quietly pre-filters out every listing requiring an
  account is a common failure mode and worth guarding against directly in
  the prompt.

### Working unattended

A scheduled run has no one to ask mid-run. Give it explicit, unambiguous
rules for the situations it will hit repeatedly rather than leaving them to
its judgment each time — the account-wall handling above is one example.
Others worth spelling out in the prompt: what counts as "done" for the run
(a floor count, or "until reasonable candidates run out"), what to do if a
data source (email, a browser, a specific site) isn't reachable (report it,
don't silently skip), and what's timely enough to flag at the very top of
the report versus what can wait in the row detail.

## Notes for whoever installs this skill

This skill is shared, but the data it produces is not: each person's
criteria doc, application tracker, and resume belong to them. When setting
this up for a new user, do not reuse or reference another user's saved
criteria or tracker — start Phase 1 fresh. If multiple people share one
Project or folder, use distinctly named docs per person (e.g.
`job-search-criteria-alex.md`) rather than one shared file.

Job boards' terms of service vary on automated access — search-based
discovery is generally fine, but be judicious about high-frequency scraping
or anything that looks like evading a site's normal usage limits.
