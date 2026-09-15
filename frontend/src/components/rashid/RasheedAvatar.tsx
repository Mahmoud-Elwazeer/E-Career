import { motion, useReducedMotion } from "framer-motion";

/**
 * RasheedAvatar — a polished, professional AI career-coach avatar.
 *
 * A framed circular headshot (the pattern used by modern AI assistants and
 * professional networks) with soft shading, brand-aligned styling, subtle
 * ambient ring, and expression states. Designed to read as a competent HR
 * professional rather than a cartoon mascot.
 *
 * States:
 *  - idle: gentle breathing + occasional blink
 *  - greeting: warm smile, slight head tilt
 *  - thinking: eyes up, brow raised
 *  - talking: subtle mouth motion
 */

export type RasheedExpression = "idle" | "greeting" | "thinking" | "talking";

interface RasheedAvatarProps {
  expression?: RasheedExpression;
  /** pixel size of the round avatar */
  size?: number;
  /** show the animated status ring */
  ring?: boolean;
  className?: string;
}

const C = {
  bgTop: "#12514D",
  bgBottom: "#0A3836",
  skin: "#E7C2A0",
  skinShade: "#D3A784",
  skinLight: "#F2D6BB",
  hair: "#241D18",
  hairHi: "#3A2E25",
  suit: "#0C403D",
  suitHi: "#155F5A",
  shirt: "#F2F7F6",
  tie: "#2A8F88",
  brow: "#241D18",
  eyeWhite: "#FBF7F2",
  iris: "#3B2C21",
  mouth: "#A85C54",
  teeth: "#FFF8F2",
};

