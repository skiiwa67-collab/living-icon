import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import set_mood as sm, mood_sources as ms

class MultiAgentSetMood(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._live, self._canon, self._mslive = sm.LIVE, dict(sm.CANON), ms.LIVE
        sm.LIVE = ms.LIVE = self.tmp / 'live'
        for s in sm.CANON: sm.CANON[s] = self.tmp / 'own' / f'{s}.json'
        (self.tmp / 'own').mkdir()
        (self.tmp / 'own' / 'saxon.json').write_text(json.dumps({'agent': 'saxon', 'mood': 'calm', 'gif_path': 'x.gif', 'updated': 'old'}))
    def tearDown(self):
        sm.LIVE, ms.LIVE = self._live, self._mslive; sm.CANON.clear(); sm.CANON.update(self._canon)

    def test_roster_is_12_bots_no_groups(self):
        self.assertEqual(len(sm.STATES), 12)
        self.assertNotIn('dfw-node', sm.STATES)
    def test_eve_flat_others_matrix(self):
        self.assertIn('relay-active', sm.STATES['eve'])
        for s in sm.STATES:
            if s != 'eve': self.assertEqual(sm.STATES[s], ['calm','excited','somber','angry','thrilled'])
    def test_every_agent_writes_own_and_live(self):
        for s in sm.STATES:
            m = 'thinking' if s == 'eve' else 'somber'
            sm.write_state(s, m)
            self.assertEqual(json.loads(sm.CANON[s].read_text())['mood'], m)
            self.assertEqual(json.loads((sm.LIVE / f'{s}.json').read_text())['mood'], m)
    def test_keeps_bot_schema(self):
        out = sm.write_state('saxon', 'angry')
        self.assertEqual(out['gif_path'], 'x.gif'); self.assertNotEqual(out['updated'], 'old')
    def test_rejects_bad_mood_and_agent(self):
        with self.assertRaises(SystemExit): sm.write_state('helios', 'idle')
        with self.assertRaises(SystemExit): sm.write_state('dfw-node', 'calm')

if __name__ == '__main__':
    unittest.main()
