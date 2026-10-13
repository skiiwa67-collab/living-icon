#!/usr/bin/env python3
"""Set an agent's live Living Icon mood. Box-local only (no GitHub/Notion/Dropbox).
usage: set_mood.py <agent-slug> <mood> [--hold SECONDS] [--revert MOOD] [--source TEXT] [--ask-id ID] [--bot NAME]
Roster + stateModel come from docs/status/mood-sources.json (12 bots, no group rooms).
Eve (flat 8 moods): canonical /workspace/agent-backups/Eve/mood-state.json, mirrored to docs/status/live/eve.json.
Everyone else (matrix moods): writes the bot's own box file from the mapping (merged, keeps its
schema) atomically, then mirrors to docs/status/live/<slug>.json for the dashboard."""
import argparse, json, os, sys, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mood_sources as ms
LIVE = ms.LIVE
_M = ms.load_map()
# Each bot's own box file (from docs/status/mood-sources.json); live/<slug>.json when it has none.
CANON = {s: ms.src_path(c) for s, c in _M['agents'].items()}
STATES = {s: (_M['flat_moods'] if c['stateModel'] == 'flat' else _M['matrix_moods']) for s, c in _M['agents'].items()}
DEFAULT = {s: ('idle' if c['stateModel'] == 'flat' else 'calm') for s, c in _M['agents'].items()}
DEFAULT_HOLD = {'frustrated': 5, 'happy': 4}

def _atomic(path, rec):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name, suffix='.tmp')
    with os.fdopen(fd, 'w') as f:
        json.dump(rec, f, indent=2); f.write('\n')
        f.flush(); os.fsync(f.fileno())
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)

def canonical_path(agent):
    return CANON.get(agent, LIVE / f'{agent}.json')

def write_state(agent, mood, hold=None, revert=None, source='cli', ask_id=None, bot=None, voice_state=None):
    if agent not in STATES:
        raise SystemExit(f'unknown agent {agent!r}; roster: {sorted(STATES)}')
    allowed = STATES[agent]
    if mood not in allowed:
        raise SystemExit(f'unknown mood {mood!r} for {agent}; allowed: {allowed}')
    revert = revert or DEFAULT[agent]
    if hold is None and agent == 'eve':
        hold = DEFAULT_HOLD.get(mood)
    now = datetime.now(timezone.utc)
    rec = {'mood': mood, 'since': now.isoformat(timespec='seconds'), 'ask_id': ask_id, 'bot': bot,
           'source': source, 'agent': agent, 'stateModel': _M['agents'][agent]['stateModel'],
           'hold_until': (now + timedelta(seconds=hold)).isoformat(timespec='seconds') if hold else None,
           'revert_to': revert if hold else None}
    path = canonical_path(agent)
    old = ms._read(path) if path.exists() else None
    out = dict(old or {})          # keep the bot's own schema/extra keys
    out.update(rec)
    for k in ('updated_at', 'updated'):   # bots that timestamp with these keys
        if k in out: out[k] = rec['since']
    if voice_state: out['voice_state'] = voice_state
    _atomic(path, out)
    sync_mirror(agent)
    return out

def sync_mirror(agent):
    src = canonical_path(agent)
    if src != LIVE / f'{agent}.json' and src.exists():
        _atomic(LIVE / f'{agent}.json', json.loads(src.read_text()))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('agent'); ap.add_argument('mood', nargs='?')
    ap.add_argument('--hold', type=float); ap.add_argument('--revert')
    ap.add_argument('--source', default='cli'); ap.add_argument('--ask-id'); ap.add_argument('--bot'); ap.add_argument('--voice')
    ap.add_argument('--sync-only', action='store_true')
    a = ap.parse_args()
    if a.sync_only:
        sync_mirror(a.agent); print('synced')
    else:
        if not a.mood: ap.error('mood required')
        print(json.dumps(write_state(a.agent, a.mood, a.hold, a.revert, a.source, a.ask_id, a.bot, a.voice)))
