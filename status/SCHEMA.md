# living-icon-status-feed/v1

One JSON Soft-PASS file the browser dashboard Soft-PASS polls.

```
{
  "schema": "living-icon-status-feed/v1",
  "updated_at": "<ISO8601 America/Chicago or offset>",
  "stale_threshold_seconds": 21600,
  "agents": [
    {
      "agent": "helios",
      "mood": "calm|excited|somber|angry|thrilled|unreported",
      "voice_state": "idle|listening|talking",
      "gif_path": "/workspace/living-icon/packages/<agent>-happy/softpass/avatar-idle.gif",
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
Ada Soft-PASS owns web host. Feed lives at `/workspace/living-icon/status/feed.json`.
