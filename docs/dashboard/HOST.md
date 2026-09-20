# Soft-PASS host

- **Canonical UI:** `index.html` + `data.json` + `refresh_data.py`
- **P-stack feed:** polls `../../status/feed.json` (tinkabot Soft-PASS) for `stuck_seconds` + Soft-FAIL lamp
- **Pages Soft-FAIL:** `living-icon` has_pages=false — no Soft-PASS public URL yet
- **Soft-PASS open now:** open this folder via browser `file://…/docs/dashboard/index.html` (feed fetch needs same-origin; if file:// blocks fetch, Soft-PASS run `python3 -m http.server 8765` from `living-icon/` and open `http://127.0.0.1:8765/docs/dashboard/`)
