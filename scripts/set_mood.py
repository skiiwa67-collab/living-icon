#!/usr/bin/env python3
"""Set a bot's live Living Icon mood. Box-local only (no GitHub/Notion/Dropbox).
usage: set_mood.py <slug> <mood> --as <slug> [--test] [--voice V] [--hold S] [--revert MOOD] [--source T] [--ask-id ID] [--bot NAME]
Roster/stateModel/source path: docs/status/mood-sources.json (12 bots, no group rooms).
A bot may only write its own slot (--as must equal <slug>) unless --test is given.
Writes the bot's own source file atomically (merged, keeps its schema), mirrors to
docs/status/live/<slug>.json, and appends to /workspace/agent-backups/Team/mood-writes.log."""
import argparse, json, os, sys, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mood_sources as ms
LIVE = ms.LIVE
WRITE_LOG = Path('/workspace/agent-backups/Team/mood-writes.log')
_M = ms.load_map()
CANON = {s: ms.src_path(c) for s, c in _M['agents'].items()}
STATES = {s: (_M['flat_moods'] if c['stateModel'] == 'flat' else _M['matrix_moods']) for s, c in _M['agents'].items()}
DEFAULT = {s: ('idle' if c['stateModel'] == 'flat' else 'calm') for s, c in _M['agents'].items()}
DEFAULT_HOLD = {'eve': {'frustrated': 5, 'happy': 4}}
VOICES = ('idle', 'listening', 'talking')

def _atomic(path, rec):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name, suffix='.tmp')
    with os.fdopen(fd, 'w') as f:
        json.dump(rec, f, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)

def log_write(writer, target, old, new):
    try:
        WRITE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(WRITE_LOG, 'a') as f:
            f.write(json.dumps({'ts': datetime.now(timezone.utc).isoformat(timespec='microseconds'),
                                'writer': writer, 'target': target, 'old': old, 'new': new}) + '\n')
    except OSError:
        pass

def canonical_path(agent):
    return CANON.get(agent, LIVE / f'{agent}.json')

def write_state(agent, mood, hold=None, revert=None, source='cli', ask_id=None, bot=None,
                voice_state=None, writer=None):
    if agent not in STATES:
        raise SystemExit(f'unknown agent {agent!r}; roster: {sorted(STATES)}')
    if mood not in STATES[agent]:
        raise SystemExit(f'unknown mood {mood!r} for {agent}; allowed: {STATES[agent]}')
    if voice_state and voice_state not in VOICES:
        raise SystemExit(f'unknown voice {voice_state!r}; allowed: {VOICES}')
    revert = revert or DEFAULT[agent]
    if hold is None:
        hold = DEFAULT_HOLD.get(agent, {}).get(mood)
    now = datetime.now(timezone.utc)
    rec = {'mood': mood, 'since': now.isoformat(timespec='microseconds'), 'ask_id': ask_id, 'bot': bot,
           'source': source, 'agent': agent, 'stateModel': _M['agents'][agent]['stateModel'],
           'hold_until': (now + timedelta(seconds=hold)).isoformat(timespec='microseconds') if hold else None,
           'revert_to': revert if hold else None}
    path = canonical_path(agent)
    old = ms._read(path) if path.exists() else None
    out = dict(old or {})
    out.update(rec)
    for k in ('updated_at', 'updated'):
        if k in out: out[k] = rec['since']
    if voice_state: out['voice_state'] = voice_state
    _atomic(path, out)
    sync_mirror(agent)
    log_write(writer or agent, agent, (old or {}).get('mood'), mood)
    return out

def sync_mirror(agent):
    src = canonical_path(agent)
    if src != LIVE / f'{agent}.json' and src.exists():
        rec = json.loads(src.read_text())
        prev = ms._read(LIVE / f'{agent}.json') or {}
        if 'waiting' in prev: rec.setdefault('waiting', prev['waiting'])   # keep OK-queue overlay
        _atomic(LIVE / f'{agent}.json', rec)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('agent'); ap.add_argument('mood', nargs='?')
    ap.add_argument('--as', dest='as_bot', help='slug of the bot doing the write (must equal agent)')
    ap.add_argument('--test', action='store_true', help='allow writing another bot\'s slot (tests only)')
    ap.add_argument('--voice'); ap.add_argument('--hold', type=float); ap.add_argument('--revert')
    ap.add_argument('--source', default='cli'); ap.add_argument('--ask-id'); ap.add_argument('--bot')
    ap.add_argument('--sync-only', action='store_true')
    a = ap.parse_args()
    if a.sync_only:
        sync_mirror(a.agent); print('synced'); sys.exit(0)
    if not a.mood: ap.error('mood required')
    if a.as_bot != a.agent and not a.test:
        ap.error(f'refused: --as {a.as_bot!r} may not write {a.agent!r} (a bot writes only its own slot; use --test for tests)')
    writer = a.as_bot or 'test'
    if a.test and a.as_bot != a.agent: writer = f'test:{a.as_bot or "anon"}'
    print(json.dumps(write_state(a.agent, a.mood, a.hold, a.revert, a.source, a.ask_id, a.bot, a.voice, writer)))
