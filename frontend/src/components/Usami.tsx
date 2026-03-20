import { motion, useReducedMotion, type Variants } from "framer-motion";
import { useTheme } from "@/hooks/use-theme";

/**
 * Usami — USAM's geometric mascot
 * 
 * A minimal, abstract character composed of:
 * - Graduation cap silhouette (education motif)
 * - Arrow/chevron body (career growth)
 * - Overlapping circular forms (support)
 * 
 * Reacts to: idle, searchFocus, saved, empty, locked, wave
 */

export type UsamiMood =
  | "idle"
  | "searchFocus"
  | "saved"
  | "empty"
  | "locked"
  | "wave";

interface UsamiProps {
  mood?: UsamiMood;
  size?: number;
  className?: string;
}

// Theme-aware color palette
function useUsamiColors() {
  const { theme } = useTheme();
  switch (theme) {
    case "dark":
      return {
        primary: "hsl(178, 72%, 25%)",
        secondary: "hsl(180, 24%, 70%)",
        accent: "hsl(180, 18%, 50%)",
        face: "hsl(0, 0%, 85%)",
        bg: "hsl(0, 0%, 15%)",
      };
    case "night":
      return {
        primary: "hsl(178, 60%, 20%)",
        secondary: "hsl(180, 20%, 55%)",
        accent: "hsl(180, 15%, 40%)",
        face: "hsl(0, 0%, 75%)",
        bg: "hsl(0, 0%, 8%)",
      };
    default:
      return {
        primary: "hsl(178, 72%, 13%)",
        secondary: "hsl(180, 24%, 87%)",
        accent: "hsl(180, 18%, 87%)",
        face: "hsl(0, 0%, 100%)",
        bg: "hsl(0, 0%, 97%)",
      };
  }
}

// Idle breathing animation
const breathe: Variants = {
  idle: {
    scaleY: [1, 1.015, 1],
    transition: { duration: 3.5, repeat: Infinity, ease: "easeInOut" },
  },
};

// Eye blink
const blink: Variants = {
  idle: {
    scaleY: [1, 1, 0.1, 1, 1],
    transition: {
      duration: 4,
      repeat: Infinity,
      times: [0, 0.72, 0.74, 0.76, 1],
      ease: "easeInOut",
    },
  },
};

