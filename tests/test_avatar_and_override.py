import json, sys, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tests')); sys.path.insert(0, str(REPO / 'scripts'))
from PIL import Image
import display, sync_avatars, mood_sources as ms, sync_live_moods as sync, set_mood as sm
from test_set_mood_multi import Base

class Display(unittest.TestCase):
    M = {'stateModel': 'matrix'}
    def test_pending_and_urgent_show_excited(self):
        for st in ('pending', 'urgent'):
            self.assertEqual(display.display_mood(self.M, 'somber', {'state': st}), ('excited', 'ok-request-' + st))
    def test_none_or_approved_keeps_own_mood(self):
        for o in (None, {'state': 'none'}, {'state': 'approved'}):
            self.assertEqual(display.display_mood(self.M, 'somber', o), ('somber', None))
    def test_flat_model_unchanged(self):
        self.assertEqual(display.display_mood({'stateModel': 'flat'}, 'idle', {'state': 'pending'}), ('idle', None))

class EveOverride(unittest.TestCase):
    def test_eve_pending_shows_relay_active(self):
        F = {'stateModel': 'flat'}
        for st in ('pending', 'urgent'):
            self.assertEqual(display.display_mood(F, 'idle', {'state': st}, 'eve'), ('relay-active', 'ok-request-' + st))
        self.assertEqual(display.display_mood(F, 'thinking', {'state': 'none'}, 'eve'), ('thinking', None))
        self.assertIn('relay-active', ms.load_map()['flat_moods'])

class Avatars(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.m = ms.load_map(); self.id = self.m['agents']['helios']['id']
        self.d = self.t / 'agents' / self.id; self.d.mkdir(parents=True)
        (self.d / 'avatar.png').write_bytes(b'ORIGINAL')
        self.kw = dict(agents=self.t / 'agents', state_path=self.t / 'st.json')
    def test_writes_still_backup_once_and_only_on_change(self):
        out = sync_avatars.sync(self.m, {'helios': ('excited', 'idle')}, **self.kw)
        self.assertEqual(out, ['helios'])
        self.assertEqual((self.d / 'avatar.orig.png').read_bytes(), b'ORIGINAL')
        im = Image.open(self.d / 'avatar.png'); self.assertEqual(im.format, 'PNG')
        self.assertEqual(sync_avatars.sync(self.m, {'helios': ('excited', 'idle')}, **self.kw), [])
        self.assertEqual(sync_avatars.sync(self.m, {'helios': ('calm', 'idle')}, **self.kw), ['helios'])
        self.assertEqual((self.d / 'avatar.orig.png').read_bytes(), b'ORIGINAL')   # backup kept, not overwritten
        self.assertEqual([p.name for p in self.d.iterdir() if p.name.endswith('.tmp')], [])
    def test_missing_agent_dir_skipped(self):
        self.assertEqual(sync_avatars.sync(self.m, {'ada': ('calm', 'idle')}, **self.kw), [])

class SyncOverride(Base):
    def test_pending_ask_overlays_excited_without_touching_own_file(self):
        sm.write_state('saxon', 'somber')
        now = datetime.now(timezone.utc).isoformat()
        self.q.write_text(json.dumps([{'ask_id': 'ASK-T1', 'bot': 'Saxon', 'status': 'pending', 'ts': now, 'since': now}]))
        sync.main(queue_path=self.q, write_feeds=False, hashes_path=self.hp)
        live = json.loads((sm.LIVE / 'saxon.json').read_text())
        self.assertEqual(live['mood'], 'somber'); self.assertEqual(live['display_mood'], 'excited')
        self.assertEqual(json.loads(sm.CANON['saxon'].read_text())['mood'], 'somber')
        self.q.write_text('[]')
        sync.main(queue_path=self.q, write_feeds=False, hashes_path=self.hp)
        live = json.loads((sm.LIVE / 'saxon.json').read_text())
        self.assertNotIn('display_mood', live); self.assertEqual(live['mood'], 'somber')

class AvatarGate(Base):
    def test_avatar_write_off_by_default(self):
        import os; os.environ.pop('LI_AVATAR_WRITE', None)
        called = []; orig = sync.sync_avatars.sync
        sync.sync_avatars.sync = lambda *a, **k: called.append(1) or []
        try: sync.main(queue_path=self.q, write_feeds=False, hashes_path=self.hp)
        finally: sync.sync_avatars.sync = orig
        self.assertEqual(called, [])

if __name__ == '__main__': unittest.main()
