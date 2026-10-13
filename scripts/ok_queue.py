#!/usr/bin/env python3
"""READ-ONLY view of the team OK queue (/workspace/agent-backups/Perseus/interrupt-pending.json,
written by team/tools/ok_request.py). Never writes it. Missing/malformed file -> empty queue.
Statuses: open, approved, denied, parked, blocked-offline, tap-pending, withdrawn, stale.
Newest record per ask_id wins. Staleness = ok_request.py rule (pausing clock + re-read required)."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
QUEUE = Path('/workspace/agent-backups/Perseus/interrupt-pending.json')
# Also Helios relay statuses (OK-QUEUE-DESIGN.md merged audit): pending=open,
# held-for-card / held-for-chat = waiting-parked, held-launch = launch-dnd.
# Status vocabulary: team/tools/ok_request.py + Helios audit (OK-QUEUE-DESIGN.md).
# Timers (minutes) mirror ok_request.MINS; the clock pauses in the launch window and while driving,
# and an ask can only go stale once Eve recorded a re-read (reread_at) — same rule as ok_request.sweep().
MINS = {'pending': 30, 'open': 30, 'held-launch': 30, 'held-for-card': 720, 'held-for-chat': 720, 'parked': 720}
CLOSED = {'approved', 'denied', 'withdrawn', 'stale', 'done', 'fail', 'failed', 'blocked', 'answered', 'info'}
EVE_MOOD = {'open': 'relay-active', 'tap-pending': 'relay-active',
            'parked': 'waiting-parked', 'blocked-offline': 'waiting-parked',
            'held-for-card': 'waiting-parked', 'held-for-chat': 'waiting-parked',
            'held-launch': 'launch-dnd'}
LAUNCH = Path('/workspace/living-icon-repo/docs/status/live/launch.json')
DRIVE = Path('/workspace/agent-backups/Eve/driving.json')

def _ts(s):
    if not isinstance(s, str): return None
    try:
        t = datetime.fromisoformat(s.strip().replace('Z', '+00:00'))
    except ValueError:
        return None
    return t if t.tzinfo else t.astimezone()

def norm_status(s):
    s = (s or '').strip().lower()
    if s in ('pending', 'open', ''): return 'open'
    if s == 'blocked-offline': return s
    if s.startswith('blocked'): return 'blocked'
    if s.startswith('resolved') or s.startswith('approved'): return 'approved'
    if s in ('later',): return 'parked'
    for k in ('denied', 'parked', 'tap-pending', 'withdrawn', 'stale', 'done', 'failed', 'fail',
              'answered', 'held-for-card', 'held-for-chat', 'held-launch', 'info'):
        if s.startswith(k): return k
    return s

def load_raw(path=None):
    try:
        data = json.loads(Path(path or QUEUE).read_text())
    except (OSError, ValueError):
        return []
    if isinstance(data, dict):
        data = data.get('items') or data.get('asks') or []
    return [r for r in data if isinstance(r, dict)] if isinstance(data, list) else []

def load(path=None):
    return [r for r in load_raw(path) if r.get('kind', 'ask') == 'ask']

def latest(items):
    """Append-only queue: the newest record per ask_id is that ask's state (as ok_request.latest)."""
    cur = {}
    for r in items:
        aid = r.get('ask_id') or r.get('id')
        if aid: cur[aid] = r
    return cur

def _pauses(items, now):
    iv = []
    try:
        net = _ts(json.loads(LAUNCH.read_text()).get('net'))
        if net: iv.append((net - timedelta(minutes=30), net + timedelta(minutes=60)))
    except (OSError, ValueError, AttributeError): pass
    on = None
    for r in items:
        if r.get('kind') == 'driving':
            if r.get('state') == 'on' and on is None: on = _ts(r.get('ts'))
            elif r.get('state') == 'off' and on: iv.append((on, _ts(r.get('ts')) or now)); on = None
    if on is None and DRIVE.exists():
        try: on = _ts(json.loads(DRIVE.read_text()).get('since'))
        except (OSError, ValueError): on = None
    if on: iv.append((on, now))
    return iv

def _elapsed_min(start, now, iv):
    tot = (now - start).total_seconds()
    for a, b in iv:
        a, b = max(a, start), min(b, now)
        if b > a: tot -= (b - a).total_seconds()
    return tot / 60

def active(items=None, now=None, path=None):
    """Asks still awaiting resolution: [{ask_id, bot, status, since}] (newest record per ask_id)."""
    now = now or datetime.now(timezone.utc)
    raw = items if items is not None else load_raw(path)
    iv = _pauses(raw, now)
    out = []
    for aid, r in latest([x for x in raw if x.get('kind', 'ask') == 'ask']).items():
        st = 'tap-pending' if r.get('tap_pending') and norm_status(r.get('status')) in ('held-for-card', 'held-for-chat') else norm_status(r.get('status'))
        if st in CLOSED: continue
        since = _ts(r.get('since')) or _ts(r.get('filed')) or _ts(r.get('sent_at')) or _ts(r.get('ts')) or _ts(r.get('time'))
        raw_st = norm_status(r.get('status'))
        if raw_st in MINS and since and r.get('reread_at'):
            if _elapsed_min(since, now, iv) >= MINS[raw_st]: continue   # stale (only after Eve re-read)
        out.append({'ask_id': aid, 'bot': r.get('bot'), 'status': st,
                    'since': since.isoformat() if since else None})
    return out

def eve_mood(act):
    ms = {EVE_MOOD.get(a['status']) for a in act}
    for m in ('launch-dnd', 'waiting-parked', 'relay-active'):
        if m in ms: return m
    return None

def newest_event(items=None, path=None):
    """Latest timestamp of any queue item (filed/answered/resolved), for manual-mood respect."""
    best = None
    for r in (items if items is not None else load(path)):
        for k in ('filed', 'sent_at', 'answered_at', 'resolved', 'since', 'ts'):
            t = _ts(r.get(k))
            if t and (best is None or t > best): best = t
    return best

def waiting_by_slug(act, name_to_slug):
    w = {}
    for a in act:
        b = (a.get('bot') or '').strip()
        slug = name_to_slug.get(b) or name_to_slug.get(b.lower())
        if slug and slug not in w:
            w[slug] = {'ask_id': a['ask_id'], 'since': a['since'], 'status': a['status']}
    return w

def name_map(m):
    d = {}
    for s, c in m['agents'].items():
        d[c['name']] = s; d[c['name'].lower()] = s; d[s] = s
        d[c['name'].split()[0].lower()] = d.get(c['name'].split()[0].lower(), s)
    return d
