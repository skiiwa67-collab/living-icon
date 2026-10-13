import sys, unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import ok_queue as q
M = {'agents': {'yard-software': {'name': 'Yard Software'}, 'dropbox-organizer': {'name': 'DropBox Organizer'},
                'ada': {'name': 'Ada'}, 'strip-electrical': {'name': 'Strip Electrical'}}}
N = q.name_map(M)
NOW = datetime(2026, 10, 13, 12, 20, tzinfo=timezone.utc)
def ask(aid, bot, st, ts='2026-10-13T06:35:00-05:00'):
    return {'kind': 'ask', 'ask_id': aid, 'bot': bot, 'status': st, 'since': '2026-10-13T06:35:00-05:00', 'ts': ts}
class T(unittest.TestCase):
    def test_variants(self):
        for b in ('Yard Software', 'yard software', 'YARD-SOFTWARE', ' yard_software ', 'YS', 'ys', 'yard-software', 'YardSoftware'):
            self.assertEqual(q.resolve_slug(b, N), 'yard-software', b)
        self.assertEqual(q.resolve_slug('dropbox organizer', N), 'dropbox-organizer')
        self.assertEqual(q.resolve_slug('DBO', N), 'dropbox-organizer')
    def test_askid_prefix_when_no_bot(self):
        self.assertEqual(q.resolve_slug('', N, 'YS-ROUTERSPEC-1'), 'yard-software')
        self.assertEqual(q.resolve_slug(None, N, 'ADA-20261013-01'), 'ada')
    def test_unknown_goes_other(self):
        act = q.active([ask('ZZ-1', 'Mystery Bot', 'open')], now=NOW)
        self.assertEqual(len(q.unmapped(act, N)), 1)
        self.assertEqual(q.ok_request_by_slug(N, now=NOW, items=[ask('ZZ-1', 'Mystery Bot', 'open')]), {})
    def test_badge_for_alias(self):
        items = [ask('YS-X', 'YS', 'blocked-offline')]
        act = q.active(items, now=NOW)
        self.assertEqual(q.unmapped(act, N), [])
        self.assertEqual(q.ok_request_by_slug(N, now=NOW, items=items)['yard-software']['state'], 'pending')
        self.assertIn('yard-software', q.waiting_by_slug(act, N))
    def test_header_count_matches_badges_done_not_counted(self):
        items = [ask('YS-ROUTERSPEC-1', 'Yard Software', 'blocked-offline'),
                 ask('YS-ROUTERSPEC-1', 'Yard Software', 'done', ts='2026-10-13T07:17:26-05:00'),
                 ask('ADA-20261013-01', 'Ada', 'done')]
        act = q.active(items, now=NOW)
        self.assertEqual(len(act), 0)
        self.assertEqual(q.ok_request_by_slug(N, now=NOW, items=items), {})
        items.append(ask('SE-1', 'strip electrical', 'open'))
        act = q.active(items, now=NOW)
        badges = q.ok_request_by_slug(N, now=NOW, items=items)
        self.assertEqual(len(act), len(badges) + len(q.unmapped(act, N)))
if __name__ == '__main__': unittest.main()
