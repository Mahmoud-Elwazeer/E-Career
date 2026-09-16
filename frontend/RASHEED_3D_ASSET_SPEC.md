# Rasheed — 3D Interactive Character Asset Spec (v2, production)

This is the **authoritative production brief** for the Rasheed 3D character asset.
The frontend integration (React Three Fiber renderer + semantic state machine +
graceful fallback) is **already built and deployed**. This document is the exact
contract the asset must satisfy. The integration code is the source of truth;
every requirement below is enforced by the automated validator
(`src/components/rashid/validateRasheedGlb.ts`) and reported in dev via the
`?rasheedCheck=1` overlay.

> **Status:** the production `rasheed.glb` does **not exist yet**. Until a file
> that PASSES validation is placed at `frontend/public/models/rasheed.glb`, the
> app deliberately stays on the animated vector fallback. A GLB that loads but
> is missing rig/morphs/clips is **not** an acceptable deliverable.

> **Identity:** Rasheed is a warm, professional Middle‑Eastern **male HR / career
> coach** for the USAM platform (jobs.usamif.com). Brand teal `#0A3836` suit,
> `#2A8F88` tie, off-white shirt, approachable confident smile, short dark hair,
> neat short beard. Use the existing vector Rasheed + the product screenshots as
> the identity reference. This must read as **Rasheed specifically**, not a
> generic avatar.

---

## 0. Why this spec changed (verify, don't assume)

Ready Player Me — previously the fastest path — **shut down its public platform
and APIs on 31 January 2026** after being acquired by Netflix. It is no longer a
viable production source. This v2 spec removes RPM and lists only tools verified
active as of this writing. Re-verify any tool's status before committing budget.

---

## 1. Delivery: format, path, budget

| Item | Requirement |
|---|---|
| **Format** | glTF 2.0 **binary `.glb`**, single self-contained file, embedded textures |
| **Drop-in path** | `frontend/public/models/rasheed.glb` (served at `/models/rasheed.glb`) |
| **Optional mobile LOD** | `frontend/public/models/rasheed-low.glb` (optional) |
| **File size** | ≤ **6 MB** target, **10 MB hard cap** (Draco or meshopt compression OK) |
| **Triangles** | ≤ ~50k (half-body) / ≤ ~90k (full-body) |
| **Textures** | PBR metal-rough, ≤ 2048² albedo, ORM packed; KTX2/Basis preferred |
| **Draw calls** | ≤ ~6 meshes/materials (body, head, hair, eyes, teeth, prop) |

## 2. Orientation, scale, framing

- **Y-up, faces −Z** (toward camera). Real-world **meters**.
- Standing height ~1.7–1.8 units; the renderer frames the **bust** by default
  (camera target ~`y=1.45`) and can switch to `full`. Deliver **full-body** so
  both framings work; the app crops to the bust for hero/companion.
- Origin at feet (hips acceptable). Symmetrical A/T rest pose.

## 3. Skeleton / rig — REQUIRED (validator checks bone names)

- **Humanoid, Mixamo-compatible bone names.** Prefix `mixamorig:` is expected but
  the validator also accepts unprefixed standard names.
- **Must contain a head bone** named `Head` / `mixamorig:Head` (NOT only
  `HeadTop_End`). The renderer rotates this bone for head-gaze.
- Required core chain: `Hips, Spine, Spine1, Spine2, Neck, Head`,
  `LeftShoulder/Arm/ForeArm/Hand`, `RightShoulder/Arm/ForeArm/Hand`,
  `Left/RightUpLeg/Leg/Foot`. Fingers strongly recommended (pointing/holding).
- The body mesh must be a **skinned mesh** bound to this skeleton (the renderer
  deep-clones with skeleton rebinding — non-skinned static meshes will not
  animate).

## 4. Facial morph targets — REQUIRED (validator checks morph names)

The face mesh's `morphTargetDictionary` **must** contain these names (exact,
case-sensitive). These are the ones the renderer reads directly:

**Expressions / gaze / blink (required — 21):**
```
mouthSmileLeft, mouthSmileRight, mouthFrownLeft, mouthFrownRight,
cheekSquintLeft, cheekSquintRight, browInnerUp, browOuterUpLeft,
browOuterUpRight, browDownLeft, browDownRight, eyeSquintLeft, eyeSquintRight,
eyeBlinkLeft, eyeBlinkRight, eyeLookOutLeft, eyeLookOutRight, eyeLookInLeft,
eyeLookInRight, eyeLookUpLeft, eyeLookUpRight
```
(plus `eyeLookDownLeft, eyeLookDownRight, jawOpen`)

**Full ARKit 52** is strongly recommended (superset of the above) so future
expressions/capture work without re-exporting. Standard ARKit naming.

**Lip-sync visemes (required for talking — 15 Oculus):**
```
viseme_sil, viseme_PP, viseme_FF, viseme_TH, viseme_DD, viseme_kk,
viseme_CH, viseme_SS, viseme_nn, viseme_RR, viseme_aa, viseme_E,
viseme_I, viseme_O, viseme_U
```
If only ARKit is present, `jawOpen` alone yields a basic talking flap, but
**visemes are required for real lip-sync** and are part of the acceptance bar.

## 5. Animation clips — REQUIRED (validator checks clip names)

Clips baked into the GLB (or delivered as named Mixamo FBX for retarget). The
renderer matches by **case-insensitive substring**, so any listed alias works;
exact names in the left column are safest.

