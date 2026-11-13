---
name: edit-habits
description: Add, remove, rename or reschedule habits on Gabi's daily checklist (Today / Stats tabs) and put the change live. Use for "add a habit", "remove X", "rename the sleep one", "only on weekdays", "stop it from <date>".
---

# Editing the habit checklist

The list is `const HABITS = [...]` near the top of the `<script>` in `index.html`
(`grep -n "const HABITS" index.html`). Each entry:

```js
{ id: 'nighttea', label: 'Night tea' }
{ id: 'jobprep', label: '30 min of job prep', days: [1, 2, 3, 4, 5] } // 0=Sun … 6=Sat
{ id: 'probiotic', label: 'Probiotic', from: '2026-11-11', until: '2026-12-31' } // inclusive, optional
```
`isActive()` uses `from` / `until` / `days`; nothing else needs changing.

## Rules
- **id** is the key of the saved history on Gabi's phone (localStorage, per day).
  - Wording tweak, same meaning → keep the id (history continues).
  - Meaning changes (e.g. "went to bed on time" → "got enough sleep") → new id; old history stays
    saved but hidden. Say so.
  - Removing a habit just deletes the line; its history stays saved but stops showing.
  - Bringing one back → reuse its old id (check `git log -p -S "id: '<id>'" -- index.html`).
    Say that Stats will count the gap as missed unless you add `from`.
- Order matters on screen: keep related habits together (tracking, supplements, movement, work,
  evening/sleep). Put a new habit next to its group unless Gabi says where.
- Keep labels short and concrete, with the target in the label when there is one
  ("Drank 2 L of water", "Ate enough protein (125 g+)"). The protein target lives in
  `~/Code/food-optimization/data/targets.json`.

## Ship it
Edit with one exact replacement, show the resulting list (`sed -n '/^const HABITS/,/^\];/p' index.html`),
then commit straight to `main` and push — that deploys it. Tell Gabi to close and reopen the app.
No browser test needed for list-only changes.
