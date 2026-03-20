import { useEffect, useState, useRef, useCallback } from "react";
import { motion, useReducedMotion, AnimatePresence } from "framer-motion";
import { Lock } from "lucide-react";

/**
 * LoginCareerGuide — Bust variant of the Career Guide character
 * Same face, glasses, cap, colors, shading as the hero full-body version.
 * Shows head + shoulders + 3 floating chips with lock→unlock behavior.
 * Idle loop: breathing, blink, glasses adjust (≈10s cycle).
 * Hover Google button → confident smile + chip highlight.
 * Click Google → chips unlock (lock dissolves).
 */

/* ── Brand palette (identical to hero CareerGuide) ── */
const P = {
  primary: "#0A3836",
  primaryLight: "#134E4A",
  primaryMid: "#1A5C58",
  primaryGlow: "#1D6B66",
  skin: "#D4C4B0",
  skinShadow: "#C4B09A",
  skinHighlight: "#E0D5C8",
  skinDeep: "#B8A48E",
  neutral3: "#BECFCF",
  dark: "#1A1A1A",
  darkSoft: "#2A2A2A",
} as const;

/* ── Chips ── */
const CHIPS = [
  { label: "Remote", dotColor: "#4ADE80", x: -72, y: -28 },
  { label: "Junior", dotColor: "#60A5FA", x: 72, y: -8 },
  { label: "Full-time", dotColor: "#FBBF24", x: -58, y: 32 },
];

/* ── Idle phase machine (≈10s) ── */
type Phase = "rest" | "blink1" | "rest2" | "adjustGlasses" | "blink2" | "rest3";
const PHASE_ORDER: Phase[] = ["rest", "blink1", "rest2", "adjustGlasses", "blink2", "rest3"];
const PHASE_DURATIONS: Record<Phase, number> = {
  rest: 2000, blink1: 300, rest2: 2500, adjustGlasses: 1800, blink2: 300, rest3: 2600,
};

interface LoginCareerGuideProps {
  isHoveringGoogle?: boolean;
  isUnlocking?: boolean;
  className?: string;
}

