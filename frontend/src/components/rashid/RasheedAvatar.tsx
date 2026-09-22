import { motion, useReducedMotion } from "framer-motion";

/**
 * RasheedAvatar — the platform's AI career-coach identity, as a round headshot.
 *
 * Matches the redesigned hero character (RasheedScene): a modern, friendly,
 * geometric assistant with a smart-glasses visor housing glowing eyes and a
 * support headset (the "coach on your side" signal), in the brand palette.
 * NOT a realistic illustrated face. Same expression-state API as before so
 * every consumer keeps working.
 *
 * States:
 *  - idle: gentle breathing + occasional blink
 *  - greeting: brighter smile + eye glow
 *  - thinking: eyes up, thinking dots
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
  bodyHi: "#1E7E77",
  body: "#0E5852",
  bodyDeep: "#0A403C",
  face: "#F4E9DC",
  faceShade: "#E4D3C0",
  visor: "#0A3A37",
  visorEdge: "#1C6D66",
  eye: "#0B2E2C",
  eyeGlow: "#5FE0D2",
  accent: "#F2B44C",
  accentDeep: "#D89327",
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
          <radialGradient id="ra-face" cx="0.42" cy="0.34" r="0.8">
            <stop offset="0" stopColor="#FBF3E9" />
            <stop offset="0.7" stopColor={C.face} />
            <stop offset="1" stopColor={C.faceShade} />
          </radialGradient>
          <linearGradient id="ra-body" x1="0" y1="0" x2="0.5" y2="1">
            <stop offset="0" stopColor={C.bodyHi} />
            <stop offset="1" stopColor={C.bodyDeep} />
          </linearGradient>
          <linearGradient id="ra-visor" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={C.visorEdge} />
            <stop offset="1" stopColor={C.visor} />
          </linearGradient>
          <radialGradient id="ra-eyeglow" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0" stopColor={C.eyeGlow} stopOpacity="0.9" />
            <stop offset="1" stopColor={C.eyeGlow} stopOpacity="0" />
          </radialGradient>
          <radialGradient id="ra-light" cx="0.38" cy="0.32" r="0.5">
            <stop offset="0" stopColor="#fff" stopOpacity="0.2" />
            <stop offset="1" stopColor="#fff" stopOpacity="0" />
          </radialGradient>
          <clipPath id="ra-clip"><circle cx="60" cy="60" r="60" /></clipPath>
        </defs>

        <g clipPath="url(#ra-clip)">
          <rect width="120" height="120" fill="url(#ra-bg)" />
          <rect width="120" height="120" fill="url(#ra-light)" />

          {/* Shoulders / rounded torso */}
          <path d="M16 120 Q20 92 60 86 Q100 92 104 120 Z" fill="url(#ra-body)" />
          {/* lanyard badge accent */}
          <path d="M52 90 L50 104" stroke={C.accent} strokeWidth="2.2" strokeLinecap="round" />
          <path d="M68 90 L70 104" stroke={C.accent} strokeWidth="2.2" strokeLinecap="round" />

          {/* Neck */}
          <path d="M53 78 h14 v9 q-7 4 -14 0 Z" fill={C.faceShade} />

          {/* Head */}
          <rect x="34" y="24" width="52" height="60" rx="24" fill="url(#ra-face)" />
          {/* cheeks */}
          <ellipse cx="46" cy="60" rx="6" ry="4" fill={C.accent} opacity="0.14" />
          <ellipse cx="74" cy="60" rx="6" ry="4" fill={C.accent} opacity="0.14" />

          {/* Hair cap */}
          <path d="M34 46 Q34 22 60 21 Q86 22 86 46 Q86 38 79 33 Q72 24 60 24 Q48 24 41 33 Q34 38 34 46 Z" fill="url(#ra-body)" />
          <path d="M40 38 Q49 28 60 28 Q54 31 47 33 Q41 35 40 41 Z" fill={C.bodyHi} opacity="0.5" />

          {/* Visor band housing the eyes */}
          <rect x="39" y="45" width="42" height="18" rx="9" fill="url(#ra-visor)" stroke={C.visorEdge} strokeWidth="1" />
          <path d="M43 49 Q54 46 66 48" stroke="#fff" strokeOpacity="0.18" strokeWidth="1.4" fill="none" strokeLinecap="round" />

          {/* Eyes — glowing + blinking */}
          <motion.g
            style={{ transformOrigin: "60px 54px" }}
            animate={reduced ? undefined : { scaleY: [1, 1, 0.08, 1, 1] }}
            transition={{ duration: 5.5, repeat: Infinity, times: [0, 0.63, 0.665, 0.7, 1] }}
          >
            <g transform={thinking ? "translate(1.5,-1.5)" : "translate(0,0)"}>
              {/* left */}
              <circle cx="51" cy="54" r="6" fill="url(#ra-eyeglow)" />
              <circle cx="51" cy="54" r="3.6" fill={C.eye} />
              <circle cx="51" cy="54" r="2.3" fill={C.eyeGlow} />
              <circle cx="51.8" cy="52.9" r="0.9" fill="#fff" />
              {/* right */}
              <circle cx="69" cy="54" r="6" fill="url(#ra-eyeglow)" />
              <circle cx="69" cy="54" r="3.6" fill={C.eye} />
              <circle cx="69" cy="54" r="2.3" fill={C.eyeGlow} />
              <circle cx="69.8" cy="52.9" r="0.9" fill="#fff" />
            </g>
          </motion.g>

          {/* Mouth */}
          {talking && !reduced ? (
            <motion.path
              d="M53 71 Q60 76 67 71"
              stroke={C.accentDeep} strokeWidth="2.4" fill="none" strokeLinecap="round"
              animate={{ d: ["M53 71 Q60 74 67 71", "M53 71 Q60 78 67 71", "M53 71 Q60 74 67 71"] }}
              transition={{ duration: 0.6, repeat: Infinity }}
            />
          ) : greeting ? (
            <path d="M52 70 Q60 78 68 70" stroke={C.accentDeep} strokeWidth="2.6" fill="none" strokeLinecap="round" />
          ) : (
            <path d="M53 71 Q60 75 67 71" stroke={C.accentDeep} strokeWidth="2.4" fill="none" strokeLinecap="round" />
          )}

          {/* Support headset */}
          <path d="M39 49 Q39 22 60 21 Q81 22 81 49" stroke={C.bodyDeep} strokeWidth="3" fill="none" strokeLinecap="round" opacity="0.9" />
          <rect x="31" y="50" width="8" height="14" rx="4" fill={C.bodyDeep} />
          <rect x="81" y="50" width="8" height="14" rx="4" fill={C.bodyDeep} />
          {/* mic boom + live light */}
          <path d="M39 60 Q29 65 32 76 Q34 82 44 82" stroke={C.bodyDeep} strokeWidth="2.4" fill="none" strokeLinecap="round" />
          <motion.circle
            cx="45" cy="82" r="2.4" fill={C.accent}
            animate={reduced ? undefined : { opacity: [1, 0.35, 1] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
          />
        </g>

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
