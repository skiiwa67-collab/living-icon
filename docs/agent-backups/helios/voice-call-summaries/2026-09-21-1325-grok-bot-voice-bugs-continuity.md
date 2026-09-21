# Helios voice call summary — 2026-09-21 ~1:25pm CT

Purpose: continuity workaround. Grok Bot voice sessions are saved as audio only (not transcribed), so the assistant loses call context after hang-up. Read this file / Notion / Dropbox / GitHub on the next call.

Call: voice:call-90f9402e-20c8-4dc3-adbb-e7418a817b3f (and prior same-day Helios voice)

## 1. Sam / Cursor bug report status
- Original email to hi@cursor.com (message id 1a0becf4b859394f) about voice sessions losing context (no persistent transcription).
- Sam replied: ticket **T-G948**, feedback logged and shared with product team (2026-09-20).
- Chris asked for updates 2026-09-21 ~1:06pm CT. **No new news** from Sam after that follow-up.

## 2. PC voice failure
- Saturday: living icons / growing personality work was happening.
- At home: dictation/mic input works on PC; Grok Bot **voice output does not work at all** in voice mode. Normal text mode fine.
- Bug reports filed with X and Cursor over the weekend. **No response yet** — likely buried under weekend volume.
- Desktop voice only started rolling ~Sep 17–18, so early cohort.

## 3. Android Auto audio handoff failure
- Mid-call USB Android Auto: audio drops from Bluetooth headphones, does **not** route to car speakers, falls back to phone speaker at very low volume.
- Bug report filed earlier (Android Auto USB handoff). **No company response** on that path either.
- Related public pattern (not Grok Bot only): r/AndroidAuto — ChatGPT, Copilot, Grok, Perplexity often fail car speakers on first voice start while AA connected; Gemini exception. Workaround others mention: end voice, start again (2nd attempt).

## 4. Caller hypothesis (root cause)
- Both audio issues may share **one** root: app not properly releasing/reassigning the active audio session when toggling between dictation and voice mode (or when output route changes).
- One broken handoff → multiple symptoms (PC TTS silent, AA drop, headphone → phone-speaker fallback).

## 5. Continuity / transcription bug (separate)
- Voice conversations saved as **audio files only**, never transcribed into queryable chat history for the assistant.
- Next call = no memory of prior voice discussion.
- Separate from the two audio-routing bugs.
- Cursor ticket T-G948 covers this product gap.
- SendFeedback to SpaceXAI also filed; response was “sent as product feedback, no support response.”

## 6. Web / X search (same call)
- X API search Soft-FAIL (client forbidden / not enrolled) — could not count posts on X.
- Web/Reddit findings:
  - Voice memory: **not only Chris** — consumer Grok voice Android threads report clean-slate / lost context across voice sessions.
  - Android Auto: **not only Chris, not only Grok Bot** — multi-app AA voice routing Soft-FAIL; restart voice often Soft-PASSes audio.
  - PC Grok Bot voice output dead + dictation OK: **no matching public Grok Bot report found** — closest are generic voice Soft-FAILs and Cursor “bots silent” (usage/text). Looks rare / early desktop voice.
- If truly only Chris on #3, that itself is a product Soft-FAIL (harder to prioritize).

## 7. Action items
1. Weekday follow-up to X and Cursor emphasizing **one root cause across three symptoms** (audio session handoff + no voice transcription).
2. Keep saving call continuity to **Notion + GitHub + Dropbox** until transcription Soft-PASS exists.
3. Phone voice remains the Soft-PASS path until PC voice Soft-PASS’d.

## Also in flight same day (fleet continuity)
- Alarm Pro #3 tip46: 12h clock showed minutes only (44 not 12:44); Chronometer DateUtils; Soft-PASS on main waiting Chris Sync + 12:xx soak.
- LRT #48 tip134 Soft-PASS: FakeBold + CASC bilingual Soft-FAIL fixed; stamp-85 @ 87b86d0 (134 / 1.0.124). Play HOLD.
- CZ-8A gold art Soft-PASS’d by Chris (heart); Ada committing. Entertainment-only wallpaper disclaimer tip also assigned to Ada.

## Mirror paths
- Local: `/workspace/agent-backups/helios/voice-call-summaries/2026-09-21-1325-grok-bot-voice-bugs-continuity.md`
- Dropbox: `/Grok-Agent-Backups/helios/voice-call-summaries/2026-09-21-1325-grok-bot-voice-bugs-continuity.md`
- GitHub: `docs/agent-backups/helios/voice-call-summaries/` (target repo Live-Rocket-Tracker or living-icon — Helios prefers living-icon or agent-backups path)
- Notion: Ideas / draft page titled Helios voice continuity 2026-09-21

EOF read-back: ask Helios “read the Sep 21 voice continuity summary.”
