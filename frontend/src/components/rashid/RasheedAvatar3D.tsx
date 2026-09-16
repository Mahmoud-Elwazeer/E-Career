import { Suspense, useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useGLTF, useAnimations, Environment, ContactShadows } from "@react-three/drei";
import * as THREE from "three";
import type { GLTF } from "three-stdlib";
import { useRasheed, type RasheedStateName, type RasheedExpressionName } from "./rasheed-state";
import { RASHEED_GLB_URL } from "./glb-url";
import { validateRasheedGlb, formatReport } from "./validateRasheedGlb";

/**
 * RasheedAvatar3D — the real-time 3D renderer for the Rasheed character.
 *
 * Loads a rigged GLB (see frontend/RASHEED_3D_ASSET_SPEC.md) from a FIXED path
 * and drives it purely from SEMANTIC STATE (via useRasheed):
 *   - semantic state  -> animation clip (AnimationMixer crossfade)
 *   - expression      -> ARKit blendshape pose (smile / brows)
 *   - gaze            -> head bone + eyeLook* morphs toward pointer
 *   - visemes         -> Oculus viseme morphs (future TTS lip-sync)
 *
 * It renders NOTHING itself if the asset is missing — the parent
 * (Rasheed3DOrFallback) is responsible for showing the vector fallback. This
 * component only mounts once the GLB is confirmed present, so there is no dead
 * placeholder and no broken canvas.
 */

export { RASHEED_GLB_URL };

