import json, subprocess, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'scripts'))
import set_mood as sm, mood_sources as ms, sync_live_moods as sync, art

class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._s = (sm.LIVE, dict(sm.CANON), ms.LIVE, sm.WRITE_LOG, ms.src_path)
        sm.LIVE = ms.LIVE = self.tmp / 'live'
        for s in sm.CANON: sm.CANON[s] = self.tmp / 'own' / f'{s}.json'
        ms.src_path = lambda cfg, _c=dict(sm.CANON), _m=ms.load_map(): next(_c[s] for s, c in _m['agents'].items() if c['id'] == cfg['id'])
        sm.WRITE_LOG = self.tmp / 'writes.log'
        (self.tmp / 'own').mkdir()
        (self.tmp / 'own' / 'saxon.json').write_text(json.dumps({'agent': 'saxon', 'mood': 'calm', 'gif_path': 'x.gif', 'updated': 'old'}))
        self.q = self.tmp / 'q.json'; self.q.write_text('[]'); self.hp = self.tmp / 'hashes.json'
    def tearDown(self):
        sm.LIVE, c, ms.LIVE, sm.WRITE_LOG, ms.src_path = self._s
        sm.CANON.clear(); sm.CANON.update(c)

class MultiAgentSetMood(Base):
    def test_roster_is_12_bots_no_groups(self):
        self.assertEqual(len(sm.STATES), 12); self.assertNotIn('dfw-node', sm.STATES)
    def test_eve_flat_others_matrix(self):
        self.assertIn('relay-active', sm.STATES['eve'])
        for s in sm.STATES:
            if s != 'eve': self.assertEqual(sm.STATES[s], ['calm', 'excited', 'somber', 'angry', 'thrilled'])
    def test_every_agent_writes_own_and_live_and_logs(self):
        for s in sm.STATES:
            m = 'thinking' if s == 'eve' else 'somber'
            sm.write_state(s, m, writer=s)
            self.assertEqual(json.loads(sm.CANON[s].read_text())['mood'], m)
            self.assertEqual(json.loads((sm.LIVE / f'{s}.json').read_text())['mood'], m)
        lines = [json.loads(l) for l in sm.WRITE_LOG.read_text().splitlines()]
        self.assertEqual(len(lines), 12); self.assertEqual(set(lines[0]), {'ts', 'writer', 'target', 'old', 'new'})
    def test_keeps_bot_schema_and_subsecond_since(self):
        out = sm.write_state('saxon', 'angry')
        self.assertEqual(out['gif_path'], 'x.gif'); self.assertNotEqual(out['updated'], 'old')
        self.assertRegex(out['since'], r'\.\d{6}\+00:00$')
    def test_rejects_bad_mood_and_agent(self):
        with self.assertRaises(SystemExit): sm.write_state('helios', 'idle')
        with self.assertRaises(SystemExit): sm.write_state('dfw-node', 'calm')
    def test_cli_refuses_other_bot_without_test(self):
        r = subprocess.run([sys.executable, str(REPO / 'scripts/set_mood.py'), 'helios', 'calm', '--as', 'ada'], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0); self.assertIn('refused', r.stderr)

