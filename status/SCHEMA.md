# living-icon-status-feed/v1

One JSON Soft-PASS file the browser dashboard Soft-PASS polls.

**Canonical path (box-local):** `/workspace/living-icon-repo/docs/status/feed.json`
**Mirror:** `/workspace/living-icon-repo/status/feed.json` (identical content, rebuilt by the loop; host.canonical_path = `docs/status/feed.json`)
GitHub Pages (https://skiiwa67-collab.github.io/living-icon/status/feed.json) is a backup only and is never in the live path (Chris rule, 2026-10-13).

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