// ── Semantic state -> candidate clip names (case-insensitive contains match) ─
const CLIP_ALIASES: Record<RasheedStateName, string[]> = {
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

// ── Expression -> target ARKit morph weights ────────────────────────────────
const EXPRESSION_MORPHS: Record<RasheedExpressionName, Record<string, number>> = {
  neutral: { mouthSmileLeft: 0.08, mouthSmileRight: 0.08, browInnerUp: 0.0 },
  happy: { mouthSmileLeft: 0.55, mouthSmileRight: 0.55, cheekSquintLeft: 0.25, cheekSquintRight: 0.25 },
  encouraging: { mouthSmileLeft: 0.35, mouthSmileRight: 0.35, browInnerUp: 0.25, browOuterUpLeft: 0.2, browOuterUpRight: 0.2 },
  focused: { browDownLeft: 0.25, browDownRight: 0.25, eyeSquintLeft: 0.2, eyeSquintRight: 0.2 },
};

// Ordered Oculus visemes → morph name candidates.
const OCULUS_VISEMES = [
  "viseme_sil", "viseme_PP", "viseme_FF", "viseme_TH", "viseme_DD",
  "viseme_kk", "viseme_CH", "viseme_SS", "viseme_nn", "viseme_RR",
  "viseme_aa", "viseme_E", "viseme_I", "viseme_O", "viseme_U",
];

function pickClip(names: string[], state: RasheedStateName): string | null {
  const aliases = CLIP_ALIASES[state];
  const lower = names.map((n) => n.toLowerCase());
  for (const alias of aliases) {
    const idx = lower.findIndex((n) => n.includes(alias));
    if (idx !== -1) return names[idx];
  }
  return null;
}

interface MorphTarget {
  mesh: THREE.Mesh;
  dict: Record<string, number>;
  influences: number[];
}

function collectMorphMeshes(root: THREE.Object3D): MorphTarget[] {
  const out: MorphTarget[] = [];
  root.traverse((obj) => {
    const mesh = obj as THREE.Mesh;
    if (mesh.isMesh && mesh.morphTargetDictionary && mesh.morphTargetInfluences) {
      out.push({
        mesh,
        dict: mesh.morphTargetDictionary as Record<string, number>,
        influences: mesh.morphTargetInfluences as number[],
      });
    }
  });
  return out;
}

/** Thrown when a GLB loads but does not satisfy the Rasheed contract. */
export class RasheedGlbInvalidError extends Error {
  constructor(msg: string) {
    super(msg);
    this.name = "RasheedGlbInvalidError";
  }
}

function RasheedModel() {
  const rasheed = useRasheed();
  const gltf = useGLTF(RASHEED_GLB_URL) as unknown as GLTF;
  const { scene, animations } = gltf;
  const groupRef = useRef<THREE.Group>(null);

  // Validate the asset against the integration contract ONCE. A GLB that loads
  // but is missing rig/morphs/clips is NOT acceptable — throw so the parent
  // reverts to the vector fallback instead of showing a broken character.
  useMemo(() => {
    const report = validateRasheedGlb(gltf);
    // Surface the full report in the console for asset producers.
    // eslint-disable-next-line no-console
    console[report.pass ? "info" : "warn"](formatReport(report));
    if (!report.pass) {
      throw new RasheedGlbInvalidError(
        "rasheed.glb failed validation — see console for the PASS/FAIL report. " +
          "Fallback vector character will be used.",
      );
    }
  }, [gltf]);

  // Clone so the same cache entry can be mounted more than once safely.
  const model = useMemo(() => {
    const cloned = SkeletonUtilsClone(scene);
    cloned.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) {
        m.castShadow = true;
        m.frustumCulled = false;
      }
    });
    return cloned;
  }, [scene]);

  const { actions, names } = useAnimations(animations, model);

  const morphMeshes = useMemo(() => collectMorphMeshes(model), [model]);
  const headBone = useMemo(() => {
    let bone: THREE.Object3D | null = null;
    model.traverse((o) => {
      if (!bone && /head/i.test(o.name) && !/headtop|headend/i.test(o.name)) bone = o;
    });
    return bone;
  }, [model]);
  const headRest = useRef<THREE.Euler | null>(null);
  useEffect(() => {
    if (headBone) headRest.current = (headBone as THREE.Object3D).rotation.clone();
  }, [headBone]);

  // ── Drive animation clip from semantic state ──────────────────────────────
  const activeRef = useRef<string | null>(null);
  useEffect(() => {
    if (!names.length) return;
    const clip = pickClip(names, rasheed.state) ?? pickClip(names, "idle") ?? names[0];
    if (!clip || clip === activeRef.current) return;
    const next = actions[clip];
    const prev = activeRef.current ? actions[activeRef.current] : null;
    if (next) {
      next.reset().fadeIn(0.35).play();
      if (prev && prev !== next) prev.fadeOut(0.35);
      activeRef.current = clip;
    }
    // Re-run when a one-shot re-triggers (epoch) so reactions replay.
  }, [rasheed.state, rasheed.epoch, actions, names]);

  // ── Per-frame: expression morphs, gaze, visemes, subtle blink ─────────────
  const blink = useRef(0);
  const nextBlink = useRef(1.5 + Math.random() * 4);
  const clock = useRef(0);

  useFrame((_, delta) => {
    clock.current += delta;

    // Blink scheduling.
    nextBlink.current -= delta;
    if (nextBlink.current <= 0) {
      blink.current = 1;
      nextBlink.current = 2.5 + Math.random() * 4;
    }
    blink.current = Math.max(0, blink.current - delta * 8);

    const targetExpr = EXPRESSION_MORPHS[rasheed.expression] ?? EXPRESSION_MORPHS.neutral;
    const speaking = rasheed.state === "talking";
    const visemes = rasheed.visemes;

    for (const { dict, influences } of morphMeshes) {
      // Expression (lerp toward target; unlisted morphs relax to 0).
      for (const key in dict) {
        const idx = dict[key];
        let target = targetExpr[key] ?? 0;

        // Blink overrides eye-close morphs.
        if (key === "eyeBlinkLeft" || key === "eyeBlinkRight") target = Math.max(target, blink.current);

        // Gaze via eyeLook* morphs.
        if (key === "eyeLookOutLeft" || key === "eyeLookInRight") target = Math.max(target, Math.max(0, rasheed.gaze.x));
        if (key === "eyeLookInLeft" || key === "eyeLookOutRight") target = Math.max(target, Math.max(0, -rasheed.gaze.x));
        if (key === "eyeLookUpLeft" || key === "eyeLookUpRight") target = Math.max(target, Math.max(0, rasheed.gaze.y));
        if (key === "eyeLookDownLeft" || key === "eyeLookDownRight") target = Math.max(target, Math.max(0, -rasheed.gaze.y));

        influences[idx] = THREE.MathUtils.lerp(influences[idx], target, 0.25);
      }

      // Visemes (lip-sync). Explicit weights win; else a soft talking flap.
      if (visemes) {
        for (let v = 0; v < OCULUS_VISEMES.length; v++) {
          const idx = dict[OCULUS_VISEMES[v]];
          if (idx !== undefined) influences[idx] = THREE.MathUtils.lerp(influences[idx], visemes[v] ?? 0, 0.5);
        }
      } else if (speaking) {
        const jaw = dict["jawOpen"];
        if (jaw !== undefined) {
          const flap = (Math.sin(clock.current * 11) * 0.5 + 0.5) * 0.35;
          influences[jaw] = THREE.MathUtils.lerp(influences[jaw], flap, 0.4);
        }
      }
    }

    // Head follows gaze (subtle).
    if (headBone && headRest.current) {
      const hb = headBone as THREE.Object3D;
      const rest = headRest.current;
      hb.rotation.y = THREE.MathUtils.lerp(hb.rotation.y, rest.y + rasheed.gaze.x * 0.25, 0.1);
      hb.rotation.x = THREE.MathUtils.lerp(hb.rotation.x, rest.x - rasheed.gaze.y * 0.18, 0.1);
    }

    // Gentle breathing bob on the whole group when idle-ish.
    if (groupRef.current) {
      groupRef.current.position.y = Math.sin(clock.current * 1.2) * 0.006;
    }
  });

  return (
    <group ref={groupRef} dispose={null}>
      <primitive object={model} />
    </group>
  );
}

