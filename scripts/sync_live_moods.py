#!/usr/bin/env python3
"""Loop step (inside the approved loop; no new schedule). For every bot (Eve: mirror only):
 1. hold expiry: if hold_until passed and revert_to is set, write revert_to atomically to the bot's own file;
 2. mirror the bot's own file -> docs/status/live/<slug>.json when it changed (mood, voice_state, since, hold fields);
 3. OK-queue overlay: live json gets "waiting": {ask_id, since, status} while the bot has an open ask
    (mood untouched); removed once the ask is approved/denied/withdrawn/stale.
Never replaces a newer live mood with an older/default one. Never writes the OK queue."""
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mood_sources as ms, set_mood as sm, ok_queue as okq, display, sync_avatars
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'docs' / 'dashboard'))

import hashlib, json, os
HASHES = Path('/tmp/living-icon-hashes.json')   # persisted per-tick fingerprints (box-local)

def _h(p):
    try: return hashlib.md5(Path(p).read_bytes()).hexdigest()
    except OSError: return None

KEEP = ('mood', 'voice_state', 'since', 'hold_until', 'revert_to', 'ask_id', 'bot', 'stateModel')

def expire_hold(slug, path, now):
    rec = ms._read(path) if path.exists() else None
    if not rec: return False
    hu = ms._parse(rec.get('hold_until'))
    if hu is None or hu.timestamp() > now.timestamp() or not rec.get('revert_to'):
        return False
    new = dict(rec); old = rec.get('mood')
    new.update(mood=rec['revert_to'], hold_until=None, revert_to=None,
               since=now.isoformat(timespec='microseconds'), source='hold-expired')
    for k in ('updated_at', 'updated'):
        if k in new: new[k] = new['since']
    sm._atomic(path, new); sm.log_write('loop:hold-expiry', slug, old, new['mood'])
    return True

def main(now=None, queue_path=None, write_feeds=True, hashes_path=HASHES, avatars=None, avatar_kw=None):
    now = now or datetime.now(timezone.utc)
    m = ms.load_map(); changed = []
    raw = okq.load_raw(queue_path)
    nmap = okq.name_map(m)
    waiting = okq.waiting_by_slug(okq.active(raw, now=now), nmap)
    okreq = okq.ok_request_by_slug(nmap, now=now, items=raw)
    shown = {}
    for slug, cfg in m['agents'].items():
        src = ms.src_path(cfg); live = ms.LIVE / f'{slug}.json'
        # Eve: derive_eve_state.py owns her mood + hold expiry; here she is only mirrored.
        if slug != 'eve' and src.exists() and expire_hold(slug, src, now):
            changed.append(f'{slug}:reverted')
        lrec = ms._read(live) if live.exists() else None
        cur = ms.read_mood(slug, m)
        if src != live and cur and cur['from'] == 'source':
            srec = ms._read(src) or {}
            base = {k: srec.get(k) for k in KEEP if k in srec}
            base['mood'] = cur['mood']; base['voice_state'] = cur['voice_state']
            base.setdefault('since', datetime.fromtimestamp(cur['ts'], timezone.utc).isoformat(timespec='microseconds'))
            base.update(agent=slug, source='mirror', mirrored_from=str(src), stateModel=cfg['stateModel'])
        elif lrec is not None:
            base = dict(lrec)
        else:
            continue
        w = waiting.get(slug)
        if w: base['waiting'] = w
        else: base.pop('waiting', None)
        base['ok_request'] = okreq.get(slug) or {'state': 'none', 'ask_id': None, 'since': None, 'priority': False}
        dm, why = display.display_mood(cfg, base.get('mood'), base['ok_request'], slug)
        if why: base['display_mood'] = dm; base['display_override'] = why
        else: base.pop('display_mood', None); base.pop('display_override', None)
        shown[slug] = (dm, base.get('voice_state') or 'idle')
        if lrec != base:
            sm._atomic(live, base); changed.append(f'{slug}={base.get("mood")}' + ('+waiting' if w else ''))
    if avatars is None: avatars = os.environ.get('LI_AVATAR_WRITE') == '1'
    # OFF by default: the app restores avatar.png from its own copy within ~2 s (2026-10-14 test),
    # so a plain file write is not honored; the owning bot must call update_state avatar set.
    if avatars:   # chat avatar follows the displayed mood (writes only on change)
        for s_ in sync_avatars.sync(m, shown, **(avatar_kw or {})): changed.append(f'avatar:{s_}')
    # F10: fingerprint every source + live file; any change (incl. bots whose source IS live/) rebuilds feeds.
    try: prev = json.loads(hashes_path.read_text())
    except (OSError, ValueError): prev = {}
    cur_h = {}
    for slug, cfg in m['agents'].items():
        for p in {str(ms.src_path(cfg)), str(ms.LIVE / f'{slug}.json')}:
            cur_h[p] = _h(p)
    for p, h in cur_h.items():
        if prev.get(p) != h:
            changed.append(f'hash:{p}')
    if cur_h != prev:
        try: sm._atomic(hashes_path, cur_h)
        except OSError: pass
    if changed:
        print(datetime.now(timezone.utc).isoformat(timespec='seconds'), 'synced', ' '.join(changed))
        if write_feeds:   # feed lag fix: rebuild data.json + both feed.json (atomic) on any change
            try:
                import refresh_data; refresh_data.main()
            except Exception as e:
                print('feed refresh failed:', e)
    return changed

if __name__ == '__main__':
    main()
