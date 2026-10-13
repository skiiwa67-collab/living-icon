# OK-request overlay: spec for Ada (DRAFT 2026-10-13)
**What it is:** a corner badge that shows any bot is waiting on Chris's OK. It contains no text.
**Files:** {128,1024}/badge-{state}.gif, plus {128,1024}/{state}/frame-NN.png (transparent RGBA). Each frame is full-canvas, same size as the icon, with the badge already placed.
**Anchor:** top-right. Badge center at (83%, 17%) of icon width/height. Outer radius 13% of icon (diameter 26%), plus a soft 2.5% shadow.
Inner content (dot / check) stays inside a 6% radius. At 48px the badge is about 12px across.
**States** (20 fps):
- pending: gold ring, amber dot, 1 pulse per 2 s (40 frames, loops).
- urgent: red outer edge + gold ring, 3 pulses per 2 s (40 frames, loops). Use when priority:true and now − since > 10 min.
- approved: green ring + check. Pops in over 0.1 s, then fades to fully transparent by 1.0 s (20 frames, plays once, no loop). Then remove the overlay.
**Feed field** (proposed addition to living-icon-status-feed/v1, per agent):
  "ok_request": { "state": "none|pending|urgent|approved", "ask_id": "<id>", "since": "<ISO8601 with offset>", "priority": true|false }
  Ada computes urgent from priority + since, or the bot writes it directly. state "approved" is shown once, then becomes "none".
**Compositing order** (bottom → top): plate → bot Living Icon (mood/voice GIF frame) → OK-request badge → any UI chrome.
The badge animates on its own clock; do not sync it to the mood loop. Mood crossfades happen under it unchanged.
GIF note: the GIFs use 1-bit transparency (soft shadow is clipped). For smooth edges in the web dashboard, use the PNG frames or draw the badge in code from these numbers.
