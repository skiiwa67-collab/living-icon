#!/usr/bin/env python3
"""Regenerate Living Icon stall dashboard data.json Soft-PASS."""
import json, hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]  # living-icon
AGENTS = Path('/home/box/agent-data/agents')
PACKAGES = ROOT / 'packages'
OUT = Path(__file__).resolve().parent / 'data.json'

SLUG = {
    'Ada': 'ada-happy',
    'Da Vinci': 'da-vinci-happy',
    'Helios': 'helios-happy',
    'Elon Musk #1 (Advisor) copy': 'helios-happy',
    'Saxon': 'saxon-happy',
    'Skippy the Magnificent': 'skippy-happy',
    'tinkabot': 'tinkabot-happy',
}

def md5(p: Path):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(65536), b''):
            h.update(c)
    return h.hexdigest()

def main():
    now = datetime.now(timezone.utc)
    rows = []
    for d in sorted(AGENTS.iterdir()):
        if not d.is_dir() or not (d / 'profile.json').exists():
            continue
        try:
            p = json.loads((d / 'profile.json').read_text())
        except Exception:
            continue
        name = p.get('name') or d.name[:8]
        avatar = next((d / c for c in ('avatar.gif','avatar.png','avatar.jpg','avatar.webp') if (d / c).exists() and (d / c).stat().st_size > 0), None)
        av_mtime = datetime.fromtimestamp(avatar.stat().st_mtime, timezone.utc) if avatar else None
        stall_h = ((now - av_mtime).total_seconds() / 3600) if av_mtime else None

        growth = {'status': 'Soft-FAIL frozen', 'note': 'no personality.json'}
        mood = None
        voice_state = None
        pers = d / 'personality.json'
        if pers.exists():
            try:
                pdata = json.loads(pers.read_text())
                pm = datetime.fromtimestamp(pers.stat().st_mtime, timezone.utc)
                mood_obj = pdata.get('mood')
                if isinstance(mood_obj, dict):
                    mood = mood_obj.get('current')
                else:
                    mood = mood_obj
                voice_state = pdata.get('voice_state')
                growth = {
                    'status': 'Soft-PASS',
                    'path': str(pers),
                    'mtime': pm.isoformat(),
                    'age_hours': round((now - pm).total_seconds() / 3600, 2),
                    'traits': pdata.get('traits'),
                    'drift_enabled': (pdata.get('drift') or {}).get('enabled'),
                    'avatar_resolve': pdata.get('avatar_resolve'),
                }
            except Exception as e:
                growth = {'status': 'Soft-FAIL', 'note': str(e)}

        pkg = SLUG.get(name)
        softpass_path = None
        softpass_rel = None
        softpass_md5 = None
        softpass_mtime = None
        matrix_rel = None
        if pkg:
            sp = PACKAGES / pkg / 'softpass' / 'avatar-idle.gif'
            if sp.exists():
                softpass_path = str(sp)
                softpass_rel = f"avatars/{pkg[:-6] if pkg.endswith('-happy') else pkg}.gif"
                softpass_md5 = md5(sp)
                softpass_mtime = datetime.fromtimestamp(sp.stat().st_mtime, timezone.utc).isoformat()
            vs = voice_state or 'idle'
            m = mood or 'calm'
            mg = PACKAGES / pkg / 'matrix' / vs / f'{m}.gif'
            if not mg.exists():
                mg = PACKAGES / pkg / 'matrix' / 'idle' / f'{m}.gif'
            if not mg.exists():
                mg = PACKAGES / pkg / 'matrix' / 'idle' / 'calm.gif'
            if mg.exists():
                matrix_rel = f"avatars/{pkg[:-6] if pkg.endswith('-happy') else pkg}.gif"

        if stall_h is None:
            stall_flag = 'Soft-FAIL no avatar'
        elif stall_h >= 24:
            stall_flag = 'Soft-FAIL stall ≥24h'
        elif stall_h >= 12:
            stall_flag = 'Soft-FAIL stall ≥12h'
        elif stall_h >= 1:
            stall_flag = 'Soft-PASS aging'
        else:
            stall_flag = 'Soft-PASS fresh'

        rows.append({
            'name': name,
            'agent_id': d.name,
            'title': p.get('title') or '',
            'in_fleet': bool(pkg),
            'package': pkg,
            'mood': mood,
            'voice_state': voice_state,
            'avatar_path': str(avatar) if avatar else None,
            'avatar_md5': md5(avatar) if avatar else None,
            'avatar_mtime': av_mtime.isoformat() if av_mtime else None,
            'stall_hours': round(stall_h, 2) if stall_h is not None else None,
            'stall_flag': stall_flag,
            'softpass_path': softpass_path,
            'softpass_rel': softpass_rel,
            'softpass_md5': softpass_md5,
            'softpass_mtime': softpass_mtime,
            'matrix_rel': matrix_rel,
            'active_animation': matrix_rel or softpass_rel,
            'growth': growth,
        })

    out = {
        'schema': 'living-icon-stall-dashboard/v1',
        'generated_at': now.isoformat(),
        'generated_at_ct': datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z'),
        'thresholds_hours': {'aging': 1, 'stall_soft': 12, 'stall_hard': 24},
        'roster': rows,
        'fleet_only_note': 'Living Icon Soft-PASS packs under packages/*-happy/',
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(f'Wrote {OUT} ({len(rows)} agents)')

if __name__ == '__main__':
    main()