| Semantic state | Clip name (or alias the name contains) |
|---|---|
| `idle` | `Idle` (`breathing`, `stand`) |
| `greeting` | `Greeting` (`wave`, `hello`) |
| `talking` | `Talking` (`talk`, `speak`, `gesture`) |
| `listening` | `Listening` (`listen`, `attentive`) |
| `thinking` | `Thinking` (`think`, `ponder`, `idea`) |
| `pointing` | `Pointing` (`point`) |
| `holdingScreen` | `HoldingScreen` (`presenting`, `present`, `showing`, `phone`) |
| `reacting` | `Reacting` (`react`, `nod`, `acknowledge`) |
| `celebrating` | `Celebrating` (`celebrate`, `cheer`, `victory`, `fistpump`) |

- `idle/talking/listening/thinking/holdingScreen` loop seamlessly.
- `greeting/reacting/celebrating/pointing` may be one-shots (the app auto-returns
  to idle). Mixamo Library clips retargeted onto the rig satisfy this section.

## 6. Prop socket (phone/screen) — RECOMMENDED

- A node named `RightHandProp` parented to the right hand, positioned in the
  palm, so the app can attach a phone/screen and draw live UI on it.
- Optional low-poly phone mesh `PhoneScreen` with a flat front quad whose
  material the app can swap for a render target. If absent, the app anchors an
  HTML card to the projected socket position (already implemented).

## 7. Materials / look

- PBR metal-rough. Skin: mid roughness, low metalness, subtle SSS look.
- Suit teal `#0A3836`; tie `#2A8F88`; shirt off-white. Eyes separate material
  with spec highlight. No harsh baked shadows in albedo (scene lights handle it).
- **CC4 caveat:** Character Creator exports can carry non-uniform bone scale that
  stretches limbs in three.js during procedural bone control. If using CC4,
  apply the community fix (e.g. Auto-Avatar-Fixer) / bake uniform scale before
  export, and re-run the validator.

## 8. Interaction contract (already implemented — do NOT rebuild)

The app drives Rasheed by **semantic state only**, never by timeline. This is
the stable contract the asset plugs into:

```ts
type RasheedStateName =
  | "idle" | "greeting" | "talking" | "listening"
  | "thinking" | "pointing" | "holdingScreen" | "reacting" | "celebrating";

interface RasheedInputs {
  state: RasheedStateName;
  gaze?: { x: number; y: number };   // -1..1 head/eye look target (pointer)
  visemes?: Float32Array;            // 15 Oculus viseme weights (TTS lip-sync)
  expression?: "neutral" | "happy" | "encouraging" | "focused";
  message?: string;
}
```

Implemented in `rasheed-state.tsx` (`useRasheed`), consumed by
`RasheedAvatar3D.tsx`. Future TTS/AI: write `state` + per-frame `visemes` from a
backend agent — no renderer change needed.

## 9. How to actually PRODUCE Rasheed (verified-active options, ranked)

The requirement is a **custom Rasheed identity**, not a generic avatar. Ranked by
fit for "custom + realistic + web-ready + rigged + affordable":

1. **Reallusion Character Creator 4 + Headshot 3 (recommended in-house path).**
   Build a realistic male digital human, use Headshot to shape the face toward
   Rasheed's identity from reference images, style the teal suit, auto-includes
   facial blendshapes; export **GLB**. Add Mixamo body clips (§5). Apply the CC4
   bone-scale fix (§7) and validate. Active, commercial, one-time license.
2. **Freelance 3D character artist (recommended if no in-house 3D skills).**
   Commission a custom Rasheed to THIS spec. A real market exists for exactly
   this deliverable ("rig avatar for webapp, ARKit52 + Oculus visemes, three.js
   GLB"). Hand them this file as the brief + acceptance checklist.
3. **Blender (free) full custom.** Model/sculpt or start from a base mesh
   (MakeHuman/HumanGen) → Rigify or Mixamo auto-rig → add ARKit shape keys
   (ARKit-Creator addon) + Oculus visemes → export GLB. Most control, most labor.
4. **MetaHuman (secondary).** Highest photoreal fidelity but Unreal-centric; GLB
   export is not first-class and needs conversion + rig/blendshape remap. Use
   only if photoreal cinematic quality is the priority and someone owns the
   conversion pipeline.

**Do not** use a generic/stock avatar as the shipped Rasheed.

## 10. Acceptance checklist (must ALL pass — enforced by the validator)

- [ ] File at `frontend/public/models/rasheed.glb`, loads in GLTFLoader, ≤ 10 MB
- [ ] Skinned mesh + Mixamo-named skeleton incl. a real `Head` bone
- [ ] `morphTargetDictionary` contains all 24 required expression/gaze/jaw morphs (§4)
- [ ] 15 Oculus `viseme_*` morphs present (real lip-sync)
- [ ] Animation clips resolve for all 9 semantic states (§5)
- [ ] Faces −Z, Y-up, meters, sensible scale; full-body
- [ ] (Recommended) `RightHandProp` socket present
- [ ] Reads as **Rasheed** (identity, brand palette), professional public quality

Run the validator: open the site with `?rasheedCheck=1` (dev) — it prints a
PASS/FAIL report of every item above against the actual file. Only a PASS means
the Rasheed 3D task is truly complete.