export function RasheedAvatar({
  expression = "idle",
  size = 64,
  ring = true,
  className = "",
}: RasheedAvatarProps) {
  const reduced = useReducedMotion();
  const thinking = expression === "thinking";
  const greeting = expression === "greeting";
  const talking = expression === "talking";

  return (
    <div className={`relative inline-flex ${className}`} style={{ width: size, height: size }}>
      {/* Ambient status ring */}
      {ring && (
        <motion.span
          aria-hidden
          className="absolute inset-0 rounded-full"
          style={{ boxShadow: "0 0 0 2px hsl(var(--secondary) / 0.5)" }}
          animate={reduced ? undefined : { boxShadow: [
            "0 0 0 2px hsl(var(--secondary) / 0.5)",
            "0 0 0 4px hsl(var(--secondary) / 0.15)",
            "0 0 0 2px hsl(var(--secondary) / 0.5)",
          ] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        />
      )}

      <motion.svg
        viewBox="0 0 120 120"
        width={size}
        height={size}
        className="rounded-full"
        initial={false}
        animate={reduced ? undefined : { y: [0, -1.2, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        role="img"
        aria-label="Rasheed, AI career coach"
      >
        <defs>
          <radialGradient id="ra-bg" cx="0.5" cy="0.35" r="0.75">
            <stop offset="0" stopColor={C.bgTop} />
            <stop offset="1" stopColor={C.bgBottom} />
          </radialGradient>
          <linearGradient id="ra-skin" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={C.skinLight} />
            <stop offset="1" stopColor={C.skinShade} />
          </linearGradient>
          <linearGradient id="ra-suit" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor={C.suitHi} />
            <stop offset="1" stopColor={C.suit} />
          </linearGradient>
          <clipPath id="ra-clip"><circle cx="60" cy="60" r="60" /></clipPath>
        </defs>

        <g clipPath="url(#ra-clip)">
          {/* Background */}
          <rect width="120" height="120" fill="url(#ra-bg)" />
          {/* soft vignette */}
          <circle cx="60" cy="46" r="46" fill="#fff" opacity="0.05" />

          {/* Shoulders / suit */}
          <path d="M18 120 Q22 92 60 86 Q98 92 102 120 Z" fill="url(#ra-suit)" />
          {/* Shirt */}
          <path d="M50 90 L60 104 L70 90 L70 120 L50 120 Z" fill={C.shirt} />
          {/* Tie */}
          <path d="M60 104 L55 110 L60 120 L65 110 Z" fill={C.tie} />
          {/* Lapels */}
          <path d="M50 90 L60 104 L52 106 L42 94 Z" fill={C.suit} />
          <path d="M70 90 L60 104 L68 106 L78 94 Z" fill={C.suit} />

          {/* Neck */}
          <path d="M52 78 h16 v10 q-8 6 -16 0 Z" fill={C.skinShade} />

          {/* Head */}
          <ellipse cx="60" cy="54" rx="24" ry="26" fill="url(#ra-skin)" />
          {/* Ears */}
          <ellipse cx="37" cy="56" rx="4" ry="6" fill={C.skinShade} />
          <ellipse cx="83" cy="56" rx="4" ry="6" fill={C.skinShade} />

          {/* Hair */}
          <path d="M36 52 Q37 26 60 25 Q83 26 84 52 Q76 38 60 37 Q44 38 36 52 Z" fill={C.hair} />
          <path d="M36 52 Q35 42 41 34 L44 50 Z" fill={C.hairHi} opacity="0.5" />
          {/* Beard hint */}
          <path d="M40 60 Q40 76 60 82 Q80 76 80 60 Q72 70 60 71 Q48 70 40 60 Z" fill={C.hair} opacity="0.12" />

          {/* Eyebrows */}
          <motion.g
            animate={reduced ? undefined : { y: thinking ? -2 : 0 }}
            transition={{ duration: 0.4 }}
          >
            <path d="M46 47 Q52 44 57 47" stroke={C.brow} strokeWidth="2.2" fill="none" strokeLinecap="round" />
            <path d="M63 47 Q68 44 74 47" stroke={C.brow} strokeWidth="2.2" fill="none" strokeLinecap="round" />
          </motion.g>

          {/* Eyes */}
          <motion.g
            style={{ transformOrigin: "60px 54px" }}
            animate={reduced ? undefined : { scaleY: [1, 1, 0.1, 1, 1] }}
            transition={{ duration: 5, repeat: Infinity, times: [0, 0.62, 0.66, 0.7, 1] }}
          >
            <g transform={thinking ? "translate(2,-1.5)" : "translate(0,0)"}>
              <ellipse cx="51" cy="54" rx="4.6" ry="4" fill={C.eyeWhite} />
              <ellipse cx="69" cy="54" rx="4.6" ry="4" fill={C.eyeWhite} />
              <circle cx="52" cy="54" r="2.3" fill={C.iris} />
              <circle cx="70" cy="54" r="2.3" fill={C.iris} />
              <circle cx="52.9" cy="53.1" r="0.8" fill="#fff" />
              <circle cx="70.9" cy="53.1" r="0.8" fill="#fff" />
            </g>
          </motion.g>

          {/* Nose */}
          <path d="M60 56 Q61 62 56 64" stroke={C.skinShade} strokeWidth="1.6" fill="none" strokeLinecap="round" />

          {/* Mouth */}
          {talking && !reduced ? (
            <motion.ellipse
              cx="60" cy="70" rx="6" fill={C.mouth}
              animate={{ ry: [1.5, 4, 2, 3.5, 1.5] }}
              transition={{ duration: 0.7, repeat: Infinity }}
            />
          ) : greeting ? (
            <>
              <path d="M50 68 Q60 78 70 68 Q60 73 50 68 Z" fill={C.mouth} />
              <path d="M52 69 Q60 72 68 69" fill={C.teeth} opacity="0.9" />
            </>
          ) : (
            <path d="M52 69 Q60 75 68 69" stroke={C.mouth} strokeWidth="2.2" fill="none" strokeLinecap="round" />
          )}
        </g>

        {/* Inner rim */}
        <circle cx="60" cy="60" r="59" fill="none" stroke="#000" strokeOpacity="0.08" strokeWidth="2" />
      </motion.svg>

      {/* Thinking dots */}
      {thinking && !reduced && (
        <span className="absolute -top-1 -end-1 flex gap-0.5 rounded-full bg-card px-1.5 py-1 shadow-md">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="h-1 w-1 rounded-full bg-primary"
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
            />
          ))}
        </span>
      )}
    </div>
  );
}