export function LoginCareerGuide({
  isHoveringGoogle = false,
  isUnlocking = false,
  className = "",
}: LoginCareerGuideProps) {
  const reduced = useReducedMotion();
  const [phase, setPhase] = useState<Phase>("rest");
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  const isBlinking = phase === "blink1" || phase === "blink2";
  const glassesNudge = phase === "adjustGlasses" ? -2 : 0;
  const isSmiling = isHoveringGoogle || isUnlocking;

  /* Phase cycling */
  const advance = useCallback(() => {
    setPhase((prev) => {
      const idx = PHASE_ORDER.indexOf(prev);
      return PHASE_ORDER[(idx + 1) % PHASE_ORDER.length];
    });
  }, []);

  useEffect(() => {
    if (reduced) return;
    timerRef.current = setTimeout(advance, PHASE_DURATIONS[phase]);
    return () => clearTimeout(timerRef.current);
  }, [phase, reduced, advance]);

  if (reduced) {
    return (
      <div className={`relative flex items-center justify-center ${className}`}>
        <StaticChips />
        <svg viewBox="0 0 200 200" width="140" height="140" fill="none" role="img" aria-label="Career Guide">
          <StaticDefs />
          <StaticBust />
        </svg>
      </div>
    );
  }

  return (
    <div className={`relative flex items-center justify-center ${className}`} style={{ width: 220, height: 180 }}>
      {/* ── Floating chips ── */}
      {CHIPS.map((chip, i) => (
        <motion.div
          key={chip.label}
          className="absolute pointer-events-none whitespace-nowrap"
          style={{
            top: `calc(50% + ${chip.y}px)`,
            left: `calc(50% + ${chip.x}px)`,
            zIndex: 20,
          }}
          initial={{ opacity: 0, scale: 0.8, y: 10 }}
          animate={{
            opacity: isUnlocking ? 0.95 : 0.55,
            scale: isHoveringGoogle && i === 0 ? 1.06 : 1,
            y: [0, -chip.y * 0.04, 0],
          }}
          transition={{
            opacity: { duration: 0.5 },
            scale: { duration: 0.3 },
            y: { duration: 5 + i, repeat: Infinity, ease: "easeInOut", delay: i * 0.4 },
          }}
        >
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-medium tracking-wide"
            style={{
              background: "rgba(255,255,255,0.1)",
              border: `1px solid rgba(255,255,255,${isHoveringGoogle && i === 0 ? 0.35 : 0.15})`,
              color: "rgba(255,255,255,0.7)",
              boxShadow: isHoveringGoogle && i === 0
                ? `0 0 0 2px rgba(74,222,128,0.15), 0 2px 8px rgba(10,56,54,0.15)`
                : "none",
              transition: "border-color 0.3s, box-shadow 0.3s",
            }}
          >
            <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: chip.dotColor, opacity: 0.7 }} />
            <span>{chip.label}</span>

            {/* Lock icon — dissolves on unlock */}
            <AnimatePresence>
              {!isUnlocking && (
                <motion.span
                  initial={{ opacity: 0.5, scale: 1 }}
                  animate={{ opacity: 0.4, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.5 }}
                  transition={{ duration: 0.4 }}
                  className="ml-0.5"
                >
                  <Lock className="w-2.5 h-2.5" style={{ color: "rgba(255,255,255,0.4)" }} />
                </motion.span>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      ))}

      {/* ── SVG Bust ── */}
      <motion.svg
        viewBox="0 0 200 200"
        width="140"
        height="140"
        fill="none"
        role="img"
        aria-label="Career Guide character"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0, 0, 0.2, 1] }}
        className="relative z-10"
      >
        <defs>
          <linearGradient id="lg-skin" x1="0" y1="0" x2="0.2" y2="1">
            <stop offset="0%" stopColor={P.skinHighlight} />
            <stop offset="70%" stopColor={P.skin} />
            <stop offset="100%" stopColor={P.skinShadow} />
          </linearGradient>
          <linearGradient id="lg-body" x1="0.3" y1="0" x2="0.7" y2="1">
            <stop offset="0%" stopColor={P.primaryGlow} />
            <stop offset="40%" stopColor={P.primaryMid} />
            <stop offset="100%" stopColor={P.primary} />
          </linearGradient>
          <linearGradient id="lg-cap" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={P.primaryGlow} />
            <stop offset="100%" stopColor={P.primary} />
          </linearGradient>
          <linearGradient id="lg-lens" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={P.neutral3} stopOpacity="0.2" />
            <stop offset="100%" stopColor={P.neutral3} stopOpacity="0.04" />
          </linearGradient>
          <linearGradient id="lg-hair" x1="0.2" y1="0" x2="0.8" y2="1">
            <stop offset="0%" stopColor={P.primaryMid} />
            <stop offset="100%" stopColor={P.primary} />
          </linearGradient>
        </defs>

        {/* ── Shoulders + upper torso ── */}
        <motion.path
          d="M65 155 Q65 142 80 137 L120 137 Q135 142 135 155 L138 200 L62 200 Z"
          fill="url(#lg-body)"
          animate={{
            d: [
              "M65 155 Q65 142 80 137 L120 137 Q135 142 135 155 L138 200 L62 200 Z",
              "M64 155 Q64 141 79 136 L121 136 Q136 141 136 155 L139 200 L61 200 Z",
              "M65 155 Q65 142 80 137 L120 137 Q135 142 135 155 L138 200 L62 200 Z",
            ],
          }}
          transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
        />
        {/* Collar */}
        <path d="M80 137 L100 150 L120 137" stroke={P.neutral3} strokeWidth="1.2" fill="none" strokeLinecap="round" />
        {/* Shoulders */}
        <path d="M65 155 Q50 158 42 175 Q40 180 44 181 Q50 170 65 160" fill="url(#lg-body)" />
        <path d="M135 155 Q150 158 158 175 Q160 180 156 181 Q150 170 135 160" fill="url(#lg-body)" />

        {/* ══ HEAD ══ */}
        <motion.g
          animate={{ rotate: isSmiling ? 2 : 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          style={{ originX: "100px", originY: "120px" }}
        >
          {/* Neck */}
          <rect x="93" y="125" width="14" height="14" rx="5" fill="url(#lg-skin)" />
          <rect x="93" y="134" width="14" height="4" rx="2" fill={P.skinShadow} opacity="0.3" />

          {/* Head */}
          <ellipse cx="100" cy="90" rx="32" ry="38" fill="url(#lg-skin)" />
          {/* Cheek blush */}
          <ellipse cx="78" cy="102" rx="6" ry="3.5" fill="#D4A89A" opacity="0.06" />
          <ellipse cx="122" cy="102" rx="6" ry="3.5" fill="#D4A89A" opacity="0.06" />
          {/* Jaw shadow */}
          <ellipse cx="100" cy="122" rx="22" ry="4" fill={P.skinShadow} opacity="0.1" />

          {/* Ears */}
          <ellipse cx="68" cy="88" rx="4.5" ry="7" fill={P.skin} />
          <ellipse cx="69" cy="88" rx="2.5" ry="4.5" fill={P.skinShadow} opacity="0.2" />
          <ellipse cx="132" cy="88" rx="4.5" ry="7" fill={P.skin} />
          <ellipse cx="131" cy="88" rx="2.5" ry="4.5" fill={P.skinShadow} opacity="0.2" />

          {/* Hair */}
          <path
            d="M68 76 Q68 50 100 44 Q132 50 132 76 L132 66 Q132 52 100 47 Q68 52 68 66 Z"
            fill="url(#lg-hair)"
          />
          <rect x="68" y="73" width="3" height="10" rx="1.5" fill={P.primary} opacity="0.4" />
          <rect x="129" y="73" width="3" height="10" rx="1.5" fill={P.primary} opacity="0.4" />

          {/* ── Graduation cap ── */}
          <motion.g
            animate={{ y: phase === "adjustGlasses" ? -1 : 0 }}
            transition={{ duration: 0.3 }}
          >
            <path d="M58 58 L142 58 L135 50 Q100 43 65 50 Z" fill="url(#lg-cap)" opacity="0.8" />
            <rect x="96" y="47" width="8" height="3" rx="1.5" fill={P.primaryLight} opacity="0.5" />
            {/* Tassel */}
            <motion.path
              d="M135 54 Q144 59 142 74"
              stroke={P.neutral3}
              strokeWidth="1.2"
              strokeLinecap="round"
              fill="none"
              animate={{ d: ["M135 54 Q144 59 142 74", "M135 54 Q146 62 144 74", "M135 54 Q144 59 142 74"] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
            />
            <motion.circle
              cx="142" cy="75" r="2.5"
              fill={P.neutral3}
              animate={{ cy: [75, 77, 75] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
            />
          </motion.g>

          {/* ── Glasses ── */}
          <motion.g
            animate={{ y: glassesNudge }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
          >
            <path d="M91 88 Q100 85 109 88" stroke={P.dark} strokeWidth="0.8" fill="none" />
            <rect x="76" y="82" width="17" height="13" rx="4.5" stroke={P.dark} strokeWidth="1" fill="url(#lg-lens)" />
            <motion.rect
              x="78" y="84" width="5" height="1.5" rx="0.75"
              fill="white" opacity="0.2"
              animate={phase === "adjustGlasses" ? { opacity: [0.2, 0.6, 0.2] } : { opacity: 0.2 }}
              transition={{ duration: 0.8 }}
            />
            <rect x="107" y="82" width="17" height="13" rx="4.5" stroke={P.dark} strokeWidth="1" fill="url(#lg-lens)" />
            <rect x="109" y="84" width="4" height="1.2" rx="0.6" fill="white" opacity="0.15" />
            <line x1="76" y1="87" x2="68" y2="85" stroke={P.dark} strokeWidth="0.8" />
            <line x1="124" y1="87" x2="132" y2="85" stroke={P.dark} strokeWidth="0.8" />
          </motion.g>

          {/* ── Eyes ── */}
          <motion.g
            animate={{ scaleY: isBlinking ? 0.04 : 1 }}
            transition={{ duration: isBlinking ? 0.1 : 0.15 }}
            style={{ originX: "100px", originY: "90px" }}
          >
            <ellipse cx="84" cy="90" rx="4" ry="3.5" fill="white" opacity="0.9" />
            <ellipse cx="84" cy="90" rx="2.5" ry="2.5" fill={P.dark} />
            <circle cx="85.2" cy="89" r="0.8" fill="white" opacity="0.85" />

            <ellipse cx="116" cy="90" rx="4" ry="3.5" fill="white" opacity="0.9" />
            <ellipse cx="116" cy="90" rx="2.5" ry="2.5" fill={P.dark} />
            <circle cx="117.2" cy="89" r="0.8" fill="white" opacity="0.85" />
          </motion.g>

          {/* Eyebrows */}
          <path d="M78 78 Q83 75 90 77" stroke={P.primary} strokeWidth="1.5" strokeLinecap="round" fill="none" />
          <path d="M110 77 Q117 75 122 78" stroke={P.primary} strokeWidth="1.5" strokeLinecap="round" fill="none" />

          {/* Nose */}
          <path d="M97 99 Q100 103 103 99" stroke={P.skinShadow} strokeWidth="1" strokeLinecap="round" fill="none" />

          {/* Mouth */}
          <motion.path
            fill="none"
            stroke={P.darkSoft}
            strokeWidth="1.2"
            strokeLinecap="round"
            animate={{
              d: isSmiling
                ? "M90 110 Q100 118 110 110"
                : "M92 110 Q100 114 108 110",
            }}
            transition={{ duration: 0.35, ease: "easeOut" }}
          />
        </motion.g>
      </motion.svg>
    </div>
  );
}

/* ── Static helpers for reduced motion ── */
function StaticChips() {
  return (
    <>
      {CHIPS.map((chip) => (
        <div
          key={chip.label}
          className="absolute pointer-events-none whitespace-nowrap"
          style={{
            top: `calc(50% + ${chip.y}px)`,
            left: `calc(50% + ${chip.x}px)`,
            opacity: 0.45,
            zIndex: 20,
          }}
        >
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-medium tracking-wide"
            style={{ background: "rgba(255,255,255,0.1)", border: "1px solid rgba(255,255,255,0.15)", color: "rgba(255,255,255,0.7)" }}>
            <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: chip.dotColor, opacity: 0.7 }} />
            {chip.label}
          </div>
        </div>
      ))}
    </>
  );
}

function StaticDefs() {
  return (
    <defs>
      <linearGradient id="lg-skin" x1="0" y1="0" x2="0.2" y2="1">
        <stop offset="0%" stopColor={P.skinHighlight} />
        <stop offset="70%" stopColor={P.skin} />
        <stop offset="100%" stopColor={P.skinShadow} />
      </linearGradient>
      <linearGradient id="lg-body" x1="0.3" y1="0" x2="0.7" y2="1">
        <stop offset="0%" stopColor={P.primaryGlow} />
        <stop offset="40%" stopColor={P.primaryMid} />
        <stop offset="100%" stopColor={P.primary} />
      </linearGradient>
      <linearGradient id="lg-cap" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor={P.primaryGlow} />
        <stop offset="100%" stopColor={P.primary} />
      </linearGradient>
      <linearGradient id="lg-lens" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor={P.neutral3} stopOpacity="0.2" />
        <stop offset="100%" stopColor={P.neutral3} stopOpacity="0.04" />
      </linearGradient>
      <linearGradient id="lg-hair" x1="0.2" y1="0" x2="0.8" y2="1">
        <stop offset="0%" stopColor={P.primaryMid} />
        <stop offset="100%" stopColor={P.primary} />
      </linearGradient>
    </defs>
  );
}

function StaticBust() {
  return (
    <g>
      <path d="M65 155 Q65 142 80 137 L120 137 Q135 142 135 155 L138 200 L62 200 Z" fill="url(#lg-body)" />
      <path d="M80 137 L100 150 L120 137" stroke={P.neutral3} strokeWidth="1.2" fill="none" strokeLinecap="round" />
      <path d="M65 155 Q50 158 42 175 Q40 180 44 181 Q50 170 65 160" fill="url(#lg-body)" />
      <path d="M135 155 Q150 158 158 175 Q160 180 156 181 Q150 170 135 160" fill="url(#lg-body)" />
      <rect x="93" y="125" width="14" height="14" rx="5" fill="url(#lg-skin)" />
      <ellipse cx="100" cy="90" rx="32" ry="38" fill="url(#lg-skin)" />
      <path d="M68 76 Q68 50 100 44 Q132 50 132 76 L132 66 Q132 52 100 47 Q68 52 68 66 Z" fill="url(#lg-hair)" />
      <path d="M58 58 L142 58 L135 50 Q100 43 65 50 Z" fill="url(#lg-cap)" opacity="0.8" />
      <path d="M135 54 Q144 59 142 74" stroke={P.neutral3} strokeWidth="1.2" strokeLinecap="round" fill="none" />
      <circle cx="142" cy="75" r="2.5" fill={P.neutral3} />
      <path d="M91 88 Q100 85 109 88" stroke={P.dark} strokeWidth="0.8" fill="none" />
      <rect x="76" y="82" width="17" height="13" rx="4.5" stroke={P.dark} strokeWidth="1" fill="url(#lg-lens)" />
      <rect x="107" y="82" width="17" height="13" rx="4.5" stroke={P.dark} strokeWidth="1" fill="url(#lg-lens)" />
      <line x1="76" y1="87" x2="68" y2="85" stroke={P.dark} strokeWidth="0.8" />
      <line x1="124" y1="87" x2="132" y2="85" stroke={P.dark} strokeWidth="0.8" />
      <ellipse cx="84" cy="90" rx="2.5" ry="2.5" fill={P.dark} />
      <circle cx="85.2" cy="89" r="0.8" fill="white" opacity="0.85" />
      <ellipse cx="116" cy="90" rx="2.5" ry="2.5" fill={P.dark} />
      <circle cx="117.2" cy="89" r="0.8" fill="white" opacity="0.85" />
      <path d="M78 78 Q83 75 90 77" stroke={P.primary} strokeWidth="1.5" strokeLinecap="round" fill="none" />
      <path d="M110 77 Q117 75 122 78" stroke={P.primary} strokeWidth="1.5" strokeLinecap="round" fill="none" />
      <path d="M97 99 Q100 103 103 99" stroke={P.skinShadow} strokeWidth="1" strokeLinecap="round" fill="none" />
      <path fill="none" stroke={P.darkSoft} strokeWidth="1.2" strokeLinecap="round" d="M92 110 Q100 114 108 110" />
    </g>
  );
}
