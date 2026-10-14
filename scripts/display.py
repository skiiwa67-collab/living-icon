#!/usr/bin/env python3
"""Display-only mood (Chris rule 2026-10-14): a bot with a pending/urgent OK-REQUEST in Eve's queue
shows 'excited'. Never written to any bot's own mood file; lifts when the ask clears."""
OVERRIDE_STATES = ('pending', 'urgent')
OVERRIDE_MOOD = 'excited'
# Per-bot override state (each bot's own choice). Eve chose relay-active (2026-10-14).
PER_BOT = {'eve': 'relay-active'}

def display_mood(cfg, mood, ok_request, slug=None):
    st = (ok_request or {}).get('state')
    if st not in OVERRIDE_STATES:
        return mood, None
    if slug in PER_BOT:
        return PER_BOT[slug], 'ok-request-' + st
    # default excited is matrix-only; flat-model art has no 'excited' state
    if cfg.get('stateModel', 'matrix') == 'matrix':
        return OVERRIDE_MOOD, 'ok-request-' + st
    return mood, None
