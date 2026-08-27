---
name: meal-tracker
description: Logs meals (from photos or text descriptions) into a personal nutrition log with estimated calories and macros, and gives tailored diet/goal advice based on the user's stored profile (sex, height, weight, dietary restrictions, goals) and eating history. Use whenever the user explicitly asks to log, track, save, or record a meal/food/what they ate ("log this", "track my lunch", "add this to my food log"), asks for nutrition or diet advice, meal suggestions, a recap of their eating habits, or wants to set/update diet or health goals. If the user says a conversation is being used specifically to track meals going forward, treat every food photo/description dropped in afterward as an implicit log request without asking each time. On the very first-ever use, interview the user for their basic info before logging anything. Works even away from their computer (phone, no linked device) — queues entries and syncs later.
---

# Meal Tracker

Turns meal photos and descriptions dropped into chat into a running nutrition
log, and uses that log plus the user's stated goals to give grounded,
personalized advice — not generic diet tips.

The log's home is a local file next to this skill, but this skill can be
invoked from surfaces that don't have access to that file (e.g. Cowork on a
phone, or claude.ai without a linked computer). Step 0 below explains how to
tell which situation you're in and what to do about it — read it first.

## Where things live

- `data/profile.md` — the user's stats, restrictions, and goals (the
  permanent record)
- `data/log.csv` — every logged meal, one row each (the permanent record)
- `scripts/summarize_log.py` — computes daily/weekly totals from log.csv;
  only runs where you have a shell against these files

These files live next to this SKILL.md, on the user's computer. They are
the source of truth — always sync toward them, never treat the fallback
queue below as a second permanent copy.

If the user would rather store this elsewhere (e.g. a synced folder),
that's fine — just redirect reads/writes to the path they give you and
remember it for the rest of the conversation. Don't ask about this unless
they bring it up.

## Step 0: Do you actually have this file, right now?

Before doing anything else, figure out which mode you're in:

**Full access** — you can read and write `data/profile.md` and
`data/log.csv` directly (Claude Code with its normal file tools, or Cowork
with the computer holding this repo currently linked and reachable). This
is the common case. If you're not sure, just try reading `data/profile.md`
— if it works (or fails with a normal "file doesn't exist", meaning the
folder itself is reachable), you have full access. Skip to Step 1.

**No access** — you get a tool error, there's no filesystem/shell tool
available at all, or you're clearly in a mobile/no-device-linked context.
In this case, don't tell the user you simply can't help — fall back to
Claude's persistent memory as a queue, so nothing gets lost:

- Read `/areas/meal-tracker-pending.md` from memory (if the memory tools
  aren't available either, that's the true dead end: tell the user you
  can't log or reach their profile from here, and offer to log it verbally
  right now for them to paste in later, or to wait until they're back on
  their computer).
- If a pending file doesn't exist yet, that's fine — you'll create it the
  first time you need to queue something.
- Proceed through the rest of this skill exactly as normal (intake, meal
  logging, advice), but write anything that would normally go to
  `data/profile.md` or `data/log.csv` into that memory file instead, tagged
  clearly (see Step 1a / Step 3a below). Tell the user once, briefly, that
  this will sync to their main log next time you're on their computer —
  don't repeat that caveat on every message.

Either way, advice-giving (Step 4) should draw on the permanent log AND
any not-yet-synced entries sitting in the pending memory file, so advice
stays accurate even mid-queue.

## Step 1: First-time setup

Check whether `data/profile.md` exists (full access) or, failing that,
whether `/areas/meal-tracker-pending.md` already contains a profile section
(no access). If neither has one, this is the user's first time. Before
doing anything else, ask them for the basics needed to give real advice
rather than generic advice. Ask conversationally (not as a rigid form) for:

- Sex (relevant for calorie/macro baseline estimates)
- Height and weight
- Age (helps with calorie estimates; optional but useful)
- Activity level (sedentary / lightly active / very active, roughly)
- Dietary restrictions or preferences (allergies, vegetarian/vegan, kosher/halal, dislikes, etc.)
- Their goal(s) — e.g. weight loss, weight gain, muscle gain, maintenance, eating more balanced, hitting a protein target, managing energy levels, general health. Ask what "success" would look like to them.

You don't need every field filled to proceed — if they skip something, note
it as unknown and move on.

**Full access:** write the answers to `data/profile.md` using roughly this
shape:

```markdown
# Profile

- Sex:
- Age:
- Height:
- Weight:
- Activity level:
- Dietary restrictions/preferences:
- Goals:
- Notes: (anything else they volunteered)
- Last updated: YYYY-MM-DD
```

**No access (Step 1a):** append a `## Profile` section with the same
fields to `/areas/meal-tracker-pending.md` instead, and tell the user
this will finish saving to their permanent profile next time you're
on their computer.

