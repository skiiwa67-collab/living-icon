# voice-session-extract/v1 + voice-continuity-pool/v2

Owned by tinkabot. Soft-PASS 2026-09-21 with skill voice-call-continuity-log.

## Per-session JSON (home pull)
`/workspace/agent-backups/<Agent>/voice-session-json/YYYY-MM-DD-HHMM-<slug>.json`
Dropbox: `/Grok-Agent-Backups/<Agent>/voice-session-json/`

Required fields: schema, agent, started, ended, slug, tags[], decisions[], product_details[], bugs[], hypotheses[], actions[], ops_knowledge[], paths{}, summary_md?

## Team pool
`/workspace/agent-backups/team/voice-continuity-pool.json`
v2 adds: tag_index, recent_calls[].tags, recent_calls[].paths.local_json / dropbox_json

## Product sidecars
`/workspace/agent-backups/team/<ProductKey>.json` (e.g. Estes-Ops.json) — keywords + payload

## Soft-FAIL
No platform voice-end daemon. No native full-audio STT Soft-PASS unless STT tool ran.
