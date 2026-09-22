import { motion, useReducedMotion } from "framer-motion";

/**
 * RasheedAvatar — the platform's AI career-coach identity.
 *
 * A framed circular headshot redesigned to read as a poised, modern HR
 * professional (almond eyes with real lids, groomed beard, tailored collar &
 * tie, refined head geometry) rather than a cartoon mascot. Brand-aligned teal
 * backdrop, soft studio lighting, subtle depth. Same expression-state API as
 * before so every consumer keeps working.
 *
 * States:
 *  - idle: gentle breathing + occasional blink
 *  - greeting: warm smile, brighter eyes
 *  - thinking: eyes up, brow raised, thinking dots
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
  skin: "#D9A87E",
  skinShade: "#C08F66",
  skinLight: "#ECC49A",
  hair: "#1E1712",
  hairHi: "#332720",
  beard: "#241B14",
  suit: "#0A3836",
  suitHi: "#12514D",
  collar: "#F4F8F7",
  tie: "#E4B65B", // signal amber tie — a single warm accent
  brow: "#241B14",
  eyeWhite: "#FCFAF6",
  iris: "#4A3627",
  lid: "#C08F66",
  mouth: "#9E5049",
  teeth: "#FFFBF6",
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
        animate={reduced ? undefined : { y: [0, -1, 0] }}
        transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
        role="img"
        aria-label="Rasheed, AI career coach"
      >
        <defs>
          <radialGradient id="ra-bg" cx="0.5" cy="0.3" r="0.85">
            <stop offset="0" stopColor="#15605B" />
            <stop offset="0.6" stopColor="#0C433F" />
            <stop offset="1" stopColor="#082E2C" />
          </radialGradient>
          <linearGradient id="ra-skin" x1="0.3" y1="0" x2="0.7" y2="1">
            <stop offset="0" stopColor={C.skinLight} />
            <stop offset="0.55" stopColor={C.skin} />
            <stop offset="1" stopColor={C.skinShade} />
          </linearGradient>
          <linearGradient id="ra-suit" x1="0" y1="0" x2="0.5" y2="1">
            <stop offset="0" stopColor={C.suitHi} />
            <stop offset="1" stopColor={C.suit} />
          </linearGradient>
          <radialGradient id="ra-light" cx="0.38" cy="0.32" r="0.5">
            <stop offset="0" stopColor="#fff" stopOpacity="0.22" />
            <stop offset="1" stopColor="#fff" stopOpacity="0" />
          </radialGradient>
          <clipPath id="ra-clip"><circle cx="60" cy="60" r="60" /></clipPath>
        </defs>

        <g clipPath="url(#ra-clip)">
          <rect width="120" height="120" fill="url(#ra-bg)" />
          {/* studio key light */}
          <rect width="120" height="120" fill="url(#ra-light)" />

          {/* Shoulders / tailored suit */}
          <path d="M14 120 Q18 90 60 84 Q102 90 106 120 Z" fill="url(#ra-suit)" />
          {/* shoulder seam highlights */}
          <path d="M60 84 Q40 90 30 118" stroke={C.suitHi} strokeWidth="1.4" fill="none" opacity="0.5" />
          <path d="M60 84 Q80 90 90 118" stroke={C.suitHi} strokeWidth="1.4" fill="none" opacity="0.5" />
          {/* Collar */}
          <path d="M48 88 L60 100 L72 88 L70 120 L50 120 Z" fill={C.collar} />
          {/* Tie knot + tie */}
          <path d="M60 100 L55 105 L60 120 L65 105 Z" fill={C.tie} />
          <path d="M56 100 L60 104 L64 100 L60 97 Z" fill={C.tie} />
          {/* Lapels over collar */}
          <path d="M48 88 L60 100 L51 103 L40 92 Z" fill={C.suit} />
          <path d="M72 88 L60 100 L69 103 L80 92 Z" fill={C.suit} />

          {/* Neck */}
          <path d="M53 76 h14 v11 q-7 5 -14 0 Z" fill={C.skinShade} />

          {/* Head — slightly tapered jaw for a mature, defined face */}
          <path d="M38 50 Q38 28 60 27 Q82 28 82 50 Q82 68 72 78 Q66 84 60 84 Q54 84 48 78 Q38 68 38 50 Z" fill="url(#ra-skin)" />
          {/* cheek/jaw shading */}
          <path d="M44 66 Q52 80 60 82 Q68 80 76 66 Q70 74 60 75 Q50 74 44 66 Z" fill={C.skinShade} opacity="0.35" />
          {/* Ears */}
          <ellipse cx="38" cy="54" rx="3.6" ry="6" fill={C.skinShade} />
          <ellipse cx="82" cy="54" rx="3.6" ry="6" fill={C.skinShade} />

          {/* Groomed beard along the jaw */}
          <path d="M42 58 Q42 78 60 84 Q78 78 78 58 Q78 70 72 76 Q66 81 60 81 Q54 81 48 76 Q42 70 42 58 Z" fill={C.beard} />
          {/* keep upper cheeks clear of beard */}
          <path d="M46 56 Q52 66 60 67 Q68 66 74 56 Q68 61 60 61 Q52 61 46 56 Z" fill="url(#ra-skin)" />

          {/* Hair — modern short crop with a defined hairline */}
          <path d="M37 50 Q36 27 60 25 Q84 27 83 50 Q83 44 78 40 Q74 33 60 32 Q46 33 42 40 Q37 44 37 50 Z" fill={C.hair} />
          <path d="M40 42 Q48 34 60 34 Q56 37 50 39 Q44 41 40 46 Z" fill={C.hairHi} opacity="0.6" />

          {/* Eyebrows — defined, slight arch */}
          <motion.g animate={reduced ? undefined : { y: thinking ? -2.5 : 0 }} transition={{ duration: 0.4 }}>
            <path d="M45 47 Q51 43.5 57 46" stroke={C.brow} strokeWidth="2.6" fill="none" strokeLinecap="round" />
            <path d="M63 46 Q69 43.5 75 47" stroke={C.brow} strokeWidth="2.6" fill="none" strokeLinecap="round" />
          </motion.g>

          {/* Eyes — almond shaped with upper lid, not round cartoon dots */}
          <motion.g
            style={{ transformOrigin: "60px 55px" }}
            animate={reduced ? undefined : { scaleY: [1, 1, 0.08, 1, 1] }}
            transition={{ duration: 5.5, repeat: Infinity, times: [0, 0.63, 0.665, 0.7, 1] }}
          >
            <g transform={thinking ? "translate(1.5,-1.5)" : "translate(0,0)"}>
              {/* left */}
              <path d="M46 55 Q51 51 57 55 Q51 58.5 46 55 Z" fill={C.eyeWhite} />
              <circle cx="52" cy="55" r="2.5" fill={C.iris} />
              <circle cx="52.9" cy="54" r="0.9" fill="#fff" />
              <path d="M46 55 Q51 51 57 55" stroke={C.lid} strokeWidth="1" fill="none" opacity="0.7" />
              {/* right */}
              <path d="M63 55 Q69 51 74 55 Q69 58.5 63 55 Z" fill={C.eyeWhite} />
              <circle cx="68" cy="55" r="2.5" fill={C.iris} />
              <circle cx="68.9" cy="54" r="0.9" fill="#fff" />
              <path d="M63 55 Q69 51 74 55" stroke={C.lid} strokeWidth="1" fill="none" opacity="0.7" />
            </g>
          </motion.g>

          {/* Nose — subtle bridge + tip */}
          <path d="M60 57 L59 64 Q60 66 62 65" stroke={C.skinShade} strokeWidth="1.5" fill="none" strokeLinecap="round" />

          {/* Mouth (in the beard area) */}
          {talking && !reduced ? (
            <motion.ellipse
              cx="60" cy="71" rx="5.5" fill={C.mouth}
              animate={{ ry: [1.3, 3.6, 1.8, 3, 1.3] }}
              transition={{ duration: 0.7, repeat: Infinity }}
            />
          ) : greeting ? (
            <>
              <path d="M51 69 Q60 77 69 69 Q60 73 51 69 Z" fill={C.mouth} />
              <path d="M53 70 Q60 72.5 67 70" fill={C.teeth} opacity="0.95" />
            </>
          ) : (
            <path d="M53 70 Q60 74.5 67 70" stroke={C.mouth} strokeWidth="2.2" fill="none" strokeLinecap="round" />
          )}
        </g>

        {/* Inner rim for depth */}
        <circle cx="60" cy="60" r="59" fill="none" stroke="#000" strokeOpacity="0.1" strokeWidth="2" />
      </motion.svg>

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
