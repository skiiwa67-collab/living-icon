# Eve live state (2026-10-13)

State file: `docs/status/live/eve.json` `{agent,state,since,hold_until,revert_to,source}`.
Dashboard polls it every 3s; past `hold_until` it shows `revert_to` (idle).
Writers: `scripts/set_mood.py eve <state> [--hold N]`, `scripts/derive_eve_state.py [--loop 5]`.
Serve from repo root (dashboard references `../../packages/eve-happy/states/`).

| State | Trigger | Who can emit |
|---|---|---|
| idle | no activity / hold expired | default + revert |
| listening | Chris voice input active | PLATFORM HOOK needed (bot doesn't see mic until turn arrives) |
| thinking | Eve working on a turn | Eve: set_mood at turn start (only while running) |
| relay-active | relay-log.jsonl line status sent/pending, no answer | deriver (read-only) |
| waiting-parked | relay-log line status yes-held-for-card (or parked_at w/o card_result) | deriver |
| launch-DND | live LRT launch NET-30min..NET+60min | deriver, needs `docs/status/live/launch.json {"net":ISO}` or `--net`; no NET feed exists on the box yet |
| happy | task done, 4s hold | Eve: set_mood at turn end |
| frustrated | Chris interrupts Eve mid-reply, 5s hold | PLATFORM HOOK needed (an interrupted turn is cancelled; bot gets no callback) |
