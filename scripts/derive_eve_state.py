#!/usr/bin/env python3
"""Derive Eve's live state from Helios's relay log (READ-ONLY) + optional launch window.
usage: derive_eve_state.py [--log PATH] [--net ISO8601] [--once | --loop SECONDS]
Priority: launch-DND > waiting-parked > relay-active > (leave manual state alone).
Only overwrites eve.json when a derived state applies, or to clear a derived
state back to idle once its condition ends; never overrides a live hold."""
import argparse, json, time, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from set_mood import write_state, LIVE
LOG = Path('/workspace/agent-backups/Helios/eve-relay/relay-log.jsonl')
LAUNCH = LIVE / 'launch.json'   # optional {"net": "ISO8601"} written by a launch watcher
GO_BEFORE, WATCH_AFTER = 30 * 60, 60 * 60   # NET-30min .. NET+60min (WATCH_AFTER_NET_SEC)
DERIVED = {'relay-active', 'waiting-parked', 'launch-DND'}

def rows(path):
    if not path.exists(): return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            try: out.append(json.loads(line))
            except ValueError: pass
    return out

def derive(log, net, now):
    if net:
        t = (datetime.fromisoformat(net.replace('Z', '+00:00')) - now).total_seconds()
        if -WATCH_AFTER < t <= GO_BEFORE: return 'launch-DND'
    rs = rows(log)
    if any(r.get('status') == 'yes-held-for-card' or (r.get('parked_at') and not r.get('card_result')) for r in rs):
        return 'waiting-parked'
    if any(r.get('status') in ('sent', 'pending') and r.get('answer') in (None, '', 'null') for r in rs):
        return 'relay-active'
    return None

def tick(log, net_arg):
    now = datetime.now(timezone.utc)
    net = net_arg
    if not net and LAUNCH.exists():
        try: net = json.loads(LAUNCH.read_text()).get('net')
        except ValueError: net = None
    cur = {}
    p = LIVE / 'eve.json'
    if p.exists():
        try: cur = json.loads(p.read_text())
        except ValueError: cur = {}
    hu = cur.get('hold_until')
    if hu and datetime.fromisoformat(hu) > now:
        return cur.get('state'), 'hold-respected'
    want = derive(log, net, now)
    if want and want != cur.get('state'):
        write_state('eve', want, source='derive_eve_state'); return want, 'wrote'
    if not want and cur.get('state') in DERIVED:
        write_state('eve', 'idle', source='derive_eve_state'); return 'idle', 'cleared'
    return cur.get('state'), 'unchanged'

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', type=Path, default=LOG); ap.add_argument('--net')
    ap.add_argument('--loop', type=float); ap.add_argument('--once', action='store_true')
    a = ap.parse_args()
    while True:
        print(*tick(a.log, a.net)); sys.stdout.flush()
        if not a.loop: break
        time.sleep(a.loop)
