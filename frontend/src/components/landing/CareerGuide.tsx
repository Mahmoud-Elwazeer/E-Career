import { useEffect, useState, useRef, useCallback } from "react";
import { motion, useReducedMotion, AnimatePresence } from "framer-motion";
import { useTheme } from "@/hooks/use-theme";
import { X } from "lucide-react";

/* ═══════════════════════════════════════════════════════════════
   CAREER GUIDE v5 — Product Concierge
   ─────────────────────────────────────
   16s cinematic idle loop · breathing · blink · eye gaze ·
   wave · thinking · glasses adjust · chip review · progress pulse
   Speech bubbles with contextual microcopy guidance
   Interactive: focus/type/hover/click/locked/noResults reactions
   First-visit greeting · tab visibility & scroll-pause aware
   ═══════════════════════════════════════════════════════════════ */

interface CareerGuideProps {
  isSearchFocused?: boolean;
  isTyping?: boolean;
  isHoverSearch?: boolean;
  isClickSearch?: boolean;
  /** 0 = idle, 1 = results loaded, 2 = no results */
  resultsState?: number;
  /** true when user encounters locked/gated content */
  isLocked?: boolean;
  className?: string;
}

/* ── Brand palette ── */
const P = {
  primary: "#0A3836",
  primaryLight: "#134E4A",
  primaryMid: "#1A5C58",
  primaryGlow: "#1D6B66",
  skin: "#D4C4B0",
  skinShadow: "#C4B09A",
  skinHighlight: "#E0D5C8",
  skinDeep: "#B8A48E",
  neutral1: "#ECECEC",
  neutral2: "#C6C6C5",
  neutral3: "#BECFCF",
  dark: "#1A1A1A",
  darkSoft: "#2A2A2A",
  white: "#FFFFFF",
  whiteAlpha: "rgba(255,255,255,0.08)",
} as const;

/* ── Idle phase machine (≈16s total loop) ── */
type IdlePhase =
  | "rest" | "blink1" | "wave" | "glanceChip" | "thinking" | "rest2"
  | "adjustGlasses" | "blink2" | "reviewChip" | "confidentNod"
  | "rest3" | "progressPulse";

const PHASE_DURATIONS: Record<IdlePhase, number> = {
  rest: 1600,
  blink1: 320,
  wave: 1800,
  glanceChip: 1400,
  thinking: 2400,
  rest2: 1000,
  adjustGlasses: 2000,
  blink2: 320,
  reviewChip: 1500,
  confidentNod: 900,
  rest3: 1200,
  progressPulse: 1100,
};

const PHASE_ORDER: IdlePhase[] = [
  "rest", "blink1", "wave", "glanceChip", "thinking", "rest2",
  "adjustGlasses", "blink2", "reviewChip", "confidentNod",
  "rest3", "progressPulse",
];

/* ── Floating chip data ── */
const CHIPS = [
  { label: "Remote",    x: -115, y: -85,  ampX: 3,  ampY: 5,  speed: 5.5, delay: 0,    dotColor: "#4ADE80" },
  { label: "Junior",    x: 115,  y: -40,  ampX: 4,  ampY: 3,  speed: 6.5, delay: 0.6,  dotColor: "#60A5FA" },
  { label: "Full-time", x: -100, y: 50,   ampX: 2,  ampY: 4,  speed: 7.0, delay: 1.2,  dotColor: "#FBBF24" },
  { label: "MENA",      x: 110,  y: 90,   ampX: 5,  ampY: 3,  speed: 5.8, delay: 0.9,  dotColor: "#F87171" },
];

const ALIGNED_OFFSETS = [
  { x: -30, y: -56 },
  { x: -30, y: -36 },
  { x: -30, y: -16 },
  { x: -30, y: 4 },
];

/* ── Spring presets ── */
const SPRING = { type: "spring" as const, stiffness: 120, damping: 18, mass: 1 };
const GENTLE = { type: "spring" as const, stiffness: 70, damping: 22, mass: 1.3 };
const SNAPPY = { type: "spring" as const, stiffness: 200, damping: 20 };

/* ── Tab visibility hook ── */
function useTabVisible() {
  const [visible, setVisible] = useState(true);
  useEffect(() => {
    const handler = () => setVisible(document.visibilityState === "visible");
    document.addEventListener("visibilitychange", handler);
    return () => document.removeEventListener("visibilitychange", handler);
  }, []);
  return visible;
}

/* ── First visit detection ── */
function useFirstVisit() {
  const [isFirst, setIsFirst] = useState(false);
  useEffect(() => {
    const key = "usam-guide-seen";
    if (!localStorage.getItem(key)) {
      setIsFirst(true);
      localStorage.setItem(key, "1");
    }
  }, []);
  return isFirst;
}

/* ════════════════════════════════════════════════
   SPEECH BUBBLE COMPONENT
   ════════════════════════════════════════════════ */
interface SpeechBubbleProps {
  message: string;
  messageAr?: string;
  isAr: boolean;
  isRTL: boolean;
  onDismiss: () => void;
  autoDismissMs?: number;
}