Once saved (either way), let them know they can update any of this any
time just by telling you ("I'm now trying to cut back on sugar", "update
my weight to X") — with full access, re-read and edit `data/profile.md`
directly and bump "Last updated"; with no access, append the change to the
pending memory file the same way meals are queued (Step 3a), so it syncs
along with everything else.

**If a profile already exists** (in `data/profile.md`, or as a synced-in
pending entry), read it before logging or giving advice so your response
is grounded in their actual goals — don't re-ask the intake questions.

## Step 2: Deciding whether to log

Log a meal when the user:
- explicitly asks you to ("log this", "track this", "add my lunch")
- has told you earlier in this conversation that the whole chat is being
  used for meal tracking — in that case, treat any food photo or food
  description as a log request without asking each time
- shares a meal photo/description without a clear ask, and it's ambiguous
  whether they want it logged — in this case, briefly ask ("Want me to log
  this one?") rather than assuming

Don't log things that aren't actually meals (e.g. a photo of a menu, a
grocery haul, a restaurant storefront) — treat those as a question or
just respond normally.

## Step 3: Analyzing and logging a meal

For a photo, look closely at the components, portion sizes (use plate
size, utensils, or hands in frame as a rough scale reference when
present), and any visible preparation style (fried vs. grilled, sauce-heavy,
etc.). For a text description, work with what's given and ask a quick
follow-up only if a key quantity is genuinely unclear and would swing the
estimate a lot (e.g. "was that a small or large portion of rice?") —
otherwise just estimate and move on; these are always going to be
estimates, not lab measurements, and the user knows that.

Estimate:
- Calories
- Protein (g), Carbs (g), Fat (g)
- A short qualitative note: how balanced it is, whether it fits their
  dietary restrictions, and anything worth flagging relative to their
  goals (e.g. "solid protein for a cutting goal", "pretty light on veggies")

Every entry, wherever it ends up, uses this same row shape:

```
date,time,meal_label,description,calories,protein_g,carbs_g,fat_g,notes
```

- `date`: YYYY-MM-DD (today unless the user says otherwise)
- `time`: HH:MM 24h if known, otherwise leave blank
- `meal_label`: breakfast/lunch/dinner/snack — infer from time of day or ask if truly unclear
- `description`: short plain-text description of what was eaten
- `notes`: your qualitative note from above

**Full access:** append one row to `data/log.csv` (create it with the
header row above if it doesn't exist yet). Quote any field containing a
comma.

**No access (Step 3a):** append the same row, as a fenced ` ```csv ` line
(or a plain bullet if that's easier), under a `## Pending log entries`
section in `/areas/meal-tracker-pending.md`. This is a queue, not a
duplicate log — it gets folded into `data/log.csv` and cleared the next
time you have full access (Step 3b).

After logging (either way), confirm in one short line (e.g. "Logged:
grilled chicken bowl — ~650 kcal, 45g protein, 60g carb, 20g fat") — don't
restate the whole row, and don't belabor the sync/no-sync distinction once
the user already knows which mode you're in.

## Step 3b: Syncing pending entries

Whenever you find yourself with full access (Step 0), check
`/areas/meal-tracker-pending.md` for anything queued up before moving on
with the rest of the task — do this quietly as part of getting oriented,
the same way you'd check for an existing profile:

1. If it has `## Profile` section, merge those fields into
   `data/profile.md` (fill in anything missing there; a pending value
   should win over a blank, but ask the user if a pending value actually
   conflicts with an existing one rather than silently overwriting).
2. If it has `## Pending log entries`, append each row to `data/log.csv`
   in order.
3. Once synced, remove the synced content from the memory file (leave the
   file's frontmatter/description intact if the memory tool requires it,
   just clear the entries) so it doesn't get double-applied later.
4. Let the user know in one line, e.g. "Synced 3 meals you logged from
   your phone earlier this week."

If there's nothing pending, don't mention this step at all — it should be
invisible on the common path.

## Step 4: Giving advice

When logging a meal, when asked directly for advice, or when asked "what
should I eat", ground your answer in real data, not generic tips:

1. Read the profile (`data/profile.md`, merged with any pending profile
   info) for their goals and restrictions.
2. Read the relevant slice of the log — `data/log.csv` plus any entries
   still sitting in the pending queue — usually today's entries for
   in-the-moment advice ("what should I have for dinner"), or the last
   1-2 weeks for pattern-level advice.
3. Say something specific: what they're on track for today, what's low
   (e.g. protein, fiber, veggies), and 1-3 concrete meal ideas that would
   help close the gap — informed by what they've actually been eating
   (don't suggest something wildly outside their apparent preferences
   unless asked to branch out). Keep it to a few sentences of prose, not
   a big structured report, unless they ask for something more thorough.

Avoid being preachy or repeating the same boilerplate ("stay hydrated!",
"everything in moderation!") every time — treat this like a knowledgeable
friend who actually looked at what they ate, not a canned nutrition app.

## Step 5: Summaries

When the user asks for a recap, a weekly summary, or "how am I doing":

**Full access:** run the bundled script to get accurate daily/weekly
totals rather than eyeballing the CSV yourself — meal counts add up fast
and arithmetic mistakes undermine trust in the log:

```bash
python3 scripts/summarize_log.py data/log.csv --days 7
```

(Adjust `--days` for the period they're asking about — e.g. `--days 1`
for just today, `--days 30` for a month.) The script prints per-day totals
and a period average for calories and each macro. If there are also
pending (unsynced) entries in memory for the period in question, sync them
first (Step 3b) so the script's totals include them.

**No access:** you can't run the script, so total up the entries in the
pending memory file yourself — the entry counts here are small enough
that this is fine to do by hand, just be careful with the arithmetic.

Either way, use the totals plus the profile to write a short, honest
recap: how the period tracked against their goal, any clear patterns
(e.g. protein consistently low, weekends much higher calorie), and one or
two suggestions going forward. Don't just dump the raw numbers —
interpret them.

If the user wants this recap automatically on a schedule (e.g. every
Sunday), you can offer to set that up as a scheduled task if the
environment supports it — that's separate from this skill itself.

## A note on accuracy

These are visual/descriptive estimates, not a food scale or barcode
lookup — say so naturally if the user pushes on precision (e.g. "that's a
rough estimate based on the photo, could easily be ±15%"), but don't
caveat every single message with a disclaimer. The log is most valuable
for spotting trends over time, not for any single number being exact.