export function Usami({ mood = "idle", size = 200, className = "" }: UsamiProps) {
  const reduced = useReducedMotion();
  const colors = useUsamiColors();
  const { dir } = useTheme();
  const isRTL = dir === "rtl";

  // Flip mascot for RTL so it faces into the content
  const flipX = isRTL ? -1 : 1;

  // Mood-specific body transforms
  const bodyVariants: Record<UsamiMood, any> = {
    idle: reduced
      ? { rotate: 0, x: 0, y: 0 }
      : { rotate: [0, -1.5, 0, 1.5, 0], x: 0, y: 0, transition: { duration: 6, repeat: Infinity, ease: "easeInOut" } },
    searchFocus: { rotate: -6 * flipX, y: -4, transition: { type: "spring", stiffness: 200, damping: 15 } },
    saved: { rotate: 0, y: [0, -12, 0], transition: { duration: 0.5, ease: "easeOut" } },
    empty: { rotate: 4 * flipX, y: 2, transition: { type: "spring", stiffness: 120, damping: 12 } },
    locked: { rotate: 0, x: 8 * flipX, transition: { duration: 0.8, ease: "easeInOut" } },
    wave: { rotate: -3 * flipX, y: -2, transition: { type: "spring", stiffness: 150, damping: 10 } },
  };

  // Cap tilt per mood
  const capVariants: Record<UsamiMood, any> = {
    idle: reduced
      ? { rotate: 0 }
      : { rotate: [0, -2, 0, 2, 0], transition: { duration: 5, repeat: Infinity, ease: "easeInOut" } },
    searchFocus: { rotate: -8 * flipX, transition: { type: "spring", stiffness: 180, damping: 12 } },
    saved: { rotate: [0, 6 * flipX, 0], transition: { duration: 0.6 } },
    empty: { rotate: 5 * flipX, transition: { duration: 0.4 } },
    locked: { rotate: 0 },
    wave: { rotate: -5 * flipX, transition: { duration: 0.5 } },
  };

  // Arrow indicator
  const arrowVariants: Record<UsamiMood, any> = {
    idle: reduced ? { opacity: 0.3 } : { opacity: [0.2, 0.5, 0.2], y: [0, -3, 0], transition: { duration: 3, repeat: Infinity } },
    searchFocus: { opacity: 0.7, y: -6, transition: { type: "spring", stiffness: 200 } },
    saved: { opacity: 1, y: -10, scale: 1.15, transition: { type: "spring", stiffness: 300, damping: 10 } },
    empty: { opacity: 0.15, y: 4 },
    locked: { opacity: 0.6, x: 12 * flipX, rotate: 90 * flipX, transition: { duration: 0.6, ease: "easeInOut" } },
    wave: { opacity: 0.5, y: -4 },
  };

  // Sparkle for "saved" mood
  const showSparkle = mood === "saved" && !reduced;

  return (
    <motion.svg
      viewBox="0 0 200 220"
      width={size}
      height={size * 1.1}
      className={`select-none ${className}`}
      style={{ transform: `scaleX(${flipX})` }}
      role="img"
      aria-label="Usami career guide mascot"
    >
      {/* ── Body: rounded shield/arrow shape ── */}
      <motion.g
        style={{ originX: "100px", originY: "130px" }}
        animate={bodyVariants[mood]}
      >
        {/* Main body */}
        <motion.path
          d="M60 85 C60 55, 140 55, 140 85 L140 155 C140 175, 120 190, 100 195 C80 190, 60 175, 60 155 Z"
          fill={colors.primary}
          variants={reduced ? undefined : breathe}
          animate="idle"
          style={{ originX: "100px", originY: "140px" }}
        />

        {/* Overlapping support circle (left) */}
        <circle cx="72" cy="100" r="18" fill={colors.secondary} opacity={0.35} />
        {/* Overlapping support circle (right) */}
        <circle cx="128" cy="100" r="18" fill={colors.secondary} opacity={0.35} />

        {/* Face area */}
        <ellipse cx="100" cy="115" rx="28" ry="24" fill={colors.face} opacity={0.95} />

        {/* Eyes */}
        <motion.g variants={reduced ? undefined : blink} animate="idle">
          <ellipse cx="88" cy="112" rx="4" ry="4.5" fill={colors.primary} />
          <ellipse cx="112" cy="112" rx="4" ry="4.5" fill={colors.primary} />
        </motion.g>

        {/* Gentle smile */}
        <path
          d="M92 124 Q100 130 108 124"
          fill="none"
          stroke={colors.primary}
          strokeWidth="2"
          strokeLinecap="round"
          opacity={mood === "empty" ? 0 : 1}
        />
        {/* Neutral mouth for empty */}
        {mood === "empty" && (
          <line x1="92" y1="125" x2="108" y2="125" stroke={colors.primary} strokeWidth="2" strokeLinecap="round" />
        )}

        {/* ── Graduation cap ── */}
        <motion.g
          style={{ originX: "100px", originY: "70px" }}
          animate={capVariants[mood]}
        >
          {/* Cap base (diamond/rhombus) */}
          <polygon
            points="50,68 100,48 150,68 100,82"
            fill={colors.primary}
          />
          {/* Cap top block */}
          <rect x="82" y="55" width="36" height="14" rx="2" fill={colors.primary} />
          {/* Tassel */}
          <motion.g
            animate={
              reduced
                ? {}
                : {
                    rotate: [0, 8, -4, 0],
                    transition: { duration: 2.5, repeat: Infinity, ease: "easeInOut" },
                  }
            }
            style={{ originX: "135px", originY: "62px" }}
          >
            <line x1="135" y1="62" x2="148" y2="78" stroke={colors.accent} strokeWidth="2.5" strokeLinecap="round" />
            <circle cx="148" cy="80" r="3.5" fill={colors.accent} />
          </motion.g>
        </motion.g>

        {/* ── Growth arrow indicator ── */}
        <motion.g animate={arrowVariants[mood]}>
          <path
            d="M100 170 L100 198 M92 190 L100 200 L108 190"
            fill="none"
            stroke={colors.primary}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity={0.6}
          />
        </motion.g>

        {/* ── Sparkle effects (saved mood) ── */}
        {showSparkle && (
          <>
            {[
              { cx: 55, cy: 75, delay: 0 },
              { cx: 145, cy: 80, delay: 0.15 },
              { cx: 70, cy: 155, delay: 0.25 },
              { cx: 135, cy: 150, delay: 0.1 },
            ].map((sp, i) => (
              <motion.circle
                key={i}
                cx={sp.cx}
                cy={sp.cy}
                r="2.5"
                fill={colors.accent}
                initial={{ opacity: 0, scale: 0 }}
                animate={{
                  opacity: [0, 1, 0],
                  scale: [0, 1.5, 0],
                  transition: { duration: 0.7, delay: sp.delay, ease: "easeOut" },
                }}
              />
            ))}
          </>
        )}

        {/* ── Pointing hand for locked mood ── */}
        {mood === "locked" && (
          <motion.g
            initial={{ opacity: 0, x: -10 * flipX }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3, duration: 0.4, ease: "easeOut" }}
          >
            <path
              d="M142 135 L165 130 L160 126 L170 124"
              fill="none"
              stroke={colors.primary}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {/* Arrow tip pointing right */}
            <polygon
              points="170,120 178,124 170,128"
              fill={colors.primary}
            />
          </motion.g>
        )}
      </motion.g>
    </motion.svg>
  );
}