/**
 * Minimal SkeletonUtils.clone (deep clone preserving skinned-mesh bone bindings)
 * inlined to avoid an extra import path that differs across three versions.
 */
function SkeletonUtilsClone(source: THREE.Object3D): THREE.Group {
  const sourceLookup = new Map<THREE.Object3D, THREE.Object3D>();
  const cloneLookup = new Map<THREE.Object3D, THREE.Object3D>();
  const clone = source.clone() as unknown as THREE.Group;

  parallelTraverse(source, clone, (a, b) => {
    sourceLookup.set(b, a);
    cloneLookup.set(a, b);
  });

  clone.traverse((node) => {
    const mesh = node as THREE.SkinnedMesh;
    if (!(mesh as THREE.SkinnedMesh).isSkinnedMesh) return;
    const srcMesh = sourceLookup.get(mesh) as THREE.SkinnedMesh;
    const srcBones = srcMesh.skeleton.bones;
    mesh.skeleton = srcMesh.skeleton.clone();
    mesh.bind(
      mesh.skeleton,
      srcMesh.bindMatrix,
    );
    mesh.skeleton.bones = srcBones.map((b) => cloneLookup.get(b) as THREE.Bone);
  });

  return clone;
}

function parallelTraverse(
  a: THREE.Object3D,
  b: THREE.Object3D,
  cb: (a: THREE.Object3D, b: THREE.Object3D) => void,
) {
  cb(a, b);
  for (let i = 0; i < a.children.length; i++) parallelTraverse(a.children[i], b.children[i], cb);
}

/** Points gaze toward the pointer over the canvas. */
function PointerGaze() {
  const rasheed = useRasheed();
  const { gl } = useThree();
  useEffect(() => {
    const el = gl.domElement;
    const onMove = (e: PointerEvent) => {
      const r = el.getBoundingClientRect();
      const x = ((e.clientX - r.left) / r.width) * 2 - 1;
      const y = -(((e.clientY - r.top) / r.height) * 2 - 1);
      rasheed.setGaze({ x: THREE.MathUtils.clamp(x, -1, 1), y: THREE.MathUtils.clamp(y, -1, 1) });
    };
    const onLeave = () => rasheed.setGaze({ x: 0, y: 0 });
    el.addEventListener("pointermove", onMove);
    el.addEventListener("pointerleave", onLeave);
    return () => {
      el.removeEventListener("pointermove", onMove);
      el.removeEventListener("pointerleave", onLeave);
    };
  }, [gl, rasheed]);
  return null;
}

interface RasheedAvatar3DProps {
  className?: string;
  /** camera framing: 'bust' (default) or 'full' */
  frame?: "bust" | "full";
}

export function RasheedAvatar3D({ className = "", frame = "bust" }: RasheedAvatar3DProps) {
  const camPos: [number, number, number] = frame === "full" ? [0, 0.9, 3.2] : [0, 1.5, 1.9];
  const target: [number, number, number] = frame === "full" ? [0, 0.9, 0] : [0, 1.45, 0];

  return (
    <div className={`relative h-full w-full ${className}`} aria-label="Rasheed 3D career coach">
      <Canvas
        shadows
        dpr={[1, 1.8]}
        camera={{ position: camPos, fov: 32, near: 0.1, far: 50 }}
        gl={{ antialias: true, preserveDrawingBuffer: false, powerPreference: "high-performance" }}
        onCreated={({ camera }) => camera.lookAt(...target)}
      >
        <ambientLight intensity={0.6} />
        <directionalLight position={[3, 5, 4]} intensity={1.4} castShadow shadow-mapSize={[1024, 1024]} />
        <directionalLight position={[-4, 2, -2]} intensity={0.4} color="#2A8F88" />
        <Suspense fallback={null}>
          <RasheedModel />
          <Environment preset="city" />
        </Suspense>
        <ContactShadows position={[0, 0, 0]} opacity={0.35} scale={6} blur={2.4} far={4} />
        <PointerGaze />
      </Canvas>
    </div>
  );
}

// Preload only when the asset is known to exist (guarded by the parent probe).
export function preloadRasheedGLB() {
  useGLTF.preload(RASHEED_GLB_URL);
}

export default RasheedAvatar3D;
