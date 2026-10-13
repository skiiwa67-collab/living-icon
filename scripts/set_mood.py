#!/usr/bin/env python3
"""Set an agent's live Living Icon mood (Helios spec 2026-10-13).
usage: set_mood.py <agent> <mood> [--hold SECONDS] [--revert MOOD] [--source TEXT] [--ask-id ID] [--bot NAME]
Canonical (single source of truth): /workspace/agent-backups/Eve/mood-state.json,
written atomically (temp+rename). docs/status/live/<agent>.json is a mirror copy
for dashboard serving only. Fields: mood, since, ask_id, bot, source (+ hold_until, revert_to)."""
import argparse, json, os, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
LIVE = Path(__file__).resolve().parents[1] / 'docs' / 'status' / 'live'
CANON = {'eve': Path('/workspace/agent-backups/Eve/mood-state.json')}
STATES = {'eve': ['idle','listening','thinking','relay-active','happy','waiting-parked','launch-dnd','frustrated']}
DEFAULT_HOLD = {'frustrated': 5, 'happy': 4}

def _atomic(path, rec):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name, suffix='.tmp')
    with os.fdopen(fd, 'w') as f:
        json.dump(rec, f, indent=2); f.write('\n')
        f.flush(); os.fsync(f.fileno())
    os.chmod(tmp, 0o644)              # mkstemp is 0600; dashboard must read it
    os.replace(tmp, path)

def canonical_path(agent):
    return CANON.get(agent, LIVE / f'{agent}.json')

def write_state(agent, mood, hold=None, revert='idle', source='cli', ask_id=None, bot=None):
    allowed = STATES.get(agent)
    if allowed and mood not in allowed:
        raise SystemExit(f'unknown mood {mood!r} for {agent}; allowed: {allowed}')
    if hold is None:
        hold = DEFAULT_HOLD.get(mood)
    now = datetime.now(timezone.utc)
    rec = {'mood': mood, 'since': now.isoformat(timespec='seconds'), 'ask_id': ask_id, 'bot': bot,
           'source': source, 'agent': agent,
           'hold_until': (now + timedelta(seconds=hold)).isoformat(timespec='seconds') if hold else None,
           'revert_to': revert if hold else None}
    _atomic(canonical_path(agent), rec)   # source of truth first
    sync_mirror(agent)
    return rec

def sync_mirror(agent):
    """Copy canonical -> docs/status/live/<agent>.json (dashboard serving copy)."""
    src = canonical_path(agent)
    if src != LIVE / f'{agent}.json' and src.exists():
        _atomic(LIVE / f'{agent}.json', json.loads(src.read_text()))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('agent'); ap.add_argument('mood', nargs='?')
    ap.add_argument('--hold', type=float); ap.add_argument('--revert', default='idle')
    ap.add_argument('--source', default='cli'); ap.add_argument('--ask-id'); ap.add_argument('--bot')
    ap.add_argument('--sync-only', action='store_true', help='just mirror canonical -> docs/status/live')
    a = ap.parse_args()
    if a.sync_only:
        sync_mirror(a.agent); print('synced')
    else:
        if not a.mood: ap.error('mood required')
        print(json.dumps(write_state(a.agent, a.mood, a.hold, a.revert, a.source, a.ask_id, a.bot)))
