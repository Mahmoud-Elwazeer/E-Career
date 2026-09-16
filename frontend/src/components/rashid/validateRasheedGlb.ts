import * as THREE from "three";
import type { GLTF } from "three-stdlib";

/**
 * validateRasheedGlb — automated acceptance check for the Rasheed 3D asset.
 *
 * Given a loaded GLTF, verify it satisfies EXACTLY what RasheedAvatar3D consumes:
 *   - a skinned mesh + humanoid skeleton with a real Head bone (gaze)
 *   - the required facial morph targets (expressions / gaze / jaw)
 *   - the 15 Oculus visemes (lip-sync)
 *   - an animation clip resolvable for each of the 9 semantic states
 *
 * These constants are the single source of truth mirrored in
 * RASHEED_3D_ASSET_SPEC.md. If the renderer's contract changes, change it here
 * too. The result drives both the dev overlay (?rasheedCheck=1) and the
 * production gate (a GLB that fails is treated as "not present" -> fallback).
 */

// ── Required contract (mirrors RasheedAvatar3D + the spec) ──────────────────
export const REQUIRED_HEAD_BONE = /(^|:)head$/i; // matches "Head" / "mixamorig:Head"

export const REQUIRED_EXPRESSION_MORPHS = [
  "mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight",
  "cheekSquintLeft", "cheekSquintRight", "browInnerUp", "browOuterUpLeft",
  "browOuterUpRight", "browDownLeft", "browDownRight", "eyeSquintLeft",
  "eyeSquintRight", "eyeBlinkLeft", "eyeBlinkRight", "eyeLookOutLeft",
  "eyeLookOutRight", "eyeLookInLeft", "eyeLookInRight", "eyeLookUpLeft",
  "eyeLookUpRight", "eyeLookDownLeft", "eyeLookDownRight", "jawOpen",
] as const;

export const REQUIRED_VISEMES = [
  "viseme_sil", "viseme_PP", "viseme_FF", "viseme_TH", "viseme_DD",
  "viseme_kk", "viseme_CH", "viseme_SS", "viseme_nn", "viseme_RR",
  "viseme_aa", "viseme_E", "viseme_I", "viseme_O", "viseme_U",
] as const;

// Semantic state -> accepted clip-name substrings (mirrors CLIP_ALIASES).
export const CLIP_ALIASES: Record<string, string[]> = {
  idle: ["idle", "breathing", "stand"],
  greeting: ["greeting", "wave", "hello"],
  talking: ["talking", "talk", "speak", "gesture"],
  listening: ["listening", "listen", "attentive"],
  thinking: ["thinking", "think", "ponder", "idea"],
  pointing: ["pointing", "point"],
  holdingScreen: ["holdingscreen", "presenting", "present", "showing", "phone"],
  reacting: ["reacting", "react", "nod", "acknowledge"],
  celebrating: ["celebrating", "celebrate", "cheer", "victory", "fistpump"],
};

export interface CheckResult {
  ok: boolean;
  label: string;
  detail?: string;
}

export interface RasheedGlbReport {
  pass: boolean;
  /** Hard requirements that must all pass for the asset to be usable. */
  required: CheckResult[];
  /** Recommended (not blocking) — quality/completeness signals. */
  recommended: CheckResult[];
  summary: {
    bones: number;
    skinnedMeshes: number;
    morphNames: string[];
    clipNames: string[];
    triangles: number;
  };
}

function collect(gltf: GLTF) {
  const boneNames: string[] = [];
  const morphNames = new Set<string>();
  let skinnedMeshes = 0;
  let triangles = 0;

  gltf.scene.traverse((obj) => {
    const anyObj = obj as THREE.Object3D & {
      isBone?: boolean;
      isSkinnedMesh?: boolean;
      morphTargetDictionary?: Record<string, number>;
      geometry?: THREE.BufferGeometry;
    };
    if (anyObj.isBone) boneNames.push(obj.name);
    if (anyObj.isSkinnedMesh) skinnedMeshes++;
    if (anyObj.morphTargetDictionary) {
      Object.keys(anyObj.morphTargetDictionary).forEach((k) => morphNames.add(k));
    }
    const geom = anyObj.geometry;
    if (geom) {
      const idx = geom.getIndex();
      const pos = geom.getAttribute("position");
      if (idx) triangles += idx.count / 3;
      else if (pos) triangles += pos.count / 3;
    }
  });

  const clipNames = (gltf.animations ?? []).map((c) => c.name);
  return { boneNames, morphNames, skinnedMeshes, triangles: Math.round(triangles), clipNames };
}

