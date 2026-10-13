#!/usr/bin/env python3
"""Loop step (no new schedule): mirror each non-Eve bot's own box mood file into
docs/status/live/<slug>.json, only when the source is newer than the live file.
Never writes a bot's source file; never replaces a newer live mood with an older/default one."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mood_sources as ms, set_mood as sm
import json
from datetime import datetime, timezone

def main():
    m = ms.load_map(); changed = []
    for slug, cfg in m['agents'].items():
        if slug == 'eve':
            continue  # handled by derive_eve_state.py
        src = ms.src_path(cfg); live = ms.LIVE / f'{slug}.json'
        if src == live or not src.exists():
            continue
        cur = ms.read_mood(slug, m)
        if not cur or cur['from'] != 'source':
            continue
        lrec = ms._read(live) if live.exists() else None
        if lrec and lrec.get('mood') == cur['mood'] and lrec.get('mirrored_from') == str(src):
            continue
        rec = {'mood': cur['mood'], 'voice_state': cur['voice_state'], 'agent': slug,
               'since': datetime.fromtimestamp(cur['ts'], timezone.utc).isoformat(timespec='seconds'),
               'source': 'mirror', 'mirrored_from': str(src), 'stateModel': cfg['stateModel'],
               'hold_until': None, 'revert_to': None}
        sm._atomic(live, rec); changed.append(f'{slug}={cur["mood"]}')
    if changed:
        print(datetime.now().isoformat(timespec='seconds'), 'synced', ' '.join(changed))

if __name__ == '__main__':
    main()
