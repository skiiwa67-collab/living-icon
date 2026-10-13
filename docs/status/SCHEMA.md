# living-icon-status-feed/v1

One JSON Soft-PASS file the browser dashboard Soft-PASS polls.

**Canonical (box-local):** `/workspace/living-icon-repo/docs/status/feed.json`, plus a copy at `/workspace/living-icon-repo/status/feed.json`.
Both are rebuilt atomically by `docs/dashboard/refresh_data.py` inside the Living Icon loop, using the box mood files listed in `docs/status/mood-sources.json`.
GitHub Pages is a backup only and is never in the live path (Chris rule, 2026-10-13). Timestamps are ISO 8601 with an offset.
`stateModel`: `matrix` uses moods calm|excited|somber|angry|thrilled and voices idle|listening|talking. `flat` (Eve) uses idle|listening|thinking|relay-active|waiting-parked|launch-dnd|happy|frustrated.
`waiting`: {ask_id, since, status} while the bot has an unresolved OK ask (read-only from interrupt-pending.json).

```
{
  "schema": "living-icon-status-feed/v1",
  "updated_at": "<ISO8601 America/Chicago or offset>",
  "stale_threshold_seconds": 21600,
  "host": {
    "has_pages": true,
    "canonical_path": "docs/status/feed.json",
    "url": "https://skiiwa67-collab.github.io/living-icon/dashboard/"
  },
  "agents": [
    {
      "agent": "helios",
      "mood": "calm|excited|somber|angry|thrilled|unreported",
      "voice_state": "idle|listening|talking",
      "gif_path": "/workspace/living-icon-repo/packages/<agent>-happy/matrix/{voice}/{mood}.gif",
      "gif_md5": "<md5>",
      "gif_mtime": "<ISO8601>",
      "stuck_seconds": 0,
      "stuck_softfail": false,
      "personality_path": null,
      "growth": { "source": "personality.json|unreported", "traits": {}, "mood_scores": {} }
    }
  ]
}
```

HARD: Soft-FAIL invent md5/mtime/traits. Soft-FAIL claim live if stuck_softfail true.
Ada Soft-PASS owns web host. Soft-FAIL invent has_pages false — Pages Soft-PASS from docs/.

## ok_request (per agent, 2026-10-13, Da Vinci OVERLAY-SPEC r2)
`"ok_request": {"state": "none|pending|urgent|approved", "ask_id": "<id>|null", "since": "<UTC ISO8601>|null", "priority": true|false}`.
`urgent` means priority:true and the ask has been open for more than 10 min. `approved` is reported for 30 s after approval, then becomes `none`.
The dashboard plays the approved frames once. Art: `packages/_overlay/ok-request/128/{state}/frame-NN.png` (full-canvas, top-right badge).
Order: plate, then Living Icon, then badge, then chrome. Feeds are rebuilt atomically by the loop whenever a mood or overlay changes, and on the 10 min refresh.
All timestamps are UTC ISO 8601.
