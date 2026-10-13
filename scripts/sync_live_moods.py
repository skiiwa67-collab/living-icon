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
import mood_sources as ms, set_mood as sm, ok_queue as okq

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

def main(now=None, queue_path=None):
    now = now or datetime.now(timezone.utc)
    m = ms.load_map(); changed = []
    waiting = okq.waiting_by_slug(okq.active(now=now, path=queue_path), okq.name_map(m))
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
        if lrec != base:
            sm._atomic(live, base); changed.append(f'{slug}={base.get("mood")}' + ('+waiting' if w else ''))
    if changed:
        print(datetime.now().isoformat(timespec='seconds'), 'synced', ' '.join(changed))
    return changed

if __name__ == '__main__':
    main()
