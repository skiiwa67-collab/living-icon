import json, os, sys, tempfile, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import set_mood, derive_eve_state as d

NOW = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
def iso(dt): return dt.isoformat()

class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.canon = self.tmp / 'mood-state.json'
        self.live = self.tmp / 'live'
        self._saved = (dict(set_mood.CANON), set_mood.LIVE, d.LIVE, d.LAUNCH)
        self._iso = (d.QUEUE, set_mood.WRITE_LOG)   # isolate from the real OK queue / write log
        d.QUEUE = self.tmp / 'queue.json'; set_mood.WRITE_LOG = self.tmp / 'writes.log'
        set_mood.CANON['eve'] = self.canon
        set_mood.LIVE = d.LIVE = self.live
        d.LAUNCH = self.live / 'launch.json'
        self.log = self.tmp / 'relay-log.jsonl'
        self.log.write_text('')
    def tearDown(self):
        c, set_mood.LIVE, d.LIVE, d.LAUNCH = self._saved
        d.QUEUE, set_mood.WRITE_LOG = self._iso
        set_mood.CANON.clear(); set_mood.CANON.update(c)
    def lines(self, *rs): self.log.write_text(''.join(json.dumps(r) + '\n' for r in rs))
    def row(self, ask, status, mins_ago=1, **kw):
        r = {'ask_id': ask, 'bot': 'Helios', 'status': status, 'sent_at': iso(NOW - timedelta(minutes=mins_ago))}
        if status == 'held-for-card': r['answered_at'] = r['sent_at']
        r.update(kw); return r

class Derive(Base):
    def test_empty_log(self):
        self.assertEqual(d.derive(self.log, None, NOW), (None, None))
    def test_missing_log(self):
        self.assertEqual(d.derive(self.tmp / 'nope.jsonl', None, NOW), (None, None))
    def test_pending_relay_active(self):
        self.lines(self.row('A', 'pending'))
        self.assertEqual(d.derive(self.log, None, NOW)[0], 'relay-active')
    def test_held_for_card_is_waiting_parked(self):
        self.lines(self.row('A', 'held-for-card'))
        self.assertEqual(d.derive(self.log, None, NOW)[0], 'waiting-parked')
    def test_retired_aliases_and_other_statuses_ignored(self):
        self.lines(self.row('A', 'sent'), self.row('B', 'yes-held-for-card'), self.row('C', 'answered'),
                   self.row('D', 'done'), self.row('E', 'failed'))
        self.assertEqual(d.derive(self.log, None, NOW), (None, None))
    def test_newest_line_per_ask_wins(self):
        self.lines(self.row('A', 'pending', 3), self.row('A', 'done', 2))
        self.assertEqual(d.derive(self.log, None, NOW), (None, None))
        self.lines(self.row('A', 'pending', 3), self.row('A', 'held-for-card', 2))
        self.assertEqual(d.derive(self.log, None, NOW)[0], 'waiting-parked')
    def test_stale_pending(self):
        self.lines(self.row('A', 'pending', 31))
        self.assertEqual(d.derive(self.log, None, NOW), (None, None))
        self.lines(self.row('A', 'pending', 29))
        self.assertEqual(d.derive(self.log, None, NOW)[0], 'relay-active')
    def test_stale_held_for_card(self):
        self.lines(self.row('A', 'held-for-card', 12 * 60 + 1))
        self.assertEqual(d.derive(self.log, None, NOW), (None, None))
        self.lines(self.row('A', 'held-for-card', 11 * 60))
        self.assertEqual(d.derive(self.log, None, NOW)[0], 'waiting-parked')
    def test_priority(self):
        self.lines(self.row('A', 'pending'), self.row('B', 'held-for-card'))
        m, r = d.derive(self.log, None, NOW)
        self.assertEqual((m, r['ask_id']), ('waiting-parked', 'B'))
        self.assertEqual(d.derive(self.log, iso(NOW + timedelta(minutes=5)), NOW)[0], 'launch-dnd')
    def test_launch_window_edges(self):
        for off, want in [(30*60, 'launch-dnd'), (30*60 + 1, None), (-60*60, 'launch-dnd'), (-60*60 - 1, None), (0, 'launch-dnd')]:
            self.assertEqual(d.derive(self.log, iso(NOW + timedelta(seconds=off)), NOW)[0], want, off)

class Tick(Base):
    def test_write_unchanged_clear_shape(self):
        self.lines(self.row('A', 'pending'))
        r1 = d.tick(self.log, None, NOW); self.assertEqual(r1, ('relay-active', 'wrote', 'A'))
        r2 = d.tick(self.log, None, NOW); self.assertEqual(r2, ('relay-active', 'unchanged', 'A'))
        self.lines(self.row('A', 'pending'), self.row('A', 'done'))
        r3 = d.tick(self.log, None, NOW); self.assertEqual(r3, ('idle', 'cleared', None))
        r4 = d.tick(self.log, None, NOW); self.assertEqual(r4, ('idle', 'unchanged', None))
        for r in (r1, r2, r3, r4): self.assertEqual(len(r), 3)
        st = json.loads(self.canon.read_text())
        self.assertEqual(set(['mood','since','ask_id','bot','source']) - set(st), set())
        self.assertEqual(oct(self.canon.stat().st_mode & 0o777), '0o644')
        self.assertEqual(self.canon.read_bytes(), (self.live / 'eve.json').read_bytes())
    def test_hold_respected_same_shape(self):
        set_mood.write_state('eve', 'frustrated', hold=5)
        self.lines(self.row('A', 'pending'))
        r = d.tick(self.log, None, datetime.now(timezone.utc))
        self.assertEqual(r[:2], ('frustrated', 'hold-respected')); self.assertEqual(len(r), 3)

