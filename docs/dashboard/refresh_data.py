#!/usr/bin/env python3
"""Regenerate the Living Icon dashboard data.json AND both status feeds (box-local only).
- roster = docs/status/mood-sources.json (12 bots; group rooms are not bots)
- mood   = live box mood file (scripts/mood_sources.read_mood); personality.json default only when none
- art    = actually-live file from scripts/art.resolve (voice->idle, mood->calm fallback)
- waiting/open asks from the OK queue (read-only)
All writes atomic (temp + rename)."""
import json, hashlib, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import mood_sources, art, ok_queue
from set_mood import _atomic
AGENTS = Path('/home/box/agent-data/agents')
OUT = Path(__file__).resolve().parent / 'data.json'
FEEDS = [ROOT / 'docs' / 'status' / 'feed.json', ROOT / 'status' / 'feed.json']
STALE_S = 21600

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(65536), b''): h.update(c)
    return h.hexdigest()

def iso(ts): return datetime.fromtimestamp(ts, timezone.utc).isoformat()   # UTC ISO everywhere

def build_row(slug, cfg, now, waiting, okreq=None):
    d = AGENTS / cfg['id']
    prof = {}
    try: prof = json.loads((d / 'profile.json').read_text())
    except (OSError, ValueError): pass
    avatar = next((d / c for c in ('avatar.gif', 'avatar.png', 'avatar.jpg', 'avatar.webp')
                   if (d / c).exists() and (d / c).stat().st_size > 0), None)
    av_mtime = avatar.stat().st_mtime if avatar else None
    stall_h = (now.timestamp() - av_mtime) / 3600 if av_mtime else None
    growth = {'status': 'Soft-FAIL frozen', 'note': 'no personality.json'}
    mood = voice = None
    pers = next((p for p in (d / 'personality.json', ROOT / cfg['art_dir'] / 'personality.json') if p.exists()), None)
    if pers:
        try:
            pd = json.loads(pers.read_text())
            mo = pd.get('mood'); mood = mo.get('current') if isinstance(mo, dict) else (mo if isinstance(mo, str) else None)
            voice = pd.get('voice_state')
            pm = pers.stat().st_mtime
            growth = {'status': 'Soft-PASS', 'path': str(pers), 'mtime': iso(pm),
                      'age_hours': round((now.timestamp() - pm) / 3600, 2), 'traits': pd.get('traits'),
                      'drift_enabled': (pd.get('drift') or {}).get('enabled'), 'avatar_resolve': pd.get('avatar_resolve')}
        except (OSError, ValueError) as e:
            growth = {'status': 'Soft-FAIL', 'note': str(e)}
    mood_from = 'personality.json default' if mood else None
    live = None
    try: live = mood_sources.read_mood(slug)
    except Exception: pass
    if live:   # live box mood wins; personality default only when no live file
        mood, voice, mood_from = live['mood'], live['voice_state'], live['path']
    if mood not in (mood_sources.load_map()['flat_moods'] if cfg['stateModel'] == 'flat' else mood_sources.load_map()['matrix_moods']):
        mood = None
    live_art = art.resolve(cfg, mood, voice or 'idle')
    sp = ROOT / cfg['art_dir'] / 'softpass' / 'avatar-idle.gif'
    flag = ('Soft-FAIL no avatar' if stall_h is None else 'Soft-FAIL stall ≥24h' if stall_h >= 24 else
            'Soft-FAIL stall ≥12h' if stall_h >= 12 else 'Soft-PASS aging' if stall_h >= 1 else 'Soft-PASS fresh')
    return {
        'name': cfg['name'], 'slug': slug, 'agent_id': cfg['id'], 'title': prof.get('title') or '',
        'in_fleet': True, 'package': Path(cfg['art_dir']).name, 'stateModel': cfg['stateModel'],
        'mood': mood, 'voice_state': voice, 'mood_from': mood_from,
        'mood_since': iso(live['ts']) if live else None,
        'avatar_path': str(avatar) if avatar else None, 'avatar_md5': md5(avatar) if avatar else None,
        'avatar_mtime': iso(av_mtime) if av_mtime else None,
        'stall_hours': round(stall_h, 2) if stall_h is not None else None, 'stall_flag': flag,
        'softpass_path': str(sp) if sp.exists() else None,
        'live_art': live_art, 'live_art_md5': md5(ROOT / live_art) if live_art else None,
        'live_art_mtime': iso((ROOT / live_art).stat().st_mtime) if live_art else None,
        'active_animation': live_art,
        'art_inventory': art.inventory(cfg),
        'waiting': waiting.get(slug),
        'ok_request': (okreq or {}).get(slug) or {'state': 'none', 'ask_id': None, 'since': None, 'priority': False},
        'growth': growth,
    }

