# Habit + Weight Tracker — setup guide (for sharing)

A single static `index.html` (vanilla JS, no build step). Two parts:

- **Today / Stats tabs** — a daily habit checklist (stored in the browser, per-device).
- **Weight tab** — an adaptive-TDEE energy tracker: enter your daily weight + calories and it tells you whether you're in a **deficit / maintenance / surplus**, computed from your *smoothed weight trend* vs. your intake. Data syncs to a personal Supabase database so it survives refreshes and devices.

You can keep both parts or delete the habit tabs — the Weight tab is self-contained. **Claude can adapt any of this for you** (change the habit list, remove the habit tabs, restyle, etc.) — just ask it.

### It doesn't matter which apps you use
The app is just a web page + a database. **You read your weight and calories from whatever you already use — any food tracker (MyFitnessPal, LoseIt, MacroFactor, Cronometer…) and any scale/weight app — and type them into the built-in "Add / edit a day" form.** That's the whole data path, and it works on **any phone, including Android** (it's a website, not an iOS app).

Everything below about **Apple Health, Cronometer, and Shortcuts is optional** — it's just an iOS convenience for auto-filling *weight*. Skip that entire section if you're not on iOS or you'd rather just type two numbers a day. If your apps have their own export/API and you want automatic import, ask Claude — it can build that for your specific apps.

---

## ⚠️ Most important step: use YOUR OWN Supabase

The code ships with the original owner's Supabase URL + key. You **must** replace them with your own (Step 3), or your weight/calorie data will write into someone else's database and be readable by them.

---

## Step 1 — Get the code
Fork or download `index.html` from the shared repo into your own new GitHub repository.

## Step 2 — Create your Supabase (free)
1. Go to supabase.com → **New project** (free tier). On the create screen set: **Enable Data API** = ON, **Automatically expose new tables** = off, **Enable automatic RLS** = on. Save the database password somewhere safe (you won't need it for the app, but don't lose it).
2. When it finishes provisioning, open **SQL Editor**, paste this, and **Run**:

```sql
create table if not exists public.health_daily (
  date         date primary key,
  weight_lb    numeric,
  intake_kcal  numeric,
  updated_at   timestamptz not null default now()
);

alter table public.health_daily enable row level security;

create policy "anon read"   on public.health_daily for select to anon using (true);
create policy "anon insert" on public.health_daily for insert to anon with check (true);
create policy "anon update" on public.health_daily for update to anon using (true) with check (true);

grant select, insert, update on public.health_daily to anon;

create or replace function public.touch_updated_at()
  returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end; $$;

create trigger health_daily_touch before update on public.health_daily
  for each row execute function public.touch_updated_at();
```

## Step 3 — Put in your credentials
In `index.html`, near the top of the `<script>` (search for `SUPABASE_URL`), replace these two lines:

```js
const SUPABASE_URL = 'https://YOURPROJECT.supabase.co';
const SUPABASE_KEY = 'sb_publishable_YOURKEY';
```

Get both from Supabase → **Project Settings → API Keys**: the **Project URL** and the **publishable** key (a.k.a. `anon public`). Use the *publishable* one, **never** the `secret` / `service_role` key. The publishable key is safe in public code because Row-Level Security gates access.

(Optional, tidiness) rename the browser-storage keys so they're yours:
```js
const STORE_KEY  = 'gabi-habit-tracker'; // -> your-name-habits
const ENERGY_KEY = 'gabi-energy-data';   // -> your-name-energy
```

## Step 4 — Deploy
GitHub repo → **Settings → Pages** → deploy from the `main` branch (root). Your app will be live at `https://<you>.github.io/<repo>/`. Open it on your phone and **Add to Home Screen** for an app-like icon.

## Step 5 — Use it (works with any apps, any phone)
- **Weight tab → "Add / edit a day":** pick a date (defaults to today), type your **weight** and/or **calories** — read off *whatever* food tracker and scale/weight app you use — tap **Save**. That's the reliable, universal way to log; nothing about it is tied to a specific app or platform.
- The **Analysis window** (14/21/28 days) drives the verdict — 28 days is the steadiest read if you don't weigh every day.
- Weigh on a consistent cadence (ideally every morning, same conditions) for the best trend.

---

## Optional (iOS only) — auto-push weight from Apple Health
**Skip this unless you're on an iPhone and your weight is in Apple Health.** It just saves you typing the weight number. On Android or with any other setup, use the manual form above (or ask Claude to wire up your own apps' export/API).

If your weight lives in Apple Health, a Shortcut can push it so you don't type it:
1. **Date** → **Format Date** (Custom format `yyyy-MM-dd`).
2. **Find Health Samples**: Body Mass, Sort by End Date, Order Latest, Limit 1 → **Calculate Statistics → Average**.
3. **Get Contents of URL**: `POST` to `https://YOURPROJECT.supabase.co/rest/v1/health_daily`
   - Headers: `apikey: <publishable key>`, `Authorization: Bearer <publishable key>`, `Content-Type: application/json`, `Prefer: resolution=merge-duplicates`
   - Request Body (JSON): `date` = Formatted Date, `weight_lb` = Average
4. Run it **manually** (foreground). Note: iOS background automations often fail the network request, so don't rely on an unattended nightly trigger.

**Calories: use the manual form, not Apple Health.** Nutrition apps (Cronometer, etc.) tend to write *duplicate* Dietary Energy entries into Apple Health, so calorie totals read from Health are unreliable. Typing the number from your food app is accurate and takes seconds.

---

## How the numbers are computed (so you can trust it)
- Daily scale readings are smoothed into a trend line with a **calendar-day-aware exponential moving average** (α = 0.1): `new = old + (1-(1-0.1)^gap) × (weigh-in − old)`, where `gap` = days since the last weigh-in.
- The **weekly trend** = least-squares slope of that smoothed line over the analysis window, × 7.
- **Daily balance** = slope (lb/day) × **3,500 kcal/lb** (energy in a pound of fat).
- **Maintenance** = average intake − daily balance.
- **Verdict**: within ±0.2 lb/week = maintenance, above = surplus, below = deficit.

It's only as accurate as your calorie logging and weigh-in consistency — and it needs ~2 weeks of data before the estimate stabilizes.
