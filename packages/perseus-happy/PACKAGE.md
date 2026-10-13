# Perseus — Living Icon personality package (DRAFT 2026-10-13)

- **Character:** Perseus, Chris's coordinator: a calm deep-blue orb face with a silver Greek-helm crest and a faint constellation/network ring
- **Mood coverage:** calm, excited, somber, angry, thrilled (SCHEMA names)
- **Voice states:** idle, listening, talking
- **Format:** `matrix/{voice}/{mood}.gif`, 128×128, 2 s loop @ 20 fps; no lettering
- **Platform:** `softpass/avatar-idle.gif` (128) + `softpass/avatar-idle.png` (1024); `perseus-idle.png` 1024 avatar master
- **Palette:** plate #0C0A12, navy #12286E, blue #326ED7, silver #D7E1F0, gold bar #FFC828 (angry adds a red rim, #C83C46)
- **Review extras:** `perseus-{mood}.png` (1024 still), `perseus-{mood}.gif` (512 idle loop), `perseus-moods-sheet.png`, `transitions.gif`, `transitions-spec.md`
- **Status:** idle art set as the Perseus sidebar avatar 2026-10-13 (perseus-idle.png == perseus-calm.png by design). Mood sheet awaiting Chris review; matrix not yet wired by Ada (dashboard reads packages/perseus-happy/matrix, which does not exist yet).
- **Inventory (verified 2026-10-13):** 15/15 matrix GIFs present, 128x128, 40 frames @ 50 ms; transitions.gif 512x512, 45 frames @ 600 ms (5 mood holds + crossfades).