def update_feed(path, rows, now, open_asks):
    try: feed = json.loads(path.read_text())
    except (OSError, ValueError): feed = {'schema': 'living-icon-status-feed/v1', 'agents': []}
    feed['updated_at'] = now.isoformat()
    feed['stale_threshold_seconds'] = feed.get('stale_threshold_seconds', STALE_S)
    feed['generator'] = 'docs/dashboard/refresh_data.py (box-local, every loop refresh)'
    feed['open_asks'] = open_asks
    by = {a.get('agent'): a for a in feed.get('agents', []) if isinstance(a, dict)}
    out = []
    for r in rows:
        a = by.get(r['slug'], {'agent': r['slug']})
        # stuck = mood changed after the installed sidebar avatar and the avatar hasn't caught up
        stuck = 0.0
        if r['avatar_mtime'] and r['mood_since'] and r['live_art_md5'] and r['avatar_md5'] != r['live_art_md5']:
            ms_, av = datetime.fromisoformat(r['mood_since']), datetime.fromisoformat(r['avatar_mtime'])
            if av < ms_: stuck = round((now - ms_).total_seconds(), 3)
        a.update(mood=r['mood'] or 'unreported', voice_state=r['voice_state'] or 'idle',
                 stateModel=r['stateModel'], mood_source=r['mood_from'], mood_since=r['mood_since'],
                 gif_path=r['live_art'], gif_md5=r['live_art_md5'], gif_mtime=r['live_art_mtime'],
                 installed_avatar_path=r['avatar_path'], installed_avatar_md5=r['avatar_md5'],
                 installed_avatar_mtime=r['avatar_mtime'],
                 stuck_seconds=stuck, stuck_softfail=stuck > feed['stale_threshold_seconds'],
                 waiting=r['waiting'], ok_request=r['ok_request'], checked_at=now.isoformat())
        out.append(a)
    feed['agents'] = out
    _atomic(path, feed)

def main():
    now = datetime.now(timezone.utc)
    m = mood_sources.load_map()
    act = ok_queue.active(now=now)
    waiting = ok_queue.waiting_by_slug(act, ok_queue.name_map(m))
    okreq = ok_queue.ok_request_by_slug(ok_queue.name_map(m), now=now)
    rows = [build_row(s, c, now, waiting, okreq) for s, c in m['agents'].items()]
    open_asks = len(act)
    out = {'schema': 'living-icon-stall-dashboard/v2', 'generated_at': now.isoformat(),
           'thresholds_hours': {'aging': 1, 'stall_soft': 12, 'stall_hard': 24},
           'open_asks': open_asks, 'asks': act, 'roster': rows,
           'fleet_only_note': 'Roster = docs/status/mood-sources.json; art from <art_dir> on the box'}
    _atomic(OUT, out)
    for f in FEEDS: update_feed(f, rows, now, open_asks)
    print(f'Wrote {OUT} + {len(FEEDS)} feeds ({len(rows)} agents, {open_asks} open asks)')

if __name__ == '__main__':
    main()
