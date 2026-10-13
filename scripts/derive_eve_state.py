#!/usr/bin/env python3
"""Derive Eve's mood from Helios's relay log (READ-ONLY) + optional launch window.
usage: derive_eve_state.py [--log PATH] [--net ISO8601] [--once | --loop SECONDS]

Status names: Helios eve-relay/SCHEMA.md (canonical).
  pending -> relay-active | held-for-card -> waiting-parked | answered -> no change
  done/failed -> idle (clears a derived mood)
Rules: newest line per ask_id is that ask's state; pending older than 30 min
(by sent_at) and held-for-card older than 12 h (by answered_at, else sent_at) are stale.
Priority: launch-dnd > waiting-parked > relay-active > idle. A live hold is never overridden.
tick() always returns (mood, action, ask_id); action in hold-respected|manual-respected|wrote|cleared|unchanged.
Also merges the OK queue (scripts/ok_queue.py, read-only)."""
import argparse, json, time, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from set_mood import write_state, LIVE, canonical_path
import ok_queue
LOG = Path('/workspace/agent-backups/Helios/eve-relay/relay-log.jsonl')
LAUNCH = LIVE / 'launch.json'   # optional {"net": "ISO8601"} written by a launch watcher
GO_BEFORE, WATCH_AFTER = 30 * 60, 60 * 60   # NET-30min .. NET+60min (WATCH_AFTER_NET_SEC)
STALE = {'pending': 30 * 60, 'held-for-card': 12 * 3600, 'held-for-chat': 12 * 3600}
MOOD = {'pending': 'relay-active', 'held-for-card': 'waiting-parked', 'held-for-chat': 'waiting-parked',
        'held-launch': 'launch-dnd'}   # Tinkabot diff + Helios audit (OK-QUEUE-DESIGN.md)
DERIVED = {'relay-active', 'waiting-parked', 'launch-dnd'}

def _ts(s):
    if not s: return None
    try:
        t = datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except ValueError:
        return None
    return t if t.tzinfo else t.astimezone()   # naive = box-local (CT)

def rows(path):
    """relay-log.jsonl rows; missing/retired file (e.g. renamed .retired) -> [] (queue still drives Eve)."""
    try:
        if not path.exists(): return []
    except OSError:
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            try: out.append(json.loads(line))
            except ValueError: pass
    return out

def latest_per_ask(rs):
    cur = {}
    for r in rs:                      # append-only: later lines win
        if r.get('ask_id'): cur[r['ask_id']] = r
    return list(cur.values())

def is_stale(r, now):
    st = r.get('status')
    ref = _ts(r.get('sent_at')) if st == 'pending' else (_ts(r.get('answered_at')) or _ts(r.get('sent_at')))
    if st not in STALE: return False   # held-launch: no timeout (launch window governs)
    return ref is None or (now - ref).total_seconds() > STALE[st]

def in_launch_window(net, now):
    n = _ts(net)
    if not n: return False
    t = (n - now).total_seconds()     # seconds until NET
    return -WATCH_AFTER <= t <= GO_BEFORE

PRIORITY = ('launch-dnd', 'waiting-parked', 'relay-active')
QUEUE = None   # None -> ok_queue.QUEUE; tests override

def queue_path():
    return QUEUE or ok_queue.QUEUE

def derive(log, net, now, queue=None):
    """Merge relay-log.jsonl + OK queue (interrupt-pending.json, read-only).
    Priority launch-dnd > waiting-parked > relay-active > idle."""
    if net and in_launch_window(net, now):
        return 'launch-dnd', None
    cands = []
    live = [r for r in latest_per_ask(rows(log)) if r.get('status') in MOOD and not is_stale(r, now)]
    if any(r['status'] == 'held-launch' for r in live):
        cands.append(('launch-dnd', None))
    for status in ('held-for-card', 'held-for-chat', 'pending'):
        hits = [r for r in live if r['status'] == status]
        if hits:
            cands.append((MOOD[status], max(hits, key=lambda r: _ts(r.get('answered_at') or r.get('sent_at')) or now)))
            break
    act = ok_queue.active(now=now, path=queue or queue_path())
    for want in ('launch-dnd', 'waiting-parked', 'relay-active'):
        hits = [a for a in act if ok_queue.EVE_MOOD.get(a['status']) == want]
        if hits:
            h = max(hits, key=lambda a: a['since'] or '')
            cands.append((want, {'ask_id': h['ask_id'], 'bot': h['bot']}))
    if not cands:
        return None, None
    return min(cands, key=lambda c: PRIORITY.index(c[0]))

def tick(log=LOG, net_arg=None, now=None):
    now = now or datetime.now(timezone.utc)
    net = net_arg
    if not net and LAUNCH.exists():
        try: net = json.loads(LAUNCH.read_text()).get('net')
        except ValueError: net = None
    cur = {}
    p = canonical_path('eve')
    if p.exists():
        try: cur = json.loads(p.read_text())
        except ValueError: cur = {}
    hu = _ts(cur.get('hold_until'))
    if hu and hu > now:
        return cur.get('mood'), 'hold-respected', cur.get('ask_id')
    if hu and cur.get('revert_to') and cur.get('mood') != cur['revert_to']:
        # hold expired: apply revert_to atomically to Eve's own file before deriving
        write_state('eve', cur['revert_to'], source='hold-expired', writer='eve:deriver')
        cur = json.loads(p.read_text())
    # A manual set (anything not written by the deriver) stands until a newer relay/queue event.
    if cur.get('source') not in (None, 'derive_eve_state', 'hold-expired') and not (net and in_launch_window(net, now)):
        since = _ts(cur.get('since'))
        ev = [t for r in rows(log) for t in (_ts(r.get('sent_at')), _ts(r.get('answered_at'))) if t]
        qe = ok_queue.newest_event(path=queue_path())
        if qe: ev.append(qe)
        if since and (not ev or max(ev) <= since):
            return cur.get('mood'), 'manual-respected', cur.get('ask_id')
    want, row = derive(log, net, now)
    ask = (row or {}).get('ask_id'); bot = (row or {}).get('bot')
    if want and (want != cur.get('mood') or ask != cur.get('ask_id')):
        write_state('eve', want, source='derive_eve_state', ask_id=ask, bot=bot, writer='eve:deriver')
        return want, 'wrote', ask
    if not want and cur.get('mood') in DERIVED:
        write_state('eve', 'idle', source='derive_eve_state', writer='eve:deriver')
        return 'idle', 'cleared', None
    return cur.get('mood'), 'unchanged', cur.get('ask_id')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', type=Path, default=LOG); ap.add_argument('--net')
    ap.add_argument('--loop', type=float); ap.add_argument('--once', action='store_true')
    a = ap.parse_args()
    while True:
        print(datetime.now().isoformat(timespec='seconds'), *tick(a.log, a.net)); sys.stdout.flush()
        if not a.loop: break
        time.sleep(a.loop)
