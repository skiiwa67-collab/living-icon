#!/usr/bin/env python3
"""Display-only mood (Chris rule 2026-10-14): a bot with a pending/urgent OK-REQUEST in Eve's queue
shows 'excited'. Never written to any bot's own mood file; lifts when the ask clears."""
OVERRIDE_STATES = ('pending', 'urgent')
OVERRIDE_MOOD = 'excited'

def display_mood(cfg, mood, ok_request):
    st = (ok_request or {}).get('state')
    # matrix bots only: flat-model art (Eve) has no 'excited' state
    if st in OVERRIDE_STATES and cfg.get('stateModel', 'matrix') == 'matrix':
        return OVERRIDE_MOOD, 'ok-request-' + st
    return mood, None