function SpeechBubble({ message, messageAr, isAr, isRTL, onDismiss, autoDismissMs = 5000 }: SpeechBubbleProps) {
  useEffect(() => {
    const t = setTimeout(onDismiss, autoDismissMs);
    return () => clearTimeout(t);
  }, [onDismiss, autoDismissMs]);

  return (
    <motion.div
      className="absolute pointer-events-auto z-30"
      style={{
        bottom: "calc(50% + 60px)",
        [isRTL ? "right" : "left"]: "calc(50% - 80px)",
        maxWidth: 240,
      }}
      initial={{ opacity: 0, y: 8, scale: 0.92 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -6, scale: 0.95 }}
      transition={{ duration: 0.35, ease: [0, 0, 0.2, 1] }}
    >
      <div
        className="relative px-4 py-3 rounded-xl text-[12px] leading-[1.5] font-medium tracking-wide"
        style={{
          background: "rgba(255,255,255,0.14)",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
          border: "1px solid rgba(255,255,255,0.2)",
          color: "rgba(255,255,255,0.9)",
          boxShadow: "0 4px 24px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.1)",
        }}
      >
        <span>{isAr && messageAr ? messageAr : message}</span>
        <button
          onClick={onDismiss}
          className="absolute top-1.5 end-1.5 p-0.5 rounded-full hover:bg-white/10 transition-colors"
          aria-label="Dismiss"
        >
          <X className="w-3 h-3" style={{ color: "rgba(255,255,255,0.5)" }} />
        </button>
        {/* Tail */}
        <div
          className="absolute -bottom-1.5 start-8"
          style={{
            width: 12,
            height: 6,
            background: "rgba(255,255,255,0.14)",
            clipPath: "polygon(0 0, 100% 0, 50% 100%)",
            border: "none",
          }}
        />
      </div>
    </motion.div>
  );
}

/* ════════════════════════════════════════════════
   MAIN COMPONENT
   ════════════════════════════════════════════════ */

