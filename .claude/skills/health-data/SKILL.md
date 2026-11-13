---
name: health-data
description: Read, check or fix Gabi's daily weight / calories eaten / Cronometer burn in the tracker's Supabase database, and compare Cronometer's burn estimate with the measured maintenance. Use for "check this week's data", "fix Nov 12", "what does the app have for…", "I logged the wrong day", "how off is Cronometer".
---

# Health data (Weight tab)

Everything goes through `python3 -I .claude/skills/health-data/db.py` (no dependencies):

| Need | Command |
|---|---|
| What the app has for some days | `db.py get 2026-11-10 2026-11-12` (no args = last 14 days) |
| Weekly check | `db.py check` (or `check 14`) → table + flags |
| Fix numbers for a day | `db.py set 2026-11-12 intake=2095 burn=2495` |
| Remove a number (e.g. no weigh-in that day) | `db.py clear 2026-11-07 weight` |
| How off is Cronometer | `db.py compare` (or `compare 21`) |

Fields: `weight` (lb), `intake` (kcal eaten), `burn` (Cronometer's *total* burned: BMR + activity + exercise).
`set` and `clear` print the row before and after; show both.

## How the data behaves
- One row per date (primary key). A save overwrites only the fields it sends; it never duplicates.
- Gabi enters data with the app's **Add / edit a day** form: filled boxes replace, empty boxes keep
  the saved value. The form cannot clear a value — that is what `db.py clear` is for.
- The phone keeps a local copy and re-syncs on opening the Weight tab; the cloud row wins per day,
  so a fix here reaches the phone on Gabi's next open. No code change or push needed for data fixes.
- Gabi deleted the Apple Health Shortcut (Nov 2026). Values with long decimals (e.g. 145.062680002205)
  are old Shortcut writes; clean numbers are typed.

## Rules
- Change data only when Gabi gives the numbers (or explicitly asks). If what Gabi says doesn't match
  the row (e.g. a different day already holds those values), show the row and ask first.
- Answer with the **app's own numbers** in a table (Day | Weight | Eaten | Cronometer burn) so Gabi can
  compare with Cronometer. Don't bring in other projects' data (food-optimization) unless asked.
- Real spikes stay: a ~2 lb jump after a big or salty day is water; the trend line smooths it.
  Ask "typo or real?" once, and keep it if real.

## The Cronometer experiment
Gabi eats intuitively for ~2 weeks (restarted Nov 7, 2026), logging everything, to measure how far
Cronometer's burn estimate is from Gabi's real maintenance (`compare`). Notes when reporting:
- Real maintenance = avg eaten − (trend slope × 3,500 kcal/lb); trend = calendar-day-aware EMA (α 0.1).
- The first week after a break is often water weight; trust the 14-day number, 21 is steadier.
- Report: Cronometer avg burn, measured maintenance, gap in kcal and %, correction factor
  (multiply Cronometer's number by it).
