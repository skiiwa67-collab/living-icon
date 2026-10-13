#!/usr/bin/env python3
"""Set an agent's live Living Icon state.
usage: set_mood.py <agent> <state> [--hold SECONDS] [--revert STATE] [--source TEXT]
Writes docs/status/live/<agent>.json atomically. With --hold, the dashboard
shows <state> until hold_until, then shows revert_to (default idle)."""
import argparse, json, os, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
LIVE = Path(__file__).resolve().parents[1] / 'docs' / 'status' / 'live'
STATES = {'eve': ['idle','listening','thinking','relay-active','happy','waiting-parked','launch-DND','frustrated']}
DEFAULT_HOLD = {'frustrated': 5, 'happy': 4}

def write_state(agent, state, hold=None, revert='idle', source='cli'):
    allowed = STATES.get(agent)
    if allowed and state not in allowed:
        raise SystemExit(f'unknown state {state!r} for {agent}; allowed: {allowed}')
    if hold is None:
        hold = DEFAULT_HOLD.get(state)
    now = datetime.now(timezone.utc)
    rec = {'agent': agent, 'state': state, 'since': now.isoformat(timespec='seconds'),
           'hold_until': (now + timedelta(seconds=hold)).isoformat(timespec='seconds') if hold else None,
           'revert_to': revert if hold else None, 'source': source}
    LIVE.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=LIVE, suffix='.tmp')
    with os.fdopen(fd, 'w') as f:
        json.dump(rec, f, indent=2); f.write('\n')
    os.replace(tmp, LIVE / f'{agent}.json')
    return rec

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('agent'); ap.add_argument('state')
    ap.add_argument('--hold', type=float); ap.add_argument('--revert', default='idle')
    ap.add_argument('--source', default='cli')
    a = ap.parse_args()
    print(json.dumps(write_state(a.agent, a.state, a.hold, a.revert, a.source)))
