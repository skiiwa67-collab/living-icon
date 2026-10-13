# Perseus: transitions spec (DRAFT 2026-10-13)
Shared base pose (frame 0 and the last frame of every mood × voice loop): orb radius 150 on a 512 grid (center 256,236), brightness 0.90,
halo 50 px blue #326ED7, network opacity 0.55, eyes open, smile 0.5, no brow, no rim tint. Loops are 2.0 s at 20 fps. Envelope sin²(πt);
angry uses an ease-in over 0–0.08 and an ease-out over 0.5–1.0, with a 7 Hz flicker (−25%) during 0.08–0.45.

| mood | glow color | brightness | radius | halo | network | face / pulse |
|---|---|---|---|---|---|---|
| calm | blue | 0.90→1.00 | 150 | 50→60 | 0.55 | 1 breath per 2 s; blink at t=0.85 |
| excited | blue | 1.15 | 154 | 75 | 0.95 | smile 0.85; stars twinkle 2 Hz |
| somber | blue (dim) | 0.60 | 150 | 40 | 0.30 | eyes half-lidded (0.5), smile 0.15 |
| angry | red rim, 60% mix | 1.05 + flicker | 150 | 50 | 0.40 | slanted brows, eyes 0.7, flat mouth; settles to calm |
| thrilled | blue + silver bloom | 1.30 | 160 | 100 | 1.00 | smile 1.0, squint 0.6 |

Voice overlays: listening = 3 silver ripple rings, 1 cycle/s. Talking = mouth oval opening at 3 Hz plus a 6 px bob at 2 Hz.
Ada tween: lerp every numeric parameter over 0.4 s with smoothstep. transitions.gif holds each mood 0.6 s, then crossfades over 0.4 s.