function resolveClip(clipNames: string[], aliases: string[]): string | null {
  const lower = clipNames.map((n) => n.toLowerCase());
  for (const alias of aliases) {
    const i = lower.findIndex((n) => n.includes(alias));
    if (i !== -1) return clipNames[i];
  }
  return null;
}

export function validateRasheedGlb(gltf: GLTF): RasheedGlbReport {
  const { boneNames, morphNames, skinnedMeshes, triangles, clipNames } = collect(gltf);

  const required: CheckResult[] = [];
  const recommended: CheckResult[] = [];

  // 1) Skinned mesh present.
  required.push({
    ok: skinnedMeshes > 0,
    label: "Skinned mesh present",
    detail: `${skinnedMeshes} skinned mesh(es)`,
  });

  // 2) Head bone present.
  const hasHead = boneNames.some((b) => REQUIRED_HEAD_BONE.test(b));
  required.push({
    ok: hasHead,
    label: "Head bone present (gaze)",
    detail: hasHead ? "found" : `no bone matching /(:)?head$/ in ${boneNames.length} bones`,
  });

  // 3) Required facial morphs.
  const missingMorphs = REQUIRED_EXPRESSION_MORPHS.filter((m) => !morphNames.has(m));
  required.push({
    ok: missingMorphs.length === 0,
    label: `Facial morphs (${REQUIRED_EXPRESSION_MORPHS.length} required)`,
    detail: missingMorphs.length ? `missing ${missingMorphs.length}: ${missingMorphs.join(", ")}` : "all present",
  });

  // 4) Visemes (lip-sync).
  const missingVisemes = REQUIRED_VISEMES.filter((v) => !morphNames.has(v));
  required.push({
    ok: missingVisemes.length === 0,
    label: `Oculus visemes (${REQUIRED_VISEMES.length} required)`,
    detail: missingVisemes.length ? `missing ${missingVisemes.length}: ${missingVisemes.join(", ")}` : "all present",
  });

  // 5) A clip for every semantic state.
  const unresolved: string[] = [];
  for (const [state, aliases] of Object.entries(CLIP_ALIASES)) {
    if (!resolveClip(clipNames, aliases)) unresolved.push(state);
  }
  required.push({
    ok: unresolved.length === 0,
    label: `Animation clips for 9 states`,
    detail: unresolved.length ? `no clip for: ${unresolved.join(", ")}` : `${clipNames.length} clips cover all states`,
  });

  // ── Recommended (non-blocking) ────────────────────────────────────────────
  const hasProp = boneNames.some((b) => /righthandprop/i.test(b)) ||
    !!gltf.scene.getObjectByName("RightHandProp");
  recommended.push({ ok: hasProp, label: "RightHandProp socket", detail: hasProp ? "found" : "not found (HTML card fallback used)" });

  const arkitFull = ["noseSneerLeft", "mouthPucker", "cheekPuff", "tongueOut"].every((m) => morphNames.has(m));
  recommended.push({ ok: arkitFull, label: "Full ARKit 52 (superset)", detail: arkitFull ? "present" : "partial — future expressions may need re-export" });

  const triOk = triangles > 0 && triangles <= 120000;
  recommended.push({ ok: triOk, label: "Triangle budget ≤ ~120k", detail: `${triangles.toLocaleString()} tris` });

  const pass = required.every((r) => r.ok);

  return {
    pass,
    required,
    recommended,
    summary: {
      bones: boneNames.length,
      skinnedMeshes,
      morphNames: Array.from(morphNames).sort(),
      clipNames,
      triangles,
    },
  };
}

/** Console-friendly formatter for the dev overlay / logs. */
export function formatReport(report: RasheedGlbReport): string {
  const line = (r: CheckResult) => `  ${r.ok ? "PASS" : "FAIL"}  ${r.label}${r.detail ? ` — ${r.detail}` : ""}`;
  return [
    `Rasheed GLB validation: ${report.pass ? "PASS ✅" : "FAIL ❌"}`,
    "Required:",
    ...report.required.map(line),
    "Recommended:",
    ...report.recommended.map(line),
    `Summary: ${report.summary.bones} bones, ${report.summary.skinnedMeshes} skinned, ` +
      `${report.summary.morphNames.length} morphs, ${report.summary.clipNames.length} clips, ` +
      `${report.summary.triangles.toLocaleString()} tris`,
  ].join("\n");
}
