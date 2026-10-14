import unittest
from pathlib import Path
R = Path(__file__).resolve().parents[1]
class SchemaDocs(unittest.TestCase):
    def test_schema_docs_box_canonical(self):
        for p in ('status/SCHEMA.md', 'docs/status/SCHEMA.md'):
            s = (R / p).read_text()
            self.assertNotIn('Canonical path (GitHub Pages', s, p)
            self.assertIn('backup only', s, p)
if __name__ == '__main__': unittest.main()
