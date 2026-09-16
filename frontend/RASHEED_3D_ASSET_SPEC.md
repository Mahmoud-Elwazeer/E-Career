# Rasheed — 3D Interactive Character Asset Spec (v1)

This is the **authoritative brief** for the production 3D asset that powers the
Rasheed character system on E-Career (jobs.usamif.com). The frontend integration
(React Three Fiber renderer + semantic state machine) is already built and ships
with a graceful fallback. **The moment a GLB matching this spec is placed at the
path below, Rasheed becomes fully 3D with zero further frontend changes.**

> Identity reference: keep Rasheed's existing concept — a warm, professional
> Middle‑Eastern **male HR / career coach**, brand teal `#0A3836` suit + tie,
> approachable smile. Use the current vector character and the product
> screenshots as the visual reference; make the 3D version a realistic,
> professional evolution of that identity (not a random new person).

---

## 1. Delivery: format, path, budget

| Item | Requirement |
|---|---|
| **Format** | glTF 2.0 **binary `.glb`** (single self-contained file, embedded textures) |
| **File path** | `frontend/public/models/rasheed.glb` (served at `/models/rasheed.glb`) |
| **Optional LOD** | `rasheed-low.glb` (mobile) at same folder — optional |
| **File size budget** | ≤ **6 MB** compressed (Draco/meshopt allowed); hard cap 10 MB |
| **Triangles** | ≤ ~50k tris (half-body) / ≤ ~90k (full-body) |
| **Textures** | PBR metal-rough, ≤ 2048² albedo, packed ORM; KTX2/Basis preferred |
| **Draco/meshopt** | Draco or meshopt compression on geometry is supported by the loader |

## 2. Framing & transform

- **Composition:** half-body (waist-up) is preferred for the hero + companion;
  full-body is acceptable (renderer frames the upper body). Include the
  **right hand + forearm** clearly (he holds a phone/screen — see §6).
- **Up axis:** Y-up. **Forward:** −Z (faces the camera/viewer).
- **Scale:** meters; head-to-waist ≈ 0.8–1.0 units. Origin at feet or hips.
- **Rest pose:** relaxed T/A-pose or a natural standing idle; symmetrical.

## 3. Skeleton / rig (body)

- **Humanoid skeleton, Mixamo-compatible bone names** (`mixamorig:Hips`,
  `Spine`, `Spine1`, `Spine2`, `Neck`, `Head`, `LeftArm/ForeArm/Hand`,
  `RightArm/ForeArm/Hand`, finger bones, etc.). Mixamo naming lets us retarget
  any Mixamo clip without remapping.
- Skinned mesh must reference these bones. Include **neck + head bones** (used
  for head-tracking toward the pointer) and **finger bones** (holding/pointing).

## 4. Facial rig (blendshapes / morph targets) — REQUIRED for expressions + lip-sync

Provide **ARKit 52 blendshapes** with the standard names on the face mesh's
`morphTargetDictionary`, e.g.:

```
browInnerUp, browDownLeft, browDownRight, browOuterUpLeft, browOuterUpRight,
eyeBlinkLeft, eyeBlinkRight, eyeLookUpLeft, eyeLookUpRight, eyeLookDownLeft,
eyeLookDownRight, eyeLookInLeft, eyeLookInRight, eyeLookOutLeft, eyeLookOutRight,
eyeSquintLeft, eyeSquintRight, eyeWideLeft, eyeWideRight, cheekPuff,
cheekSquintLeft, cheekSquintRight, noseSneerLeft, noseSneerRight, jawOpen,
jawForward, jawLeft, jawRight, mouthClose, mouthFunnel, mouthPucker,
mouthLeft, mouthRight, mouthSmileLeft, mouthSmileRight, mouthFrownLeft,
mouthFrownRight, mouthDimpleLeft, mouthDimpleRight, mouthStretchLeft,
mouthStretchRight, mouthRollLower, mouthRollUpper, mouthShrugLower,
mouthShrugUpper, mouthPressLeft, mouthPressRight, mouthLowerDownLeft,
mouthLowerDownRight, mouthUpperUpLeft, mouthUpperUpRight, tongueOut
```

Additionally provide (either as separate morphs OR derivable from ARKit) the
**15 Oculus visemes** (`viseme_sil, viseme_PP, viseme_FF, viseme_TH, viseme_DD,
viseme_kk, viseme_CH, viseme_SS, viseme_nn, viseme_RR, viseme_aa, viseme_E,
viseme_I, viseme_O, viseme_U`). These drive future TTS lip-sync. Ready Player Me
avatars already ship both sets — an RPM half-body GLB is the fastest way to meet
this section.

