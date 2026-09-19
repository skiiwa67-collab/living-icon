# Living Icon — Helios voice states (drop-in)

Circular animated avatar for voice/talking UI (~64–128px).

## Files
| File | State | Motion |
|------|-------|--------|
| `idle.svg` | idle | slow glow pulse + gentle corona rotate + rare blink |
| `listening.svg` | listening | faster pulse + blink |
| `talking.svg` | talking | bounce + flare + mouth open/close |

## Size
Designed at **128×128** viewBox. Crisp at **64–128px**. Clip to circle in UI if needed (`border-radius: 50%`).

## Format pick (2026-09-19)
**CSS + SVG** (self-contained SMIL/CSS in SVG). Lottie deferred until we own a React host with lottie-web/lottie-react.

## Platform note
Grok Bot today Soft-PASS: one avatar file per bot (`png/jpg/webp/gif/svg`, &lt;5MB). Custom picture hides default work-state chrome. Wire as SVG/GIF swap driven by voice idle/listen/talk.

## Swap
```html
<img src="idle.svg" width="96" height="96" alt="" />
<!-- on listening --> <img src="listening.svg" ...>
<!-- on talking --> <img src="talking.svg" ...>
```

No lettering. Not LRT.

## Animated GIF Soft-PASS (platform avatar)
Platform rejects SVG. Use:
- `idle.gif` — 128×128 loop (primary Soft-PASS avatar)
- `listening.gif` — 128×128
- `talking.gif` — 128×128

All under 5 MB. Set via update_state avatar → idle.gif.
