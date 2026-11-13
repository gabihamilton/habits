#!/usr/bin/env python3
"""Read and fix the tracker's daily rows in Supabase (table health_daily).

  db.py get [FROM] [TO]              rows as a table (default: last 14 days)
  db.py set DATE field=value ...     change only the given fields (weight, intake, burn)
  db.py clear DATE field ...         set fields to empty (e.g. a wrong weigh-in)
  db.py check [DAYS]                 table + things worth flagging (default 7 days)
  db.py compare [WINDOW]             measured maintenance vs Cronometer burn (default 14)

Dates are YYYY-MM-DD. The math in `compare` mirrors analyzeEnergy() in index.html.
"""
import json, sys, urllib.request
from datetime import date, timedelta

URL = 'https://mghqfyjckbzhyefpzkaq.supabase.co/rest/v1/health_daily'
KEY = 'sb_publishable_BVJz5Rcer9rJlP-AcVPp0A_n0-UAK6z'  # publishable; public in index.html
FIELDS = {'weight': 'weight_lb', 'intake': 'intake_kcal', 'burn': 'burn_kcal'}
KCAL_PER_LB, EMA_ALPHA, BAND = 3500, 0.1, 0.2


def req(method, query='', body=None):
    r = urllib.request.Request(URL + query, method=method, data=json.dumps(body).encode() if body else None)
    for k, v in {'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json',
                 'Prefer': 'return=representation'}.items():
        r.add_header(k, v)
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read() or 'null')


def rows(frm=None, to=None):
    q = '?select=*&order=date'
    if frm: q += '&date=gte.' + frm
    if to: q += '&date=lte.' + to
    return req('GET', q)


def num(v):  # 0/blank count as "no reading", same as the app
    return float(v) if v is not None and float(v) > 0 else None


def fmt(v, d=0):
    return '—' if v is None else (f'{v:,.{d}f}')


def table(rs):
    print('| Day | Weight (lb) | Eaten (kcal) | Cronometer burn (kcal) |\n|---|---|---|---|')
    for r in rs:
        dd = date.fromisoformat(r['date'])
        print(f"| {dd:%a %b} {dd.day} | {fmt(num(r['weight_lb']), 1)} | {fmt(num(r['intake_kcal']))} "
              f"| {fmt(num(r.get('burn_kcal')))} |")


def check(days):
    start = date.today() - timedelta(days=days - 1)
    rs = rows(start.isoformat())
    table(rs)
    have = {r['date'] for r in rs}
    flags = []
    for i in range(days):
        d = (start + timedelta(days=i)).isoformat()
        if d not in have: flags.append(f'{d}: no row at all')
    prev = None
    for r in rs:
        w, i, b = num(r['weight_lb']), num(r['intake_kcal']), num(r.get('burn_kcal'))
        missing = [n for n, v in (('weight', w), ('eaten', i), ('burn', b)) if v is None]
        if missing: flags.append(f"{r['date']}: missing {', '.join(missing)}")
        if w and prev and abs(w - prev) >= 1.5: flags.append(f"{r['date']}: weight moved {w - prev:+.1f} lb vs previous weigh-in")
        for n, v in (('weight', r['weight_lb']), ('eaten', r['intake_kcal'])):
            if v is not None and len(str(v).split('.')[-1]) > 3 and '.' in str(v):
                flags.append(f"{r['date']}: {n} = {v} — long decimals, likely written by an Apple Health Shortcut, not typed")
        if i and b and abs(i - b) > 1200: flags.append(f"{r['date']}: eaten vs burn differ by {i - b:+,.0f} — typo?")
        if w: prev = w
    print('\nFlags:' if flags else '\nNo flags.')
    for f in flags: print('-', f)


def compare(window):
    rs = rows('2020-01-01')
    pts, trend, prev_day = [], None, None
    for r in rs:  # calendar-day-aware EMA over full history
        w = num(r['weight_lb'])
        if w is None: continue
        dn = date.fromisoformat(r['date']).toordinal()
        trend = w if trend is None else trend + (1 - (1 - EMA_ALPHA) ** max(1, dn - prev_day)) * (w - trend)
        prev_day = dn
        pts.append((dn, trend))
    if len(pts) < 2: sys.exit('Not enough weigh-ins.')
    cutoff = pts[-1][0] - window + 1
    wp = [p for p in pts if p[0] >= cutoff]
    recent = [r for r in rs if date.fromisoformat(r['date']).toordinal() >= cutoff]
    intakes = [num(r['intake_kcal']) for r in recent if num(r['intake_kcal'])]
    burns = [num(r.get('burn_kcal')) for r in recent if num(r.get('burn_kcal'))]
    print(f'Window: last {window} days ending {date.fromordinal(pts[-1][0])} — '
          f'{len(wp)} weigh-ins, {len(intakes)} days eaten, {len(burns)} days burn')
    if len(wp) < 3 or len(intakes) < 3: sys.exit('Need at least 3 weigh-ins and 3 days eaten.')
    mx = sum(p[0] for p in wp) / len(wp); my = sum(p[1] for p in wp) / len(wp)
    den = sum((p[0] - mx) ** 2 for p in wp)
    slope = sum((p[0] - mx) * (p[1] - my) for p in wp) / den if den else 0
    avg_in = sum(intakes) / len(intakes)
    tdee = avg_in - slope * KCAL_PER_LB
    status = 'deficit' if slope * 7 <= -BAND else 'surplus' if slope * 7 >= BAND else 'maintenance'
    print(f'Trend {slope * 7:+.2f} lb/week ({status}); avg eaten {avg_in:,.0f}; '
          f'measured maintenance {tdee:,.0f} kcal')
    if len(burns) >= 3:
        b = sum(burns) / len(burns); gap = b - tdee
        print(f'Cronometer avg burn {b:,.0f} → off by {gap:+,.0f} kcal ({gap / tdee * 100:+.0f}%); '
              f'correction factor {tdee / b:.2f}')
    else:
        print('Fewer than 3 days of Cronometer burn — no comparison yet.')


def main(a):
    if not a or a[0] in ('-h', '--help'): print(__doc__); return
    cmd = a[0]
    if cmd == 'get':
        frm = a[1] if len(a) > 1 else (date.today() - timedelta(days=13)).isoformat()
        table(rows(frm, a[2] if len(a) > 2 else None))
    elif cmd in ('set', 'clear'):
        d, body = a[1], {}
        for x in a[2:]:
            k, _, v = x.partition('=')
            if k not in FIELDS: sys.exit(f'unknown field {k}; use {", ".join(FIELDS)}')
            body[FIELDS[k]] = None if cmd == 'clear' else float(v)
        before = rows(d, d)
        if not before:
            if cmd == 'clear': sys.exit(f'No row for {d}.')
            out = req('POST', '', [dict(date=d, **body)])
        else:
            out = req('PATCH', '?date=eq.' + d, body)
        print('before:', before[0] if before else 'no row'); print('after: ', out[0])
    elif cmd == 'check': check(int(a[1]) if len(a) > 1 else 7)
    elif cmd == 'compare': compare(int(a[1]) if len(a) > 1 else 14)
    else: sys.exit(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