export function CareerGuide({
  isSearchFocused = false,
  isTyping = false,
  isHoverSearch = false,
  isClickSearch = false,
  resultsState = 0,
  isLocked = false,
  className = "",
}: CareerGuideProps) {
  const reduced = useReducedMotion();
  const { dir, lang } = useTheme();
  const isRTL = dir === "rtl";
  const isAr = lang === "ar";
  const tabVisible = useTabVisible();
  const isFirstVisit = useFirstVisit();
  const [phase, setPhase] = useState<IdlePhase>("rest");
  const [shimmerChip, setShimmerChip] = useState(-1);
  const [nodding, setNodding] = useState(false);
  const [chipsAligned, setChipsAligned] = useState(false);
  const [resultFlash, setResultFlash] = useState(0);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  /* ── Speech bubble state ── */
  const [bubble, setBubble] = useState<{ id: string; msg: string; msgAr?: string } | null>(null);
  const bubbleShownRef = useRef<Set<string>>(new Set());

  const showBubble = useCallback((id: string, msg: string, msgAr?: string) => {
    if (bubbleShownRef.current.has(id)) return;
    bubbleShownRef.current.add(id);
    setBubble({ id, msg, msgAr });
  }, []);

  const dismissBubble = useCallback(() => setBubble(null), []);

  const isBlinking = phase === "blink1" || phase === "blink2";
  const isWaving = phase === "wave";
  const isInteracting = isSearchFocused || isTyping || isHoverSearch;
  const shouldAnimate = tabVisible && !reduced;

  /* ── Phase cycling ── */
  const advancePhase = useCallback(() => {
    if (isInteracting || !tabVisible) return;
    setPhase((prev) => {
      const idx = PHASE_ORDER.indexOf(prev);
      const next = PHASE_ORDER[(idx + 1) % PHASE_ORDER.length];
      if (next === "reviewChip") setShimmerChip(Math.floor(Math.random() * CHIPS.length));
      return next;
    });
  }, [isInteracting, tabVisible]);

  useEffect(() => {
    if (!shouldAnimate) return;
    if (isInteracting) { setPhase("rest"); return; }
    timerRef.current = setTimeout(advancePhase, PHASE_DURATIONS[phase]);
    return () => clearTimeout(timerRef.current);
  }, [phase, isInteracting, shouldAnimate, advancePhase]);

  /* ── Click search → nod + align chips ── */
  useEffect(() => {
    if (isClickSearch && !reduced) {
      setNodding(true);
      setChipsAligned(true);
      const t1 = setTimeout(() => setNodding(false), 600);
      const t2 = setTimeout(() => setChipsAligned(false), 900);
      return () => { clearTimeout(t1); clearTimeout(t2); };
    }
  }, [isClickSearch, reduced]);

  /* ── Results state reactions ── */
  useEffect(() => {
    if (resultsState === 1) {
      setResultFlash(1);
      const t = setTimeout(() => setResultFlash(0), 1200);
      return () => clearTimeout(t);
    }
    if (resultsState === 2) {
      setResultFlash(2);
      showBubble(
        "no-results",
        "Try removing a filter or searching a broader title.",
        "جرب إزالة فلتر أو البحث بعنوان أوسع."
      );
      const t = setTimeout(() => setResultFlash(0), 2000);
      return () => clearTimeout(t);
    }
  }, [resultsState, showBubble]);

  /* ── Speech bubble triggers ── */

  // First visit greeting (after 1.5s)
  useEffect(() => {
    if (!isFirstVisit || reduced) return;
    const t = setTimeout(() => {
      showBubble(
        "welcome",
        "Try searching 'Remote UI/UX' — I'll help you filter fast.",
        "جرّب البحث عن 'Remote UI/UX' — سأساعدك في التصفية بسرعة."
      );
    }, 1500);
    return () => clearTimeout(t);
  }, [isFirstVisit, reduced, showBubble]);

  // On search focus
  useEffect(() => {
    if (isSearchFocused && !isTyping) {
      showBubble(
        "focus",
        "Start with a job title + location.",
        "ابدأ بالمسمى الوظيفي + الموقع."
      );
    }
  }, [isSearchFocused, isTyping, showBubble]);

  // Dismiss bubble while typing
  useEffect(() => {
    if (isTyping) dismissBubble();
  }, [isTyping, dismissBubble]);

  // Locked content
  useEffect(() => {
    if (isLocked) {
      showBubble(
        "locked",
        "Sign in to unlock full details & save jobs.",
        "سجّل الدخول لعرض التفاصيل الكاملة وحفظ الوظائف."
      );
    }
  }, [isLocked, showBubble]);

  /* ── Derived poses ── */
  const leanDir = isRTL ? 1 : -1;

  const headTilt = nodding ? 6
    : resultFlash === 2 ? leanDir * -3
    : isSearchFocused ? leanDir * 5
    : isHoverSearch ? leanDir * 2
    : phase === "thinking" ? 3.5
    : phase === "confidentNod" ? 2
    : isWaving ? 2
    : 0;

  const bodyLean = isSearchFocused ? leanDir * 3 : 0;
  const glassesNudge = phase === "adjustGlasses" ? -2.5 : 0;
  const isSmiling = isHoverSearch || isSearchFocused || nodding || resultFlash === 1 || isWaving;
  const isHmm = resultFlash === 2;

  /* Right arm pose */
  const rArmRotate =
    phase === "thinking" ? -18 :
    phase === "adjustGlasses" ? -28 : 0;
  const rArmY =
    phase === "thinking" ? -14 :
    phase === "adjustGlasses" ? -20 : 0;

  /* Left arm — wave */
  const lArmRotate = isWaving ? -25 : isSearchFocused ? 3 : 0;
  const lArmY = isWaving ? -18 : 0;

  /* Eyebrow pose */
  const eyebrowY =
    phase === "thinking" ? -3.5
    : isHoverSearch ? -1.5
    : nodding ? -2
    : resultFlash === 2 ? -4
    : resultFlash === 1 ? -1
    : isWaving ? -2
    : 0;

  const showProgress = (phase === "progressPulse" || isHoverSearch) && !isTyping;

  const chipGlanceX = phase === "glanceChip" ? leanDir * 2.5 : 0;
  const chipGlanceY = phase === "glanceChip" ? -1.5 : 0;

  const eyeOffsetX =
    isSearchFocused ? leanDir * 1.5
    : isHoverSearch ? leanDir * 0.8
    : chipGlanceX;
  const eyeOffsetY =
    nodding ? 1.2
    : phase === "thinking" ? -0.5
    : chipGlanceY;

  if (reduced) {
    return (
      <div className={`relative select-none w-full h-full ${className}`} style={{ minHeight: 380 }}>
        {CHIPS.map((chip) => (
          <div
            key={chip.label}
            className="absolute flex items-center gap-1.5 pointer-events-none whitespace-nowrap"
            style={{
              top: `calc(50% + ${chip.y}px)`,
              [isRTL ? "right" : "left"]: `calc(50% + ${chip.x}px)`,
              opacity: 0.4,
            }}
          >
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] font-medium tracking-wide border border-white/15 bg-white/8" style={{ color: "rgba(255,255,255,0.65)" }}>
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: chip.dotColor, opacity: 0.6 }} />
              {chip.label}
            </div>
          </div>
        ))}
        <svg viewBox="0 0 320 440" fill="none" className="w-full h-full" style={{ maxHeight: 440 }} role="img" aria-label="Career Guide character">
          {staticDefs}
          {renderCharacterStatic()}
        </svg>
      </div>
    );
  }

  return (
    <div className={`relative select-none w-full h-full ${className}`} style={{ minHeight: 380 }}>

      {/* ════ SPEECH BUBBLE ════ */}
      <AnimatePresence>
        {bubble && (
          <SpeechBubble
            key={bubble.id}
            message={bubble.msg}
            messageAr={bubble.msgAr}
            isAr={isAr}
            isRTL={isRTL}
            onDismiss={dismissBubble}
          />
        )}
      </AnimatePresence>

      {/* ════ FLOATING CHIPS ════ */}
      {CHIPS.map((chip, i) => {
        const isReviewed = phase === "reviewChip" && shimmerChip === i;
        const isFocusHighlight = isSearchFocused && i === 0;
        const isSuccessFlash = resultFlash === 1 && i === 0;
        const isNoResultWiggle = resultFlash === 2 && i === 2;
        const driftPaused = isSearchFocused || isTyping || chipsAligned;
        const alignedPos = ALIGNED_OFFSETS[i];

        return (
          <motion.div
            key={chip.label}
            className="absolute flex items-center gap-1.5 pointer-events-none whitespace-nowrap"
            style={{
              top: `calc(50% + ${chip.y}px)`,
              [isRTL ? "right" : "left"]: `calc(50% + ${chip.x}px)`,
              zIndex: i % 2 === 0 ? 5 : 15,
            }}
            initial={{ opacity: 0, scale: 0.85, y: 16 }}
            animate={{
              opacity: isTyping ? 0.12
                : isFocusHighlight ? 1
                : isReviewed ? 0.85
                : chipsAligned ? 0.9
                : 0.45,
              scale: isFocusHighlight ? 1.08
                : isReviewed ? 1.04
                : chipsAligned ? 1.02
                : 1,
              y: chipsAligned
                ? alignedPos.y
                : driftPaused
                ? 0
                : [0, -chip.ampY, 0],
              x: chipsAligned
                ? alignedPos.x - chip.x
                : isNoResultWiggle
                ? [0, -4, 4, -2, 0]
                : driftPaused
                ? 0
                : [0, chip.ampX * (i % 2 === 0 ? 1 : -1), 0],
              rotate: isNoResultWiggle ? [0, -3, 3, -1, 0] : 0,
            }}
            transition={{
              opacity: { duration: 0.5 },
              scale: { duration: 0.4, ease: "easeOut" },
              y: chipsAligned
                ? { type: "spring", stiffness: 150, damping: 16 }
                : driftPaused
                ? { duration: 0.6, ease: "easeOut" }
                : { duration: chip.speed, repeat: Infinity, delay: chip.delay, ease: "easeInOut" },
              x: chipsAligned
                ? { type: "spring", stiffness: 150, damping: 16 }
                : isNoResultWiggle
                ? { duration: 0.5, ease: "easeOut" }
                : driftPaused
                ? { duration: 0.6, ease: "easeOut" }
                : { duration: chip.speed * 1.3, repeat: Infinity, delay: chip.delay + 0.5, ease: "easeInOut" },
              rotate: isNoResultWiggle ? { duration: 0.5 } : { duration: 0.3 },
            }}
          >
            <div
              className="relative overflow-hidden flex items-center gap-2 px-3.5 py-2 rounded-full text-[11px] font-medium tracking-wide"
              style={{
                background: isFocusHighlight
                  ? "rgba(255,255,255,0.18)"
                  : "rgba(255,255,255,0.07)",
                border: `1px solid rgba(255,255,255,${isFocusHighlight ? 0.4 : isReviewed ? 0.25 : 0.12})`,
                color: isFocusHighlight ? P.white : "rgba(255,255,255,0.65)",
                boxShadow: isFocusHighlight
                  ? `0 0 0 3px rgba(74,222,128,0.15), 0 4px 16px rgba(10,56,54,0.2), inset 0 1px 0 rgba(255,255,255,0.08)`
                  : isSuccessFlash
                  ? `0 0 0 2px rgba(74,222,128,0.3), 0 0 12px rgba(74,222,128,0.15)`
                  : "0 1px 4px rgba(0,0,0,0.04)",
                transition: "border-color 0.4s, box-shadow 0.4s, background 0.4s",
              }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full shrink-0"
                style={{
                  background: chip.dotColor,
                  opacity: isFocusHighlight ? 1 : 0.6,
                  boxShadow: isFocusHighlight ? `0 0 6px ${chip.dotColor}` : "none",
                  transition: "opacity 0.3s, box-shadow 0.3s",
                }}
              />
              <span>{chip.label}</span>
              {(isReviewed || isSuccessFlash) && (
                <motion.div
                  className="absolute inset-0 pointer-events-none"
                  style={{
                    background: isSuccessFlash
                      ? "linear-gradient(90deg, transparent 0%, rgba(74,222,128,0.2) 50%, transparent 100%)"
                      : "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.15) 50%, transparent 100%)",
                  }}
                  initial={{ x: "-100%" }}
                  animate={{ x: "250%" }}
                  transition={{ duration: 1, ease: [0.25, 0.1, 0.25, 1] }}
                />
              )}
            </div>
          </motion.div>
        );
      })}

      {/* ════ SVG CHARACTER ════ */}
      <svg
        viewBox="0 0 320 440"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
        style={{ maxHeight: 440 }}
        role="img"
        aria-label="Career Guide — a professional figure with glasses, graduation cap, and floating filter chips"
      >
        <defs>
          <linearGradient id="cg4-skin" x1="0" y1="0" x2="0.2" y2="1">
            <stop offset="0%" stopColor={P.skinHighlight} />
            <stop offset="70%" stopColor={P.skin} />
            <stop offset="100%" stopColor={P.skinShadow} />
          </linearGradient>
          <linearGradient id="cg4-body" x1="0.3" y1="0" x2="0.7" y2="1">
            <stop offset="0%" stopColor={P.primaryGlow} />
            <stop offset="40%" stopColor={P.primaryMid} />
            <stop offset="100%" stopColor={P.primary} />
          </linearGradient>
          <linearGradient id="cg4-body-side" x1="0" y1="0" x2="1" y2="0.5">
            <stop offset="0%" stopColor={P.primary} />
            <stop offset="100%" stopColor={P.primaryMid} stopOpacity="0.8" />
          </linearGradient>
          <radialGradient id="cg4-shadow" cx="0.5" cy="1" r="0.6">
            <stop offset="0%" stopColor={P.primary} stopOpacity="0.18" />
            <stop offset="100%" stopColor={P.primary} stopOpacity="0" />
          </radialGradient>
          <linearGradient id="cg4-cap" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={P.primaryGlow} />
            <stop offset="100%" stopColor={P.primary} />
          </linearGradient>
          <linearGradient id="cg4-lens" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={P.neutral3} stopOpacity="0.2" />
            <stop offset="100%" stopColor={P.neutral3} stopOpacity="0.04" />
          </linearGradient>
          <linearGradient id="cg4-lens-reflect" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="white" stopOpacity="0.5" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="cg4-hair" x1="0.2" y1="0" x2="0.8" y2="1">
            <stop offset="0%" stopColor={P.primaryMid} />
            <stop offset="100%" stopColor={P.primary} />
          </linearGradient>
        </defs>

        {/* ── Ground shadow ── */}
        <ellipse cx="160" cy="422" rx="58" ry="9" fill="url(#cg4-shadow)" />

        {/* ── Progress arrow (background layer) ── */}
        <AnimatePresence>
          {showProgress && (
            <motion.g
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 1.2, ease: "easeInOut" }}
            >
              <motion.line
                x1="248" y1="345" x2="248" y2="155"
                stroke={P.neutral3}
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeDasharray="4 7"
                animate={{ opacity: [0.06, 0.15, 0.06] }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
              />
              <motion.path
                d="M240 168 L248 150 L256 168"
                stroke={P.neutral3}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
                animate={{ y: [0, -5, 0], opacity: [0.1, 0.25, 0.1] }}
                transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
              />
            </motion.g>
          )}
        </AnimatePresence>

        {/* ══════ BODY GROUP ══════ */}
        <motion.g
          animate={{ rotate: bodyLean, x: bodyLean * 0.6 }}
          transition={GENTLE}
          style={{ originX: "160px", originY: "330px" }}
        >
          {/* ── Torso with breathing ── */}
          <motion.path
            d="M122 244 Q122 226 142 218 L178 218 Q198 226 198 244 L204 358 Q204 370 192 370 L128 370 Q116 370 116 358 Z"
            fill="url(#cg4-body)"
            animate={{
              d: [
                "M122 244 Q122 226 142 218 L178 218 Q198 226 198 244 L204 358 Q204 370 192 370 L128 370 Q116 370 116 358 Z",
                "M121 244 Q121 226 141 217 L179 217 Q199 226 199 244 L205 359 Q205 371 193 371 L127 371 Q115 371 115 359 Z",
                "M122 244 Q122 226 142 218 L178 218 Q198 226 198 244 L204 358 Q204 370 192 370 L128 370 Q116 370 116 358 Z",
              ],
            }}
            transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
          />

          {/* Torso side shading */}
          <path
            d="M122 244 Q122 235 128 232 L128 358 Q116 358 116 348 L122 244 Z"
            fill={P.primary}
            opacity="0.3"
          />

          {/* Collar */}
          <path d="M142 218 L160 236 L178 218" stroke={P.neutral3} strokeWidth="1.6" fill="none" strokeLinecap="round" />
          <path d="M144 220 L160 234 L176 220" stroke={P.neutral3} strokeWidth="0.5" fill="none" strokeLinecap="round" opacity="0.35" />

          {/* ── Shoulders ── */}
          <path d="M122 244 Q96 250 84 278 Q80 288 87 290 Q96 268 122 254" fill="url(#cg4-body)" />
          <path d="M198 244 Q224 250 236 278 Q240 288 233 290 Q224 268 198 254" fill="url(#cg4-body)" />

          {/* ── Left arm (wave arm) ── */}
          <motion.g
            animate={{ rotate: lArmRotate, y: lArmY }}
            transition={SPRING}
            style={{ originX: "87px", originY: "290px" }}
          >
            <path d="M87 290 Q82 314 86 342 Q88 350 94 346" stroke={P.primary} strokeWidth="10" strokeLinecap="round" fill="none" />
            <motion.g
              animate={isWaving ? { rotate: [0, 15, -10, 12, 0] } : { rotate: 0 }}
              transition={isWaving ? { duration: 1.2, ease: "easeInOut" } : { duration: 0.3 }}
              style={{ originX: "90px", originY: "342px" }}
            >
              <ellipse cx="94" cy="346" rx="8" ry="7" fill="url(#cg4-skin)" />
              <ellipse cx="97" cy="343" rx="3" ry="2.5" fill={P.skin} opacity="0.6" />
              {/* Fingers for wave */}
              <AnimatePresence>
                {isWaving && (
                  <motion.g
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <line x1="90" y1="340" x2="86" y2="332" stroke={P.skin} strokeWidth="2.5" strokeLinecap="round" />
                    <line x1="93" y1="339" x2="91" y2="330" stroke={P.skin} strokeWidth="2.5" strokeLinecap="round" />
                    <line x1="96" y1="340" x2="95" y2="331" stroke={P.skin} strokeWidth="2.5" strokeLinecap="round" />
                  </motion.g>
                )}
              </AnimatePresence>
            </motion.g>
          </motion.g>

          {/* ── Right arm (gesture arm) ── */}
          <motion.g
            animate={{ rotate: rArmRotate, y: rArmY }}
            transition={SPRING}
            style={{ originX: "233px", originY: "290px" }}
          >
            <path d="M233 290 Q238 314 230 342 Q226 352 220 348" stroke={P.primary} strokeWidth="10" strokeLinecap="round" fill="none" />
            <ellipse cx="220" cy="348" rx="8" ry="7" fill="url(#cg4-skin)" />
            <ellipse cx="217" cy="345" rx="3" ry="2.5" fill={P.skin} opacity="0.6" />

            {/* Finger for thinking */}
            <AnimatePresence>
              {phase === "thinking" && (
                <motion.g
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.35 }}
                >
                  <line x1="220" y1="340" x2="218" y2="326" stroke={P.skin} strokeWidth="3.5" strokeLinecap="round" />
                  <circle cx="217" cy="324" r="2.5" fill={P.skinHighlight} />
                </motion.g>
              )}
            </AnimatePresence>

            {/* Finger for glasses nudge */}
            <AnimatePresence>
              {phase === "adjustGlasses" && (
                <motion.g
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.25 }}
                >
                  <circle cx="216" cy="330" r="3" fill={P.skin} />
                  <circle cx="215" cy="328" r="1.5" fill={P.skinHighlight} opacity="0.5" />
                </motion.g>
              )}
            </AnimatePresence>
          </motion.g>

          {/* ── Legs ── */}
          <rect x="136" y="370" width="17" height="44" rx="8.5" fill={P.dark} />
          <rect x="167" y="370" width="17" height="44" rx="8.5" fill={P.dark} />
          <line x1="144" y1="372" x2="144" y2="390" stroke={P.darkSoft} strokeWidth="0.6" opacity="0.3" />
          <line x1="176" y1="372" x2="176" y2="390" stroke={P.darkSoft} strokeWidth="0.6" opacity="0.3" />

          {/* ── Shoes ── */}
          <ellipse cx="144" cy="416" rx="14" ry="6" fill={P.primary} />
          <ellipse cx="176" cy="416" rx="14" ry="6" fill={P.primary} />
          <ellipse cx="141" cy="414" rx="5" ry="1.8" fill={P.primaryLight} opacity="0.25" />
          <ellipse cx="173" cy="414" rx="5" ry="1.8" fill={P.primaryLight} opacity="0.25" />
        </motion.g>

        {/* ══════ HEAD GROUP ══════ */}
        <motion.g
          animate={{
            rotate: headTilt,
            y: nodding ? [0, 4, -1, 0]
              : phase === "confidentNod" ? [0, 2.5, -0.5, 0]
              : 0,
          }}
          transition={
            nodding ? { duration: 0.5, ease: "easeOut" }
            : phase === "confidentNod" ? { duration: 0.8, ease: "easeOut" }
            : SPRING
          }
          style={{ originX: "160px", originY: "205px" }}
        >
          {/* ── Neck ── */}
          <rect x="150" y="206" width="20" height="15" rx="6" fill="url(#cg4-skin)" />
          <rect x="150" y="216" width="20" height="5" rx="2.5" fill={P.skinShadow} opacity="0.35" />

          {/* ── Head ── */}
          <ellipse cx="160" cy="170" rx="41" ry="47" fill="url(#cg4-skin)" />
          <ellipse cx="132" cy="185" rx="8" ry="5" fill="#D4A89A" opacity="0.08" />
          <ellipse cx="188" cy="185" rx="8" ry="5" fill="#D4A89A" opacity="0.08" />
          <ellipse cx="160" cy="210" rx="28" ry="5" fill={P.skinShadow} opacity="0.12" />

          {/* ── Ears ── */}
          <ellipse cx="119" cy="172" rx="5.5" ry="8.5" fill={P.skin} />
          <ellipse cx="120" cy="172" rx="3" ry="5.5" fill={P.skinShadow} opacity="0.25" />
          <ellipse cx="201" cy="172" rx="5.5" ry="8.5" fill={P.skin} />
          <ellipse cx="200" cy="172" rx="3" ry="5.5" fill={P.skinShadow} opacity="0.25" />

          {/* ── Hair ── */}
          <path
            d="M119 158 Q119 124 160 117 Q201 124 201 158 L201 146 Q201 127 160 121 Q119 127 119 146 Z"
            fill="url(#cg4-hair)"
          />
          <path d="M126 153 Q128 133 160 127 Q172 130 178 137" stroke={P.primaryGlow} strokeWidth="1.8" fill="none" opacity="0.2" />
          <rect x="119" y="155" width="4" height="12" rx="2" fill={P.primary} opacity="0.4" />
          <rect x="197" y="155" width="4" height="12" rx="2" fill={P.primary} opacity="0.4" />

          {/* ── Graduation cap ── */}
          <motion.g
            animate={{ y: phase === "adjustGlasses" ? -1.5 : nodding ? 1 : phase === "confidentNod" ? 0.5 : 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          >
            <path
              d="M106 137 L214 137 L205 128 Q160 120 115 128 Z"
              fill="url(#cg4-cap)"
              opacity="0.8"
            />
            <line x1="110" y1="137" x2="210" y2="137" stroke={P.primaryGlow} strokeWidth="0.5" opacity="0.3" />
            <rect x="156" y="125" width="8" height="3" rx="1.5" fill={P.primaryLight} opacity="0.5" />

            {/* Cap pin — small progress arrow motif */}
            <path d="M158 131 L160 127 L162 131" stroke={P.neutral3} strokeWidth="0.8" strokeLinecap="round" fill="none" opacity="0.6" />

            {/* Tassel */}
            <motion.path
              d="M205 133 Q216 139 214 158"
              stroke={P.neutral3}
              strokeWidth="1.6"
              strokeLinecap="round"
              fill="none"
              animate={{ d: ["M205 133 Q216 139 214 158", "M205 133 Q219 142 216 158", "M205 133 Q216 139 214 158"] }}
              transition={{ duration: 5.5, repeat: Infinity, ease: "easeInOut" }}
            />
            <motion.circle
              cx="214" cy="159" r="3.2"
              fill={P.neutral3}
              animate={{ cy: [159, 161, 159] }}
              transition={{ duration: 5.5, repeat: Infinity, ease: "easeInOut" }}
            />
          </motion.g>

          {/* ── Glasses ── */}
          <motion.g
            animate={{ y: glassesNudge }}
            transition={SNAPPY}
          >
            <path d="M149 172 Q160 168 171 172" stroke={P.dark} strokeWidth="1" fill="none" />

            <rect x="127" y="164" width="22" height="16" rx="5.5" stroke={P.dark} strokeWidth="1.2" fill="url(#cg4-lens)" />
            <motion.rect
              x="129" y="166" width="6" height="2" rx="1"
              fill="url(#cg4-lens-reflect)"
              animate={
                phase === "adjustGlasses"
                  ? { opacity: [0.3, 0.8, 0.3] }
                  : { opacity: 0.3 }
              }
              transition={{ duration: 0.9 }}
            />

            <rect x="171" y="164" width="22" height="16" rx="5.5" stroke={P.dark} strokeWidth="1.2" fill="url(#cg4-lens)" />
            <rect x="173" y="166" width="5" height="1.5" rx="0.75" fill="white" opacity="0.2" />

            <line x1="127" y1="170" x2="119" y2="168" stroke={P.dark} strokeWidth="1" />
            <line x1="193" y1="170" x2="201" y2="168" stroke={P.dark} strokeWidth="1" />
            <path d="M119 168 Q117 172 118 176" stroke={P.dark} strokeWidth="0.8" fill="none" opacity="0.5" />
            <path d="M201 168 Q203 172 202 176" stroke={P.dark} strokeWidth="0.8" fill="none" opacity="0.5" />
          </motion.g>

          {/* ── Eyes with gaze tracking ── */}
          <motion.g
            animate={{ scaleY: isBlinking ? 0.04 : 1 }}
            transition={{ duration: isBlinking ? 0.1 : 0.18 }}
            style={{ originX: "160px", originY: "174px" }}
          >
            <ellipse cx="138" cy="174" rx="5" ry="4.5" fill="white" opacity="0.9" />
            <motion.ellipse
              cx={138} cy={174} rx="3" ry="3"
              fill={P.dark}
              animate={{ cx: 138 + eyeOffsetX, cy: 174 + eyeOffsetY }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            />
            <motion.circle
              cx={139.5} cy={173} r="1"
              fill="white" opacity="0.85"
              animate={{ cx: 139.5 + eyeOffsetX * 0.5 }}
              transition={{ duration: 0.3 }}
            />

            <ellipse cx="182" cy="174" rx="5" ry="4.5" fill="white" opacity="0.9" />
            <motion.ellipse
              cx={182} cy={174} rx="3" ry="3"
              fill={P.dark}
              animate={{ cx: 182 + eyeOffsetX, cy: 174 + eyeOffsetY }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            />
            <motion.circle
              cx={183.5} cy={173} r="1"
              fill="white" opacity="0.85"
              animate={{ cx: 183.5 + eyeOffsetX * 0.5 }}
              transition={{ duration: 0.3 }}
            />
          </motion.g>

          {/* ── Eyebrows ── */}
          <motion.g
            animate={{ y: eyebrowY }}
            transition={{ duration: 0.3 }}
          >
            <motion.path
              d="M130 159 Q135 155.5 144 158"
              stroke={P.primary} strokeWidth="2" strokeLinecap="round" fill="none"
              animate={{
                d: isHmm ? "M130 157 Q135 153 144 156" : "M130 159 Q135 155.5 144 158",
              }}
              transition={{ duration: 0.35 }}
            />
            <motion.path
              d="M176 158 Q185 155.5 190 159"
              stroke={P.primary} strokeWidth="2" strokeLinecap="round" fill="none"
              animate={{
                d: isHmm ? "M176 159 Q185 157 190 160" : "M176 158 Q185 155.5 190 159",
              }}
              transition={{ duration: 0.35 }}
            />
          </motion.g>

          {/* ── Nose ── */}
          <path d="M157 184 Q160 189 163 184" stroke={P.skinShadow} strokeWidth="1.2" strokeLinecap="round" fill="none" />
          <circle cx="160" cy="186" r="0.8" fill={P.skinDeep} opacity="0.15" />

          {/* ── Mouth ── */}
          <motion.path
            fill="none"
            stroke={P.darkSoft}
            strokeWidth="1.5"
            strokeLinecap="round"
            animate={{
              d: isSmiling
                ? "M147 196 Q160 206 173 196"
                : isHmm
                ? "M150 198 Q155 195 160 197 Q165 199 170 196"
                : "M150 196 Q160 201 170 196",
            }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          />
          <ellipse cx="160" cy="208" rx="12" ry="2.5" fill={P.skinShadow} opacity="0.1" />
        </motion.g>

        {/* ══════ FLOATING MINI JOB CARDS ══════ */}
        <motion.g
          animate={{
            y: isTyping ? 0 : [0, -5, 0],
            rotate: isSearchFocused ? -2 : [0, 1, 0],
            opacity: isTyping ? 0.1 : 0.45,
          }}
          transition={{
            y: { duration: 7, repeat: Infinity, ease: "easeInOut" },
            rotate: { duration: 8, repeat: Infinity, ease: "easeInOut" },
            opacity: { duration: 0.5 },
          }}
        >
          <rect x="25" y="215" width="65" height="45" rx="8" fill="white" fillOpacity="0.08" stroke="white" strokeOpacity="0.12" strokeWidth="0.8" />
          <rect x="33" y="224" width="30" height="3.5" rx="1.75" fill="white" fillOpacity="0.3" />
          <rect x="33" y="231" width="42" height="2.5" rx="1.25" fill="white" fillOpacity="0.18" />
          <rect x="33" y="237" width="24" height="2.5" rx="1.25" fill="white" fillOpacity="0.12" />
          <circle cx="78" cy="250" r="2.5" fill={P.neutral3} fillOpacity="0.35" />
          <path d="M74 226 L78 224 L74 222" stroke="white" strokeWidth="0.8" strokeLinecap="round" fill="none" opacity="0.25" />
        </motion.g>

        <motion.g
          animate={{
            y: isTyping ? 0 : [0, -6, 0],
            opacity: isTyping ? 0.06 : nodding ? [0.4, 0.8, 0.4] : 0.35,
          }}
          transition={{
            y: { duration: 9, repeat: Infinity, ease: "easeInOut", delay: 1.5 },
            opacity: nodding ? { duration: 0.5 } : { duration: 0.3 },
          }}
        >
          <rect x="238" y="292" width="58" height="40" rx="7" fill="white" fillOpacity="0.06" stroke="white" strokeOpacity="0.1" strokeWidth="0.8" />
          <rect x="245" y="300" width="24" height="3" rx="1.5" fill="white" fillOpacity="0.25" />
          <rect x="245" y="307" width="38" height="2.5" rx="1.25" fill="white" fillOpacity="0.15" />
          <rect x="245" y="313" width="20" height="2.5" rx="1.25" fill="white" fillOpacity="0.1" />
          <rect x="273" y="322" width="16" height="5" rx="2.5" fill={P.neutral3} fillOpacity="0.2" />
        </motion.g>

        {/* ── Ambient sparkles on focus ── */}
        <AnimatePresence>
          {isSearchFocused && (
            <motion.g
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.5 }}
            >
              {[
                { cx: 88, cy: 228, r: 1.8, dur: 2.2, del: 0 },
                { cx: 242, cy: 208, r: 1.4, dur: 2.8, del: 0.5 },
                { cx: 112, cy: 305, r: 1.6, dur: 2, del: 0.9 },
              ].map((s, i) => (
                <motion.circle
                  key={i}
                  cx={s.cx} cy={s.cy} r={s.r}
                  fill={P.neutral3}
                  animate={{ opacity: [0, 0.5, 0], scale: [0.4, 1.1, 0.4] }}
                  transition={{ duration: s.dur, repeat: Infinity, delay: s.del }}
                />
              ))}
            </motion.g>
          )}
        </AnimatePresence>
      </svg>
    </div>
  );
}

/* ── Reduced-motion static render helpers ── */
const staticDefs = (
  <defs>
    <linearGradient id="cg4-skin" x1="0" y1="0" x2="0.2" y2="1">
      <stop offset="0%" stopColor={P.skinHighlight} />
      <stop offset="70%" stopColor={P.skin} />
      <stop offset="100%" stopColor={P.skinShadow} />
    </linearGradient>
    <linearGradient id="cg4-body" x1="0.3" y1="0" x2="0.7" y2="1">
      <stop offset="0%" stopColor={P.primaryGlow} />
      <stop offset="40%" stopColor={P.primaryMid} />
      <stop offset="100%" stopColor={P.primary} />
    </linearGradient>
    <linearGradient id="cg4-cap" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stopColor={P.primaryGlow} />
      <stop offset="100%" stopColor={P.primary} />
    </linearGradient>
    <linearGradient id="cg4-lens" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stopColor={P.neutral3} stopOpacity="0.2" />
      <stop offset="100%" stopColor={P.neutral3} stopOpacity="0.04" />
    </linearGradient>
    <radialGradient id="cg4-shadow" cx="0.5" cy="1" r="0.6">
      <stop offset="0%" stopColor={P.primary} stopOpacity="0.18" />
      <stop offset="100%" stopColor={P.primary} stopOpacity="0" />
    </radialGradient>
    <linearGradient id="cg4-hair" x1="0.2" y1="0" x2="0.8" y2="1">
      <stop offset="0%" stopColor={P.primaryMid} />
      <stop offset="100%" stopColor={P.primary} />
    </linearGradient>
  </defs>
);

function renderCharacterStatic() {
  return (
    <g>
      <ellipse cx="160" cy="422" rx="58" ry="9" fill="url(#cg4-shadow)" />
      <path d="M122 244 Q122 226 142 218 L178 218 Q198 226 198 244 L204 358 Q204 370 192 370 L128 370 Q116 370 116 358 Z" fill="url(#cg4-body)" />
      <path d="M142 218 L160 236 L178 218" stroke={P.neutral3} strokeWidth="1.6" fill="none" strokeLinecap="round" />
      <path d="M122 244 Q96 250 84 278 Q80 288 87 290 Q96 268 122 254" fill="url(#cg4-body)" />
      <path d="M198 244 Q224 250 236 278 Q240 288 233 290 Q224 268 198 254" fill="url(#cg4-body)" />
      <path d="M87 290 Q82 314 86 342 Q88 350 94 346" stroke={P.primary} strokeWidth="10" strokeLinecap="round" fill="none" />
      <ellipse cx="94" cy="346" rx="8" ry="7" fill="url(#cg4-skin)" />
      <path d="M233 290 Q238 314 230 342 Q226 352 220 348" stroke={P.primary} strokeWidth="10" strokeLinecap="round" fill="none" />
      <ellipse cx="220" cy="348" rx="8" ry="7" fill="url(#cg4-skin)" />
      <rect x="136" y="370" width="17" height="44" rx="8.5" fill={P.dark} />
      <rect x="167" y="370" width="17" height="44" rx="8.5" fill={P.dark} />
      <ellipse cx="144" cy="416" rx="14" ry="6" fill={P.primary} />
      <ellipse cx="176" cy="416" rx="14" ry="6" fill={P.primary} />
      <rect x="150" y="206" width="20" height="15" rx="6" fill="url(#cg4-skin)" />
      <ellipse cx="160" cy="170" rx="41" ry="47" fill="url(#cg4-skin)" />
      <path d="M119 158 Q119 124 160 117 Q201 124 201 158 L201 146 Q201 127 160 121 Q119 127 119 146 Z" fill="url(#cg4-hair)" />
      <path d="M106 137 L214 137 L205 128 Q160 120 115 128 Z" fill="url(#cg4-cap)" opacity="0.8" />
      <path d="M205 133 Q216 139 214 158" stroke={P.neutral3} strokeWidth="1.6" strokeLinecap="round" fill="none" />
      <circle cx="214" cy="159" r="3.2" fill={P.neutral3} />
      <path d="M149 172 Q160 168 171 172" stroke={P.dark} strokeWidth="1" fill="none" />
      <rect x="127" y="164" width="22" height="16" rx="5.5" stroke={P.dark} strokeWidth="1.2" fill="url(#cg4-lens)" />
      <rect x="171" y="164" width="22" height="16" rx="5.5" stroke={P.dark} strokeWidth="1.2" fill="url(#cg4-lens)" />
      <line x1="127" y1="170" x2="119" y2="168" stroke={P.dark} strokeWidth="1" />
      <line x1="193" y1="170" x2="201" y2="168" stroke={P.dark} strokeWidth="1" />
      <ellipse cx="138" cy="174" rx="3" ry="3" fill={P.dark} />
      <circle cx="139.5" cy="173" r="1" fill="white" opacity="0.85" />
      <ellipse cx="182" cy="174" rx="3" ry="3" fill={P.dark} />
      <circle cx="183.5" cy="173" r="1" fill="white" opacity="0.85" />
      <path d="M130 159 Q135 155.5 144 158" stroke={P.primary} strokeWidth="2" strokeLinecap="round" fill="none" />
      <path d="M176 158 Q185 155.5 190 159" stroke={P.primary} strokeWidth="2" strokeLinecap="round" fill="none" />
      <path d="M157 184 Q160 189 163 184" stroke={P.skinShadow} strokeWidth="1.2" strokeLinecap="round" fill="none" />
      <path fill="none" stroke={P.darkSoft} strokeWidth="1.5" strokeLinecap="round" d="M150 196 Q160 201 170 196" />
    </g>
  );
}
