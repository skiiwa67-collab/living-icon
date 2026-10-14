#!/usr/bin/env python3
"""Chat avatar follows the displayed mood (Chris-approved 2026-10-14).
On change, write a still (first frame) of the bot's current mood art to
/home/box/agent-data/agents/<id>/avatar.png atomically. One-time backup avatar.orig.png. Never deletes."""
import io, json, os, shutil, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import art
AGENTS = Path('/home/box/agent-data/agents')
STATE = Path('/tmp/living-icon-avatars.json')

def still_png(src):
    from PIL import Image
    im = Image.open(src); im.seek(0)
    buf = io.BytesIO(); im.convert('RGBA').save(buf, 'PNG'); return buf.getvalue()

def _atomic_bytes(path, data):
    path = Path(os.path.realpath(path))
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.avatar.', suffix='.tmp')
    with os.fdopen(fd, 'wb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
    os.chmod(tmp, 0o644); os.replace(tmp, path)

def sync(m, displayed, root=None, agents=None, state_path=None):
    """displayed: {slug: (mood, voice)}. Returns list of slugs whose avatar was written."""
    root = root or art.ROOT; agents = agents or AGENTS; state_path = state_path or STATE
    try: prev = json.loads(Path(state_path).read_text())
    except (OSError, ValueError): prev = {}
    out, cur = [], dict(prev)
    for slug, (mood, voice) in displayed.items():
        cfg = m['agents'].get(slug)
        if not cfg or not cfg.get('id'): continue
        rel = art.resolve(cfg, mood, voice or 'idle', root=root)
        if not rel: continue
        d = Path(agents) / cfg['id']
        if not d.is_dir(): continue
        av = d / 'avatar.png'
        if prev.get(slug) == rel and av.exists(): continue
        try:
            data = still_png(Path(root) / rel)
            orig = d / 'avatar.orig.png'
            if av.exists() and not orig.exists(): shutil.copy2(av, orig)
            _atomic_bytes(av, data)
            cur[slug] = rel; out.append(slug)
        except Exception as e:
            print(f'avatar {slug} failed: {e}')
    if cur != prev:
        try: _atomic_bytes(state_path, json.dumps(cur, indent=1).encode())
        except OSError: pass
    return out
