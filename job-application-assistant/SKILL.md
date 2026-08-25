---
name: job-application-assistant
description: Runs an end-to-end job search workflow — finds job listings across LinkedIn, Indeed, and company career pages that match a saved resume and criteria doc, ranks them, and (when asked) autofills the application forms in Chrome for review. Use this skill whenever the user wants to search for jobs, find listings that match their background, set up a recurring job search, get a digest of new postings, or have an application form filled out automatically. Also use it for first-time setup ("help me set up my job search," "I want to automate applying to jobs") and for creating or updating a scheduled/recurring job search run. Trigger on phrases like "find me jobs," "search for openings," "fill out this application," "apply to this job for me," "set up a daily job search," or "what jobs match my resume."
---

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
  template) — the user's target roles, locations, salary floor, and
  dealbreakers, plus their default preference for auto-submitting
  applications.
- **The application log** (`references/application-log-template.md` is the
  template) — every listing seen or applied to, so a scheduled run never
  re-surfaces or re-applies to the same job.

If this session is attached to a claude.ai Project (check for a `Projects`
tool), write both docs there with `project_write` — e.g.
`job-search-criteria.md` and `job-search-log.md` — and read them back with
`project_read` / `project_search` at the start of every run. This is
strongly preferred: it's what makes a *scheduled* run (a fresh session with
no memory of this conversation) able to pick up where the last run left off.
If no Project is attached, fall back to local files in the working directory
and tell the user plainly that this data will not persist once the session
ends — offer to attach a Project or have them save the files somewhere
durable.

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
     terms for the same role)
   - Locations and remote/hybrid/onsite preference
   - Minimum acceptable salary (optional but improves filtering)
   - Industries or company types to include or explicitly avoid
   - Years of experience to represent (usually inferable from the resume,
     confirm rather than re-derive from scratch)
   - Work authorization / sponsorship needs, if relevant to the user
   - Dealbreakers (anything that should auto-exclude a listing)
   - Which sources to search: LinkedIn, Indeed, specific company career
     pages, or all of the above
   - Default behavior when an application is ready: **stop and let the user
     review before submitting**, or **submit automatically**. Default to
     "stop and review" unless the user clearly asks for full automation —
     autofilled forms can contain a wrong guess, and a submitted application
     is hard to take back.

   Write the criteria doc as soon as the interview is done, following
   `references/context-doc-template.md`. Don't wait until every other setup
   step is finished to save it.

3. **Create an empty application log** from
   `references/application-log-template.md` so the first real run has
   somewhere to write.

4. **Confirm with the user** what was captured (a short summary, not a full
   reprint of the doc) and ask if anything needs correcting before the first
   real run.

## Phase 2: A search / apply run

1. **Load context.** Read the criteria doc, the application log, and (if not
   already in context) the resume.

2. **Search.** For each configured source:
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

3. **Filter and rank.** Drop anything already in the application log
   (compare by listing URL or by company + title + posted date). Drop
   anything that fails a stated dealbreaker. Rank what's left by fit against
   the resume — title match, seniority match, location/remote match, and
   any explicit must-haves. Don't just return everything that matched a
   keyword search; the value of this skill is the filtering.

4. **Present the results.** Give the user a short ranked digest — company,
   title, location, why it's a fit, link — not a wall of raw search output.
   If this is an unattended/scheduled run (see Phase 3), this digest *is*
   the deliverable; stop here unless the criteria doc says otherwise.

5. **Fill out applications, when asked.** For listings the user (or the
   criteria doc's default) says to proceed with:
   - Open the application in Chrome and fill every field it asks for using
     the resume and criteria doc as the source of truth.
   - For free-text screening questions, answer truthfully from what's
     actually in the resume/criteria doc. If a question needs information
     the skill doesn't have (e.g., "why do you want to work here"), don't
     invent an answer — draft something clearly marked as a draft and flag
     it for the user to review or write themselves, or leave it blank and
     tell the user it needs their input.
   - Upload the resume file where the form asks for one.
   - **Stop before the final submit** unless the criteria doc's default (or
     an explicit instruction for this run) says to auto-submit. When
     stopping, tell the user the application is filled and ready for their
     review.
   - Either way — filled, submitted, or abandoned — record it in the
     application log immediately, so a future run never repeats the work.

## Phase 3: Scheduling

Scheduled runs must use the scheduled-task tools (`create_trigger` /
`update_trigger` / `list_triggers` / `delete_trigger`) — never a local/
in-process cron tool, since anything scheduled that way is lost the moment
this session ends.

Recommended default: **a daily digest with no auto-apply.** The scheduled
prompt should tell the fresh session to read the criteria doc and
application log, search sources, filter against the log, and message the
user a ranked digest — explicitly *not* to fill out or submit anything. This
is the safe default because a scheduled run is unattended by definition, and
autofilling or submitting without anyone reviewing it is exactly the kind of
irreversible action that should wait for a person.

When creating the trigger:
- Write the `prompt` as a complete, standalone instruction — the fresh
  session that runs it has no memory of this conversation. It should name
  this skill, name where the criteria doc/log live (which Project, if any),
  and state clearly that it should stop at the digest unless told otherwise.
- A daily cadence is typical; use a cron expression at a reasonable hour in
  the user's timezone (convert to UTC). Don't schedule more often than
  daily unless the user asks — job boards don't refresh fast enough to
  justify it, and it burns their scheduled-run budget.
- If the user wants scheduled runs to also *fill* applications (not just
  digest), that only works reliably if their Chrome stays connected at fire
  time — say so plainly, and suggest they treat auto-fill as something to
  trigger manually right after reviewing a digest, rather than as part of
  the unattended schedule, unless they've confirmed the browser bridge is
  reliably available on that schedule.
- Never set the trigger to auto-submit applications without an explicit,
  clear request from the user to do so — confirm it back to them in plain
  language before creating or updating the trigger that way.

To change an existing schedule's cadence or behavior, use `update_trigger`
on its existing ID rather than deleting and recreating — it preserves run
history. Use `list_triggers` to find the ID if it's not already known.

## Notes for whoever installs this skill

This skill is shared, but the data it produces is not: each person's
criteria doc, application log, and resume belong to them. When setting this
up for a new user, do not reuse or reference another user's saved criteria
or log — start Phase 1 fresh. If multiple people share one Project, use
distinctly named docs per person (e.g. `job-search-criteria-alex.md`) rather
than one shared file.

Job boards' terms of service vary on automated access — search-based
discovery is generally fine, but be judicious about high-frequency scraping
or anything that looks like evading a site's normal usage limits.