class Sync(Base):
    def test_source_always_wins_even_older_rollback(self):
        sm.write_state('saxon', 'angry'); sync.main(queue_path=self.q, write_feeds=False, hashes_path=self.hp)
        own = self.tmp / 'own' / 'saxon.json'
        own.write_text(json.dumps({'agent': 'saxon', 'mood': 'calm', 'updated': '2020-01-01T00:00:00+00:00'}))
        sync.main(queue_path=self.q, write_feeds=False, hashes_path=self.hp)
        self.assertEqual(json.loads((sm.LIVE / 'saxon.json').read_text())['mood'], 'calm')
    def test_voice_and_hold_fields_kept(self):
        sm.write_state('perseus', 'excited', voice_state='talking', hold=60, revert='calm'); sync.main(queue_path=self.q, write_feeds=False, hashes_path=self.hp)
        live = json.loads((sm.LIVE / 'perseus.json').read_text())
        self.assertEqual(live['voice_state'], 'talking'); self.assertIsNotNone(live['hold_until']); self.assertEqual(live['revert_to'], 'calm')
    def test_hold_expiry_reverts_own_file(self):
        sm.write_state('helios', 'angry', hold=0.001, revert='calm')
        sync.main(now=datetime.now(timezone.utc) + timedelta(seconds=1), queue_path=self.q, write_feeds=False, hashes_path=self.hp)
        self.assertEqual(json.loads(sm.CANON['helios'].read_text())['mood'], 'calm')
    def test_waiting_overlay_set_and_cleared(self):
        sm.write_state('ada', 'calm')
        now = datetime.now(timezone.utc)
        self.q.write_text(json.dumps([{'kind': 'ask', 'ask_id': 'ADA-1', 'bot': 'Ada', 'status': 'pending', 'since': now.isoformat()}]))
        sync.main(queue_path=self.q, write_feeds=False, hashes_path=self.hp)
        live = json.loads((sm.LIVE / 'ada.json').read_text())
        self.assertEqual(live['waiting']['ask_id'], 'ADA-1'); self.assertEqual(live['mood'], 'calm')
        self.q.write_text(json.dumps([{'kind': 'ask', 'ask_id': 'ADA-1', 'bot': 'Ada', 'status': 'pending', 'since': now.isoformat()},
                                      {'kind': 'ask', 'ask_id': 'ADA-1', 'bot': 'Ada', 'status': 'approved', 'since': now.isoformat()}]))
        sync.main(queue_path=self.q, write_feeds=False, hashes_path=self.hp)
        self.assertNotIn('waiting', json.loads((sm.LIVE / 'ada.json').read_text()))
    def test_malformed_queue_ok(self):
        self.q.write_text('{oops'); sm.write_state('ada', 'calm'); sync.main(queue_path=self.q, write_feeds=False, hashes_path=self.hp)

class HashAndSymlink(Base):
    def test_live_is_source_change_triggers_rebuild(self):
        sm.write_state('helios', 'calm'); sync.main(queue_path=self.q, write_feeds=False, hashes_path=self.hp)
        self.assertEqual(sync.main(queue_path=self.q, write_feeds=False, hashes_path=self.hp), [])
        p = sm.CANON['helios']   # helios-style bot: hand-edit the file the bot owns
        p.write_text(json.dumps(dict(json.loads(p.read_text()), mood='angry')))
        ch = sync.main(queue_path=self.q, write_feeds=False, hashes_path=self.hp)
        self.assertTrue(any(c.startswith('hash:') for c in ch), ch)
    def test_atomic_write_keeps_symlink(self):
        real = self.tmp / 'real.json'; real.write_text('{}'); link = self.tmp / 'link.json'; link.symlink_to(real)
        sm._atomic(link, {'mood': 'calm'})
        self.assertTrue(link.is_symlink()); self.assertEqual(json.loads(real.read_text())['mood'], 'calm')

class QueueLatestByTs(unittest.TestCase):
    def test_newest_by_ts_not_file_order(self):
        import ok_queue as q
        recs = [{'ask_id': 'A', 'status': 'done', 'ts': '2026-10-13T12:05:00+00:00'},
                {'ask_id': 'A', 'status': 'pending', 'ts': '2026-10-13T12:00:00+00:00'}]
        self.assertEqual(q.latest(recs)['A']['status'], 'done')
        self.assertEqual(q.active(recs, now=datetime(2026, 10, 13, 12, 6, tzinfo=timezone.utc)), [])

class Art(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        for f in ('p/matrix/idle/calm.gif', 'p/matrix/idle/angry.gif', 'q/matrix/calm-idle.gif', 'e/states/idle.gif', 'e/states/launch-DND.gif'):
            (self.root / f).parent.mkdir(parents=True, exist_ok=True); (self.root / f).write_bytes(b'x')
    def r(self, d, m, v, model='matrix'): return art.resolve({'art_dir': d, 'stateModel': model}, m, v, root=self.root)
    def test_voice_falls_back_to_idle(self): self.assertEqual(self.r('p', 'angry', 'talking'), 'p/matrix/idle/angry.gif')
    def test_missing_mood_falls_back_calm_idle(self): self.assertEqual(self.r('p', 'thrilled', 'listening'), 'p/matrix/idle/calm.gif')
    def test_flat_name_layout(self): self.assertEqual(self.r('q', 'somber', 'talking'), 'q/matrix/calm-idle.gif')
    def test_eve_flat_never_calm(self):
        self.assertEqual(self.r('e', 'launch-dnd', 'idle', 'flat'), 'e/states/launch-DND.gif')
        self.assertEqual(self.r('e', 'thinking', 'idle', 'flat'), 'e/states/idle.gif')

if __name__ == '__main__':
    unittest.main()
