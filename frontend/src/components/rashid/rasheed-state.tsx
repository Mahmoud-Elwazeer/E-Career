import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

/**
 * rasheed-state — the SEMANTIC state layer for the Rasheed character system.
 *
 * The application drives Rasheed by SEMANTIC INTENT (idle, talking, thinking,
 * celebrating, …) — NOT by animation-timeline names. The 3D renderer
 * (RasheedAvatar3D) and the vector fallback (RasheedScene) both consume this
 * same state and translate it into their own animation representation.
 *
 * This decoupling is deliberate: swapping the underlying asset (vector → GLB →
 * a future MetaHuman) never touches the app code that dispatches state. It also
 * makes Rasheed drivable from ANY page (hero, companion, chat, onboarding) via
 * a single shared store, and is future-ready for TTS/viseme lip-sync and
 * AI-driven behavior (feed `visemes` + `state` from a backend agent).
 */

// ── Semantic states (the vocabulary the app speaks) ────────────────────────
export type RasheedStateName =
  | "idle"
  | "greeting"
  | "talking"
  | "listening"
  | "thinking"
  | "pointing"
  | "holdingScreen"
  | "reacting"
  | "celebrating";

export type RasheedExpressionName =
  | "neutral"
  | "happy"
  | "encouraging"
  | "focused";

/** One-shot states auto-return to `idle` after they play. */
export const ONE_SHOT_STATES: ReadonlySet<RasheedStateName> = new Set([
  "greeting",
  "reacting",
  "celebrating",
  "pointing",
]);

export interface RasheedGaze {
  /** -1 (left) .. 1 (right) */
  x: number;
  /** -1 (down) .. 1 (up) */
  y: number;
}

export interface RasheedSnapshot {
  state: RasheedStateName;
  expression: RasheedExpressionName;
  /** Head/eye look target, normalized -1..1. */
  gaze: RasheedGaze;
  /** Optional speech-bubble / caption text. */
  message: string | null;
  /**
   * Optional 15 Oculus-viseme weights (0..1) for lip-sync. Null when not
   * speaking. Future TTS pipelines write here each audio frame.
   */
  visemes: Float32Array | null;
  /** Monotonic tick bumped on every one-shot trigger so renderers can replay. */
  epoch: number;
}

export interface RasheedController extends RasheedSnapshot {
  /** Set the persistent semantic state (idle/talking/listening/…). */
  setState: (state: RasheedStateName) => void;
  /** Set facial expression independent of body state. */
  setExpression: (expression: RasheedExpressionName) => void;
  /** Point the head/eyes toward a normalized target. */
  setGaze: (gaze: RasheedGaze | null) => void;
  /** Convenience: enter talking + show a message (+ expression). */
  say: (message: string, expression?: RasheedExpressionName) => void;
  /** Stop talking / clear message → back to idle. */
  hush: () => void;
  /** Fire a one-shot reaction that auto-returns to idle. */
  react: (kind?: "reacting" | "celebrating" | "greeting" | "pointing") => void;
  /** Push viseme weights for the current audio frame (future TTS lip-sync). */
  setVisemes: (weights: Float32Array | null) => void;
}

const DEFAULT_SNAPSHOT: RasheedSnapshot = {
  state: "idle",
  expression: "neutral",
  gaze: { x: 0, y: 0 },
  message: null,
  visemes: null,
  epoch: 0,
};

const RasheedContext = createContext<RasheedController | null>(null);

/** How long one-shot states play before auto-returning to idle (ms). */
const ONE_SHOT_MS = 2400;

export function RasheedProvider({ children }: { children: ReactNode }) {
  const [snap, setSnap] = useState<RasheedSnapshot>(DEFAULT_SNAPSHOT);
  const returnTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearReturn = useCallback(() => {
    if (returnTimer.current) {
      clearTimeout(returnTimer.current);
      returnTimer.current = null;
    }
  }, []);

  const setState = useCallback(
    (state: RasheedStateName) => {
      clearReturn();
      setSnap((s) => {
        const next: RasheedSnapshot = {
          ...s,
          state,
          epoch: s.epoch + 1,
        };
        return next;
      });
      if (ONE_SHOT_STATES.has(state)) {
        returnTimer.current = setTimeout(() => {
          setSnap((s) => (ONE_SHOT_STATES.has(s.state) ? { ...s, state: "idle" } : s));
        }, ONE_SHOT_MS);
      }
    },
    [clearReturn],
  );

  const setExpression = useCallback((expression: RasheedExpressionName) => {
    setSnap((s) => ({ ...s, expression }));
  }, []);

  const setGaze = useCallback((gaze: RasheedGaze | null) => {
    setSnap((s) => ({ ...s, gaze: gaze ?? { x: 0, y: 0 } }));
  }, []);

  const setVisemes = useCallback((weights: Float32Array | null) => {
    setSnap((s) => ({ ...s, visemes: weights }));
  }, []);

  const say = useCallback(
    (message: string, expression: RasheedExpressionName = "encouraging") => {
      clearReturn();
      setSnap((s) => ({ ...s, state: "talking", message, expression, epoch: s.epoch + 1 }));
    },
    [clearReturn],
  );

  const hush = useCallback(() => {
    clearReturn();
    setSnap((s) => ({ ...s, state: "idle", message: null, visemes: null }));
  }, [clearReturn]);

  const react = useCallback(
    (kind: "reacting" | "celebrating" | "greeting" | "pointing" = "reacting") => {
      setState(kind);
    },
    [setState],
  );

  useEffect(() => () => clearReturn(), [clearReturn]);

  const value = useMemo<RasheedController>(
    () => ({
      ...snap,
      setState,
      setExpression,
      setGaze,
      say,
      hush,
      react,
      setVisemes,
    }),
    [snap, setState, setExpression, setGaze, say, hush, react, setVisemes],
  );

  return <RasheedContext.Provider value={value}>{children}</RasheedContext.Provider>;
}

/**
 * useRasheed — read + drive the shared Rasheed state from any component.
 *
 * Safe outside a provider: returns a no-op controller so components that
 * optionally drive Rasheed don't crash when the provider isn't mounted.
 */
export function useRasheed(): RasheedController {
  const ctx = useContext(RasheedContext);
  if (ctx) return ctx;
  return NOOP_CONTROLLER;
}

const NOOP_CONTROLLER: RasheedController = {
  ...DEFAULT_SNAPSHOT,
  setState: () => {},
  setExpression: () => {},
  setGaze: () => {},
  say: () => {},
  hush: () => {},
  react: () => {},
  setVisemes: () => {},
};
