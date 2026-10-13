import os, subprocess, tempfile, time, unittest
from pathlib import Path
LOOP = Path(__file__).resolve().parents[1] / 'scripts' / 'living-icon-loop.sh'
class T(unittest.TestCase):
    def env(self, d, **kw):
        e = dict(os.environ, LI_DIR=d, LI_LOGS=d, LI_LOCK=f'{d}/lock', LI_PIDFILE=f'{d}/pid', LI_SLEEP='0.1',
                 LI_DERIVE=f'sh -c "echo D >> {d}/order"', LI_SYNC=f'sh -c "echo S >> {d}/order"',
                 LI_REFRESH=f'sh -c "echo R >> {d}/order"')
        e.update(kw); return e
    def test_one_derive_per_tick_before_sync(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(['bash', str(LOOP)], env=self.env(d, LI_MAX_TICKS='3'), timeout=10, check=True)
            self.assertEqual(Path(d, 'order').read_text().split(), ['R', 'D', 'S', 'D', 'S', 'D', 'S'])
            self.assertFalse(Path(d, 'pid').exists())
    def test_no_looping_deriver_in_script(self):
        s = LOOP.read_text()
        self.assertNotIn('--loop', s); self.assertIn('derive_eve_state.py --once', s); self.assertNotIn(' &\n', s)
    def test_singleton(self):
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.Popen(['bash', str(LOOP)], env=self.env(d))
            try:
                time.sleep(0.5)
                r = subprocess.run(['bash', str(LOOP)], env=self.env(d, LI_MAX_TICKS='1'), capture_output=True, text=True, timeout=5)
                self.assertEqual(r.returncode, 1); self.assertIn('already running', r.stderr)
                self.assertEqual(Path(d, 'pid').read_text().strip(), str(p.pid))
            finally:
                p.terminate(); p.wait(5)
if __name__ == '__main__': unittest.main()
