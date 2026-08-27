# Claude Skills

A collection of custom skills for Claude — shareable across [Claude Code](https://claude.com/product/claude-code), the Claude desktop app, and [claude.ai](https://claude.ai).

Each skill lives in its own folder containing a `SKILL.md` (and, sometimes,
supporting `references/`, `scripts/`, or `assets/` files). How you install a
skill depends on which Claude surface you're using.

## Installing a skill

### Claude Code

Claude Code reads skills directly from a folder on disk — no zipping or
uploading required.

1. Clone or download this repo.
2. Copy the skill's folder into your Claude Code skills directory:
   - **Personal** (available in every project you work in):
     `~/.claude/skills/`
   - **Project-only** (available just inside one repo): `.claude/skills/`
     at that repo's root

   ```bash
   cp -r job-application-assistant ~/.claude/skills/
   ```
3. Start (or restart) a Claude Code session. Skills under those paths are
   picked up automatically — there's no separate registration step.

### Claude Desktop or claude.ai (web)

The desktop app and web don't read a local folder — they install skills
from a `.skill` file, which is just a zip archive with a different
extension.

1. From this repo, download the folder for the skill you want (e.g. on
   GitHub: open the folder → **⋮** → **Download folder**, or clone the
   whole repo and grab the folder locally).
2. Compress that folder into a `.zip`. Make sure `SKILL.md` ends up at the
   top level of the archive, not nested inside an extra folder:
   ```bash
   zip -r job-application-assistant.zip job-application-assistant
   ```
3. Rename the file extension from `.zip` to `.skill`:
   ```bash
   mv job-application-assistant.zip job-application-assistant.skill
   ```
4. Send that `.skill` file to Claude in a conversation (attach it like any
   other file). A file card will appear with a **Save skill** button —
   click it.
5. The skill is now saved to your account and available in future
   sessions across Claude Desktop, claude.ai, and Cowork.

## Skills in this repo

### `job-application-assistant`

Runs an end-to-end job search workflow — finds job listings across
LinkedIn, Indeed, and company career pages that match a saved resume and
criteria doc, ranks them, and (when asked) autofills the application forms
in Chrome for review. Covers first-time setup (resume + criteria
interview), a normal search/apply run, and setting up a recurring
scheduled run (daily digest by default, no auto-apply unless explicitly
configured).

### `meal-tracker`

Logs meals dropped into chat as photos or text descriptions into a personal
nutrition log (`data/log.csv`), with estimated calories and macros plus a
qualitative note. On first use it interviews you for sex, height, weight,
age, activity level, dietary restrictions, and goals (`data/profile.md`),
then uses that profile plus your logged history to give grounded diet
advice and meal suggestions instead of generic tips. Bundles a script
(`scripts/summarize_log.py`) for accurate daily/weekly nutrition totals
when you ask for a recap.

The log and profile only live on this computer, so when you're on your
phone (Cowork with no linked device) or otherwise away from a session that
can reach this repo, the skill queues new entries in Claude's memory
instead and folds them into `data/log.csv`/`data/profile.md` automatically
the next time it runs somewhere with access — nothing gets lost, it just
syncs a little late.
