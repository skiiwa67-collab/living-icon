# Eve live state (Helios spec, 2026-10-13)

- **Source of truth:** `/workspace/agent-backups/Eve/mood-state.json`, written atomically (temp file + rename).
  Fields: `mood`, `since` (ISO8601), `ask_id`, `bot`, `source`; extras `agent`, `hold_until`, `revert_to`.
- **Mirror:** `docs/status/live/eve.json` is a copy for dashboard serving. `set_mood.py` writes it right after
  the canonical file. If the canonical file is edited any other way, run `scripts/set_mood.py eve --sync-only`.
- **State model:** feed entry `stateModel: "flat"`. The dashboard uses `packages/eve-happy/states/<mood>.gif`
  only for flat agents; `launch-dnd` maps to `launch-DND.gif`.
- **Icon:** reads only the state file (via the mirror), polled every 3s; past `hold_until` it shows `revert_to`.
- **Priority (deriver):** launch-dnd > waiting-parked > relay-active > idle. Newest matching relay line wins; its `ask_id`/`bot` go into the state.
- **Writers:** `scripts/set_mood.py eve <mood> [--hold N] [--ask-id ID] [--bot NAME]`, `scripts/derive_eve_state.py [--loop 5]` (reads Helios's relay-log.jsonl read-only).
- Serve from repo root (dashboard references `../../packages/`).

| Mood | Trigger | Who can emit |
|---|---|---|
| idle | no activity / hold expired / derived condition ended | default + revert + deriver |
| listening | Chris voice input active | PLATFORM HOOK needed |
| thinking | Eve working on a turn | Eve: set_mood at turn start |
| relay-active | relay-log line status sent/pending, no answer | deriver |
| waiting-parked | relay-log line status yes-held-for-card (or parked_at w/o card_result) | deriver |
| launch-dnd | live LRT launch NET-30min..NET+60min | deriver; needs `docs/status/live/launch.json {"net":ISO}` or `--net` (no NET feed on box yet) |
| happy | task done, 4s hold | Eve: set_mood at turn end |
| frustrated | Chris interrupts Eve mid-reply, 5s hold | PLATFORM HOOK needed |