class OkQueueAndHold(Base):
    def q(self, *items): d.QUEUE.write_text(json.dumps(list(items)))
    def item(self, aid, status, mins_ago=1, **kw):
        r = {'ask_id': aid, 'bot': 'Ada', 'status': status, 'filed': iso(NOW - timedelta(minutes=mins_ago))}
        r.update(kw); return r
    def test_open_and_tap_pending_relay_active(self):
        for st in ('open', 'pending', 'tap-pending'):
            self.q(self.item('Q', st)); self.assertEqual(d.derive(self.log, None, NOW), ('relay-active', {'ask_id': 'Q', 'bot': 'Ada'}))
    def test_parked_blocked_waiting_parked(self):
        for st in ('parked', 'blocked-offline'):
            self.q(self.item('Q', st)); self.assertEqual(d.derive(self.log, None, NOW)[0], 'waiting-parked')
    def test_priority_queue_parked_beats_relay_pending(self):
        self.lines(self.row('A', 'pending')); self.q(self.item('Q', 'parked'))
        self.assertEqual(d.derive(self.log, None, NOW)[0], 'waiting-parked')
    def test_launch_beats_queue(self):
        self.q(self.item('Q', 'parked'))
        self.assertEqual(d.derive(self.log, iso(NOW), NOW)[0], 'launch-dnd')
    def test_stale_only_after_reread_and_closed_ignored(self):
        rr = iso(NOW)
        self.q(self.item('A', 'open', mins_ago=31, reread_at=rr), self.item('B', 'parked', mins_ago=13*60, reread_at=rr),
               self.item('C', 'approved'), self.item('D', 'withdrawn'), self.item('E', 'resolved: yes'),
               self.item('F', 'done'), self.item('G', 'fail'), self.item('H', 'blocked'))
        self.assertEqual(d.derive(self.log, None, NOW), (None, None))
    def test_no_stale_without_reread(self):
        self.q(self.item('A', 'open', mins_ago=31))
        self.assertEqual(d.derive(self.log, None, NOW)[0], 'relay-active')
    def test_pending_then_done_not_active(self):
        self.q(self.item('A', 'pending', mins_ago=5), self.item('A', 'done', mins_ago=1))
        self.assertEqual(d.derive(self.log, None, NOW), (None, None))
        import ok_queue; self.assertEqual(ok_queue.active(now=NOW, path=d.QUEUE), [])
    def test_helios_statuses(self):
        for st, want in (('held-for-card', 'waiting-parked'), ('held-for-chat', 'waiting-parked'), ('held-launch', 'launch-dnd')):
            self.q(self.item('Q', st)); self.assertEqual(d.derive(self.log, None, NOW)[0], want)
    def test_relay_log_retired_missing(self):
        self.log.rename(self.log.with_suffix('.jsonl.retired'))
        self.assertEqual(d.derive(self.log, None, NOW), (None, None))
        self.q(self.item('Q', 'open')); self.assertEqual(d.tick(self.log, None, NOW)[:2], ('relay-active', 'wrote'))
    def test_manual_set_stands_until_new_event(self):
        self.q(self.item('Q', 'parked', mins_ago=10))
        set_mood.write_state('eve', 'happy', hold=0, source='cli')
        r = d.tick(self.log, None, datetime.now(timezone.utc)); self.assertEqual(r[:2], ('happy', 'manual-respected'))
        self.q(self.item('Q', 'parked', mins_ago=10), self.item('R', 'open', mins_ago=-1))
        r = d.tick(self.log, None, datetime.now(timezone.utc) + timedelta(minutes=2)); self.assertEqual(r[0], 'waiting-parked')
    def test_missing_and_malformed_queue(self):
        self.assertEqual(d.derive(self.log, None, NOW), (None, None))
        d.QUEUE.write_text('{not json'); self.assertEqual(d.derive(self.log, None, NOW), (None, None))
    def test_queue_never_written(self):
        self.q(self.item('Q', 'open')); before = d.QUEUE.read_bytes()
        d.tick(self.log, None, NOW); self.assertEqual(d.QUEUE.read_bytes(), before)
    def test_hold_expiry_reverts(self):
        set_mood.write_state('eve', 'frustrated', hold=0.01, revert='idle')
        import time; time.sleep(0.05)
        r = d.tick(self.log, None, datetime.now(timezone.utc))
        self.assertEqual(json.loads(self.canon.read_text())['mood'], 'idle'); self.assertEqual(r[0], 'idle')

if __name__ == '__main__':
    unittest.main()
