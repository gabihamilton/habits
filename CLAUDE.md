# habits — notes for Claude

Gabi's personal habit + weight tracker. One static file, `index.html` (vanilla JS, no build).
GitHub Pages serves `main`, so **pushing to `main` = live on Gabi's phone**. Committing straight
to `main` is fine here; no branches/PRs needed. After a push Gabi closes and reopens the app.

- **Today / Stats tabs** — daily checklist, stored in the phone's localStorage. The list is
  `const HABITS = [...]` in `index.html`. For changes use the `edit-habits` skill.
- **Weight tab** — weight, calories eaten and Cronometer's estimated burn, one row per day in
  Supabase (`health_daily`). It computes real maintenance from the weight trend and compares it
  with Cronometer's burn. For reading/fixing days or the weekly check use the `health-data` skill.
- `SETUP.md` is the guide for other people self-hosting it; keep its SQL in sync with the table.

Never commit CSV/spreadsheet exports (personal data; see `.gitignore`). The Supabase key in
`index.html` is the publishable one and is meant to be public.