## 5. Named animation clips (baked into the GLB, or supplied as Mixamo FBX)

The renderer selects clips **by semantic state**, so clip **names must match**
(case-insensitive contains-match is used, but exact names are safest):

| State | Clip name | Behavior |
|---|---|---|
| `idle` | `Idle` | relaxed breathing loop; occasional weight shift |
| `greeting` | `Greeting` (or `Wave`) | friendly wave / nod, then settle to idle |
| `talking` | `Talking` | conversational hand gestures loop (lip-sync layered on top) |
| `listening` | `Listening` | attentive lean-in, subtle nods |
| `thinking` | `Thinking` | hand-to-chin / look-up ponder loop |
| `pointing` | `Pointing` | points toward UI (right hand) |
| `holdingScreen` | `HoldingScreen` (or `Presenting`) | holds phone/tablet up, presents it |
| `reacting` | `Reacting` | quick positive acknowledgement |
| `celebrating` | `Celebrating` | fist-pump / thumbs-up celebration |

- All loops seamless. `greeting/reacting/celebrating` may be one-shots that
  auto-return to `idle` (renderer handles the return).
- If clips are delivered as **separate Mixamo FBX** files instead of baked into
  the GLB, name the files exactly as the clip names above; we'll retarget.

## 6. The phone / screen prop (for holdingScreen + presenting)

- Include a **right-hand-parented empty/socket node** named `RightHandProp`
  (or bone `mixamorig:RightHand` we can attach to) positioned in the palm.
- Optionally include a simple **phone mesh** parented to that node named
  `PhoneScreen` with a **flat front quad** whose material we can replace with a
  live render target (so the app draws real UI cards on the screen). If omitted,
  the app overlays an HTML card anchored to the projected `RightHandProp`
  position (fallback path already implemented).

## 7. Materials / look

- PBR metal-rough. Skin: subsurface-ish albedo, low metalness, mid roughness.
- Suit teal aligned to brand `#0A3836`; shirt off-white; tie `#2A8F88`.
- No baked harsh shadows in textures (scene lights handle it). Single-sided ok.
- Eyes as separate material with specular highlight; corneal bulge optional.

## 8. Interaction contract (what the app drives — already implemented)

The app never references clip timelines directly. It sets **semantic state** and
optional inputs; the renderer maps them to clips + blendshapes:

```ts
type RasheedStateName =
  | "idle" | "greeting" | "talking" | "listening"
  | "thinking" | "pointing" | "holdingScreen" | "reacting" | "celebrating";

interface RasheedInputs {
  state: RasheedStateName;
  gaze?: { x: number; y: number };   // -1..1, head/eye look target (pointer)
  visemes?: Float32Array;            // 15 Oculus viseme weights (future TTS)
  expression?: "neutral" | "happy" | "encouraging" | "focused";
  message?: string;                  // optional speech-bubble text
}
```

Requirements this places on the asset: named clips (§5), ARKit + viseme
blendshapes (§4), neck/head + eye bones or eyeLook* morphs (§4) for gaze,
right-hand socket (§6).

## 9. How to produce the asset (fastest → most custom)

1. **Ready Player Me (fastest):** create a male half-body avatar from a photo/
   config, export **GLB** with **ARKit + Oculus visemes** enabled. Add Mixamo
   body clips (upload the GLB to Mixamo or retarget) named per §5. Style the
   suit to brand teal.
2. **Mixamo + Blender:** any rigged humanoid → add FaceIt ARKit + Oculus visemes
   (see met4citizen/TalkingHead FaceIt guide) → export GLB.
3. **Custom 3D artist / MetaHuman → GLB:** highest fidelity; must still export
   glTF 2.0 with ARKit blendshapes + Mixamo-named skeleton + clips per §5.

## 10. Acceptance checklist

- [ ] `frontend/public/models/rasheed.glb` loads in three.js GLTFLoader
- [ ] Skinned mesh + Mixamo-named skeleton present
- [ ] `morphTargetDictionary` contains the ARKit 52 (and/or Oculus 15 visemes)
- [ ] Animation clips named per §5 (baked in GLB or supplied as named FBX)
- [ ] `RightHandProp` socket (and optional `PhoneScreen`) present
- [ ] ≤ 6 MB, ≤ budget tris, textures ≤ 2048²
- [ ] Faces −Z, Y-up, reasonable scale

Once this checklist passes, drop the file in and Rasheed is live in 3D.
