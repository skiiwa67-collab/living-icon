# Eve live state (Helios spec, 2026-10-13)

- **Source of truth:** `/workspace/agent-backups/Eve/mood-state.json`, written atomically (temp file + rename).
  Fields: `mood`, `since` (ISO8601), `ask_id`, `bot`, `source`; extras `agent`, `hold_until`, `revert_to`.
- **Mirror:** `docs/status/live/eve.json` is a copy for dashboard serving. `set_mood.py` writes it right after
  the canonical file. If the canonical file is edited any other way, run `scripts/set_mood.py eve --sync-only`.
- **State model:** feed entry `stateModel: "flat"`. The dashboard uses `packages/eve-happy/states/<mood>.gif`
  only for flat agents; `launch-dnd` maps to `launch-DND.gif`.
- **Icon:** reads only the state file (via the mirror), polled every 3s; past `hold_until` it shows `revert_to`.
- **Status names:** canonical in Helios `eve-relay/SCHEMA.md` (LRT main 4ba398f): `pending` -> relay-active, `held-for-card` -> waiting-parked, `answered` -> no change, `done`/`failed` -> idle. Aliases `sent`/`yes-held-for-card` are retired and ignored.
- **Newest line per ask_id** is that ask's state; older lines are history.
- **Stale:** `pending` older than 30 min (by `sent_at`), `held-for-card` older than 12 h (by `answered_at`, else `sent_at`) are ignored.
- **Priority (deriver):** launch-dnd (NET-30min..NET+60min inclusive) > waiting-parked > relay-active > idle; the matched line's `ask_id`/`bot` go into the state.
- **Writes:** temp file, fsync, chmod 0644, rename. `tick()` always returns `(mood, action, ask_id)`.
- **Tests:** `python3 -m unittest discover -s tests`.
- **Writers:** `scripts/set_mood.py eve <mood> [--hold N] [--ask-id ID] [--bot NAME]`, `scripts/derive_eve_state.py [--loop 5]` (reads Helios's relay-log.jsonl read-only).
- Serve from repo root (dashboard references `../../packages/`).

| Mood | Trigger | Who can emit |
|---|---|---|
| idle | no activity / hold expired / derived condition ended | default + revert + deriver |
| listening | Chris voice input active | PLATFORM HOOK needed |
| thinking | Eve working on a turn | Eve: set_mood at turn start |
| relay-active | newest relay-log line for an ask is `pending` (<30 min) | deriver |
| waiting-parked | newest relay-log line for an ask is `held-for-card` (<12 h) | deriver |
| launch-dnd | live LRT launch NET-30min..NET+60min | deriver; needs `docs/status/live/launch.json {"net":ISO}` or `--net` (no NET feed on box yet) |
| happy | task done, 4s hold | Eve: set_mood at turn end |
| frustrated | Chris interrupts Eve mid-reply, 5s hold | PLATFORM HOOK needed |
