#!/usr/bin/env python3
"""Box-local mood source reader (no network). Never writes a bot's own source file."""
import json, os
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / 'docs' / 'status' / 'mood-sources.json'
LIVE = ROOT / 'docs' / 'status' / 'live'

def load_map():
    return json.loads(MAP.read_text())

def src_path(cfg):
    p = Path(cfg['source'])
    return p if p.is_absolute() else ROOT / p

def _ts(rec, path):
    for k in ('since', 'updated_at', 'updated'):
        v = rec.get(k)
        if isinstance(v, str):
            try:
                v2 = v[:-2] + ':' + v[-2:] if len(v) > 5 and v[-5] in '+-' and v[-3] != ':' else v
                d = datetime.fromisoformat(v2.replace('Z', '+00:00'))
                if d.tzinfo is None:
                    d = d.astimezone()  # naive = box-local
                return d.timestamp()
            except Exception:
                pass
    return path.stat().st_mtime

def _read(path):
    try:
        rec = json.loads(path.read_text())
        return rec if isinstance(rec, dict) else None
    except Exception:
        return None

def normalize(slug, cfg, rec, allowed):
    mood = rec.get('mood')
    if isinstance(mood, dict):
        mood = mood.get('current')
    mood = (cfg.get('flat_map') or {}).get(mood, mood)
    if isinstance(mood, str) and cfg['stateModel'] == 'flat':
        mood = mood.lower()
    return mood if mood in allowed else None

def read_mood(slug, m=None):
    """-> dict(mood, voice_state, from, path, ts) or None when no usable file."""
    m = m or load_map()
    cfg = m['agents'][slug]
    allowed = m['flat_moods'] if cfg['stateModel'] == 'flat' else m['matrix_moods']
    best = None
    for path in {src_path(cfg), LIVE / f'{slug}.json'}:
        if not path.exists():
            continue
        rec = _read(path)
        if not rec:
            continue
        mood = normalize(slug, cfg, rec, allowed)
        if not mood:
            continue
        cand = {'mood': mood, 'voice_state': rec.get('voice_state') or 'idle',
                'from': 'source' if path == src_path(cfg) else 'live', 'path': str(path), 'ts': _ts(rec, path)}
        if best is None or cand['ts'] > best['ts']:
            best = cand
    return best

if __name__ == '__main__':
    m = load_map()
    for s in m['agents']:
        print(s, read_mood(s, m))
