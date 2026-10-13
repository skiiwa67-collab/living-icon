# Eve Living Icon: transitions spec (DRAFT v3, 2026-10-13)
Shared base pose (frame 0 and the last frame of every loop): orb radius 150 px (on a 512 canvas, centered at 256,236), glow mix 35% teal / 65% amber,
brightness 0.90, halo falloff 55 px, smile 0.6, eyes fully open. Every mood eases out of the base and back into it, so any mood can crossfade to any other.
Colors: amber #FFA537, teal #23CDC3, gold bar #FFC828, background #10141E. Loop length 2.0 s at 20 fps (40 frames).
Peak envelope sin^2(pi*t), except interrupt and frustrated, which have their own envelopes (below).

| mood | glow (teal mix) | brightness | radius | halo | pulse / motion |
|---|---|---|---|---|---|
| idle | 0.35 | 0.90→1.00 | 150 | 55→65 | 1 breath per 2 s; eye blink at t=0.85 |
| listening | 0.35 | 1.00 | 150→154 | 55 | 3 ripple rings, 1 cycle/s, radius +8→+88 px fading out |
| thinking | 0.55 | 0.90 | 150 | 55 | 3 sparkles orbiting (ellipse r+32, y×0.42), 1 orbit/s; smile 0.15 |
| interrupt | 0.00 (full amber) | 1.25 hold; 4 Hz blinks in first 0.5 s | 150 | 80 | blink then hold; eases in over 0–0.12 and out over 0.85–1.0 |
| happy | 0.25 | 1.30 | 150→162 | 95 | 1 bloom per 2 s; smile 1.0, eyes squint (height ×0.55) |
| waiting | 1.00 (full teal) | 0.60 | 150 | 45 | steady, dim; eyes 0.75 opacity |
| dnd | 0.70 | 0.50 | 150 | 40 | rocket glint top right, twinkles 2 Hz; flat mouth, eyes 0.55 |
| frustrated | 0.10 | 1.10 with 7 Hz flicker (−35% max) | 150 | 60 | slanted brows plus ±3 px x-jitter during 0.08–0.40 s of the loop, then eases back to idle by t=1.0 |

Tween in code: lerp every numeric parameter over 0.4 s with smoothstep easing (s*s*(3-2s)). Overlay elements (rings, sparkles, rocket, brows) fade by their weight 0→1.
transitions.gif previews this, with each mood held about 0.6 s and a 0.4 s eased crossfade to the next.
