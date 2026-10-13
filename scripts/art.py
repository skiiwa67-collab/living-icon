#!/usr/bin/env python3
"""Resolve the box-local art file for (bot, mood, voice). Repo-relative paths only.
Layouts tried per art_dir: flat states/<mood>.gif (Eve), matrix/<voice>/<mood>.{gif,png},
matrix/<mood>-<voice>.{gif,png}. Fallback: voice -> idle, then mood -> calm (calm-idle)."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXTS = ('.gif', '.png')
FLAT_ART = {'launch-dnd': 'launch-DND'}

def candidates(art_dir, model, mood, voice, default):
    if model == 'flat':
        for m in (mood, default):
            for e in EXTS:
                yield f'{art_dir}/states/{FLAT_ART.get(m, m)}{e}'
        return
    for m, v in ((mood, voice), (mood, 'idle'), (default, voice), (default, 'idle')):
        for e in EXTS:
            yield f'{art_dir}/matrix/{v}/{m}{e}'
            yield f'{art_dir}/matrix/{m}-{v}{e}'

def resolve(cfg, mood, voice='idle', root=ROOT):
    model = cfg.get('stateModel', 'matrix')
    default = 'idle' if model == 'flat' else 'calm'
    art_dir = cfg.get('art_dir')
    if not art_dir:
        return None
    for rel in candidates(art_dir.rstrip('/'), model, mood or default, voice or 'idle', default):
        if (root / rel).is_file():
            return rel
    return None

def inventory(cfg, root=ROOT):
    """All art files under art_dir (repo-relative) so the dashboard can apply the same fallback."""
    d = cfg.get('art_dir')
    if not d or not (root / d).is_dir():
        return []
    return sorted(str(p.relative_to(root)) for p in (root / d).rglob('*')
                  if p.suffix in EXTS and p.is_file() and '/archive' not in str(p) and not p.name.endswith('-still.png'))
