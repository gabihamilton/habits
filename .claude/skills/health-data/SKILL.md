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
| Mark / unmark a period day | `db.py set 2026-11-20 period=yes` (or `period=no`) |
| How off is Cronometer | `db.py compare` (or `compare 21`) |

Fields: `weight` (lb), `intake` (kcal eaten), `burn` (Cronometer's *total* burned: BMR + activity + exercise).
`period` (yes/no): Gabi was on their period that day. Weigh-ins on period days and 2 days either side
are left out of the trend (water weight); calories still count.
`set` and `clear` print the row before and after; show both.

## How the data behaves
- One row per date (primary key). A save overwrites only the fields it sends; it never duplicates.
- The food-optimization project's `log-day` skill also writes intake / burn / weight here from Cronometer
  screenshots (same `db.py set`), so a row can appear without Gabi using the form.
- Gabi enters data with the app's **Add / edit a day** form: filled boxes replace, empty boxes keep
  the saved value. The form cannot clear a value — that is what `db.py clear` is for.
- The phone keeps a local copy and re-syncs on opening the Weight tab; the cloud row wins per day,
  so a fix here reaches the phone on Gabi's next open. No code change or push needed for data fixes.
- Gabi deleted the Apple Health Shortcut (Nov 2026), but its nightly automation kept writing until Nov 25 (Nov 9 eaten, Nov 23–24 weigh-ins). Values with long decimals (e.g. 145.062680002205)
  are old Shortcut writes; clean numbers are typed.

## Rules
- Change data only when Gabi gives the numbers (or explicitly asks). If what Gabi says doesn't match
  the row (e.g. a different day already holds those values), show the row and ask first.
- Answer with the **app's own numbers** in a table (Day | Weight | Eaten | Cronometer burn) so Gabi can
  compare with Cronometer. Don't bring in other projects' data (food-optimization) unless asked.
- Real spikes stay: a ~2 lb jump after a big or salty day is water; the trend line smooths it.
  Ask "typo or real?" once, and keep it if real. Big estimated days (buffets, nights out) and
  rest days with a low burn are normal too.
- Gabi often writes after midnight: "today" then means the day that just ended. Don't question it.

## The Cronometer experiment
Gabi eats intuitively for ~2 weeks (restarted Nov 7, 2026), logging everything, to measure how far
Cronometer's burn estimate is from Gabi's real maintenance (`compare`). Notes when reporting:
- Real maintenance = avg eaten − (trend slope × 3,500 kcal/lb); trend = calendar-day-aware EMA (α 0.1).
  At the start and after a break of 14+ days it restarts from the average of the first week's
  weigh-ins (max 5), not from one reading — one low/high first reading used to fake a gain/loss.
- Period weigh-ins (period days ± 2) are skipped by the trend, so bloating doesn't fake a surplus.
  Say how many were left out when it applies.
- The ±2 window was checked (Nov 2026) against 12 cycles of scale weigh-ins: weight is lowest 3–7 days
  before the period, rises ~1 lb from 2 days before, and is back to normal by about day 3. So keep ±2;
  high weigh-ins a week before a period are ordinary noise, not water. Changing the window moved the
  Cronometer correction factor by only ~0.01. Calories eaten looked a little higher the week before
  (~+150 kcal) but too few logged cycles to trust.
- RENPHO scale exports give times in Geneva time; before Oct 2026 Gabi lived in Chicago (7 h behind),
  so "afternoon" times there are morning weigh-ins. Gabi always weighs in in the morning.
- The first week after a break is often water weight; trust the 14-day number, 21 is steadier.
- Report: Cronometer avg burn, measured maintenance, gap in kcal and %, correction factor
  (multiply Cronometer's number by it).
