# Living Icon — Helios Mood Spec (v1)

**Official name:** Living Icon (two words). Do not letter the name into assets.  
**Worked example:** Helios — small living sun with eyeballs.  
**Creative seed:** something ALIVE inside a frame — presence, glow, eyes, motion contained in a shape; personality leaking past the edges.

## Visual-state → mood map

| Mood | Corona | Eyes | Rotation / flare energy | Color temp |
|------|--------|------|-------------------------|------------|
| **Calm** | Soft, even ring; short symmetric rays (~8) | Soft open lids (~5% cover); steady sclera; warm brown iris | Low — gentle pulse feel; minimal ember spill | Warm gold / amber (~3200–4000K feel) |
| **Excited** | Brighter outer glow; longer active flares (~12) + secondary thin rays | Wide; higher brightness; stronger catchlights | Mid–high — asymmetric flare lengths; ember particles | Hotter amber / orange (~4500K+) |
| **Somber** | Dim, thin cool haze; few short faint rays (~6) | Half-lidded (~50% cover); cooler iris/sclera; lower brightness | Very low — heavy / slow; sparse spill | Cool slate / muted amber (~5500K cool bias) |
| **Thrilled** | Full flare burst (~16) filling frame; strong outer leak | Fully wide; max brightness; eye-local glow | Max — long flares, dense sparks, personality past circular bound | Peak warm-white core + deep orange rim |

### Shared Helios invariants
- Circular body as the “frame”; flares/embers may leak past it (presence).
- Personality carried primarily by **eyes + corona energy** (no mouth required).
- Readable at tiny sizes (app avatar): high contrast eyes, clear disc silhouette.
- No text / letters / wordmarks in any frame.
- Alive, not cute-cloying — graphic iconic mark, not sticker-mascot.

## Alternate name-inspired directions (heroes)

| File | Idea |
|------|------|
| `alts/alt-flame-face.png` | Flame with a face / presence |
| `alts/alt-lantern-heartbeat.png` | Lantern with heartbeat / living light inside |
| `alts/alt-crystal-motion.png` | Crystal with something moving/living inside |

## File list

```
/workspace/living-icon/
  SPEC.md
  helios/
    helios-calm.png          # 1024×1024
    helios-excited.png       # 1024×1024
    helios-somber.png        # 1024×1024
    helios-thrilled.png      # 1024×1024
    storyboard-sheet.png     # 1920×1080 (calm→excited→somber→thrilled)
  alts/
    alt-flame-face.png       # 1024×1024
    alt-lantern-heartbeat.png
    alt-crystal-motion.png
  docs/concepts/             # copies of finals + SPEC
```

## Recommended icon sizes

| Use | Size | Notes |
|-----|------|-------|
| Master / source | **1024×1024** | Current masters |
| App avatar / bot face | **512×512** | Primary runtime |
| Dense UI / list | **256×256**, **128×128** | Eyes must remain round + high-contrast |
| Favicon / badge | **64×64**, **32×32** | Prefer disc+eyes only; drop fine flares if muddy |
| Storyboard / review | **1920×1080** sheet | Mood dots under panels (no lettering) |

**Export tip:** Downscale from 1024 with Lanczos; keep a warm near-black plate (`#0C0A12`–`#140C10` range) so corona reads on both light and dark chrome.

## Driver note (Soft-PASS path)
Turn expresses mood → swap avatar to matching Helios asset. GIF Soft-FAIL until proven; still frames + pack swap is the minimal Living Icon path.

*Da Vinci concept pass — 2026-09-19 CT*
