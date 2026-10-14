from pathlib import Path
R = Path(__file__).resolve().parents[1]
def test_schema_docs_box_canonical():
    for p in ('status/SCHEMA.md', 'docs/status/SCHEMA.md'):
        s = (R / p).read_text()
        assert 'Canonical path (GitHub Pages' not in s, p
        assert 'backup only' in s, p
