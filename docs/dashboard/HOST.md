# Soft-PASS host

- **Canonical UI:** `index.html` + `data.json` + `feed.json` + `refresh_data.py`
- **Phone-first:** stacked cards on a handset (16px type, 44px taps); table at ≥960px
- **Static Pages:** first view uses in-page snapshots + `data.json` / `feed.json` (no localhost)
- **P-stack feed:** also polls `../../status/feed.json` when served from the repo tree
- **GitHub Pages:** `/docs` → `https://skiiwa67-collab.github.io/living-icon/dashboard/`
- **Immediate HTML (if Pages lags):** `https://htmlpreview.github.io/?https://github.com/skiiwa67-collab/living-icon/blob/master/docs/dashboard/index.html`

Local fallback: `python3 -m http.server 8765` from the repo root, then `http://127.0.0.1:8765/docs/dashboard/`
