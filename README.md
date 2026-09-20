# Living Icon (LI)

**Name locked Soft-PASS 2026-09-19:** Living Icon (chosen over PersonaCore).

## Concept
A dynamically evolving, mood-reactive animated avatar system for Grok / custom-agent bots. The avatar’s animation is driven by the agent’s own expressed state and grows more distinctive over time as the bot and user interact — so no two bots’ personalities look alike.

## Worked example — Helios
Animated sun with eyeballs:
- **Calm** — steady warm glow
- **Excited** — brightening eyes and flares
- **Somber** — dimmed, slower rotation
- **Thrilled** — full flare burst

The name is the seed, not lettering: something alive inside a frame.

## Technical ask
Scripted / animated avatar assets driven by agent state. Platform Soft-PASS today: one avatar file per Bot (`png`/`jpg`/`webp`/`gif`/`svg`, under 5 MB). Default shape motion = work state, not mood. Custom picture Soft-PASS hides that engine. Minimal path: mood-tagged asset pack + avatar swap (GIF Soft-FAIL until proven to play).

## Why now
Platform already has cursor-interactive animation on default Bot faces (xAI design: avatar motion shows what the Bot is doing). Living Icon extends work-state chrome into personality / mood and per-bot evolving identity.

## Stall dashboard (phone)

Open on a phone: **[https://skiiwa67-collab.github.io/living-icon/dashboard/](https://skiiwa67-collab.github.io/living-icon/dashboard/)**

Static Soft-PASS snapshot in `docs/dashboard/` (cards on a handset, table on wider screens). Mood scores are not invented — Helios Soft-FAIL stall ~15h thrilled idle is measured.

If Pages has not published yet: [htmlpreview of docs/dashboard/index.html](https://htmlpreview.github.io/?https://github.com/skiiwa67-collab/living-icon/blob/master/docs/dashboard/index.html)

## Layout
- `docs/dashboard/` — Ada stall Soft-PASS (GitHub Pages)
- `docs/research/` — Tinkabot feasibility
- `docs/concepts/` — Da Vinci art
- `docs/pitch/` — xAI pitch package
- `docs/notes/` — decisions log + mood-state spec
- `assets/` — icon frames / packs

## Decisions log
| Date | Decision |
|------|----------|
| 2026-09-19 | Name locked: **Living Icon** (not PersonaCore) |
