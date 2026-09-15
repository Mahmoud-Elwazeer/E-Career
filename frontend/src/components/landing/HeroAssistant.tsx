import { motion, useReducedMotion } from "framer-motion";
import { Sparkles, Search, FileText, Mic } from "lucide-react";
import { useTheme } from "@/hooks/use-theme";

/**
 * HeroAssistant — clean, professional AI career-coach persona for the landing hero.
 *
 * Replaces the previous CareerGuide (scattered limbs / misplaced eyes). This is a
 * deliberately framed composition: a polished bust illustration inside a glass
 * card with a soft glow, an identity label, and a few intentionally-placed
 * capability chips. Brand palette only (teal), bilingual, reduced-motion safe.
 */

interface HeroAssistantProps {
  className?: string;
}

/* Brand-aligned persona palette (teal suit, warm skin, dark hair) */
const C = {
  skin: "#E7C6A5",
  skinShade: "#D8B08C",
  hair: "#26201B",
  suit: "#0A3836",
  suitLight: "#12514D",
  shirt: "#EAF3F1",
  tie: "#1D6B66",
  brow: "#26201B",
  eye: "#2A2320",
  mouth: "#B56B63",
};

export function HeroAssistant({ className = "" }: HeroAssistantProps) {
  const reduced = useReducedMotion();
  const { lang } = useTheme();
  const isAr = lang === "ar";

  const float = (delay: number) =>
    reduced
      ? {}
      : {
          animate: { y: [0, -8, 0] },
          transition: { duration: 5, repeat: Infinity, ease: "easeInOut", delay },
        };

  const chips = [
    { icon: Search, en: "Smart search", ar: "بحث ذكي", pos: "top-2 -start-6" },
    { icon: FileText, en: "CV review", ar: "مراجعة السيرة", pos: "top-1/3 -end-8" },
    { icon: Mic, en: "Interview prep", ar: "تحضير المقابلة", pos: "bottom-10 -start-4" },
  ];

  return (
    <div className={`relative w-full max-w-[420px] mx-auto ${className}`} aria-hidden="true">
      {/* Ambient glow */}
      <div
        className="absolute inset-0 -z-10 rounded-[2rem]"
        style={{ background: "radial-gradient(circle at 50% 35%, hsl(var(--secondary) / 0.25), transparent 70%)" }}
      />

      {/* Glass frame */}
      <motion.div
        className="glass-panel relative rounded-[2rem] p-6 pt-8"
        initial={reduced ? {} : { opacity: 0, scale: 0.94, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 70, damping: 18, delay: 0.3 }}
      >
        {/* Identity badge */}
        <div className="absolute -top-4 left-1/2 -translate-x-1/2 inline-flex items-center gap-1.5 rounded-full bg-secondary px-3.5 py-1.5 text-caption font-semibold text-[hsl(var(--primary))] shadow-md whitespace-nowrap">
          <Sparkles className="h-3.5 w-3.5" />
          {isAr ? "رشيد · مساعدك المهني" : "Rasheed · AI Career Coach"}
        </div>

        {/* Persona illustration */}
        <div className="mx-auto w-full max-w-[260px] aspect-square">
          <motion.svg
            viewBox="0 0 240 240"
            width="100%"
            height="100%"
            initial={reduced ? undefined : "rest"}
            animate={reduced ? undefined : "breathe"}
            variants={{ rest: { scale: 1 }, breathe: { scale: [1, 1.012, 1] } }}
            transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
          >
            <defs>
              <linearGradient id="ha-suit" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor={C.suitLight} />
                <stop offset="1" stopColor={C.suit} />
              </linearGradient>
              <radialGradient id="ha-ground" cx="0.5" cy="0.5" r="0.5">
                <stop offset="0" stopColor="#000" stopOpacity="0.14" />
                <stop offset="1" stopColor="#000" stopOpacity="0" />
              </radialGradient>
            </defs>

            {/* Ground shadow */}
            <ellipse cx="120" cy="224" rx="70" ry="10" fill="url(#ha-ground)" />

            {/* Shoulders / suit jacket */}
            <path d="M56 240 Q60 168 120 158 Q180 168 184 240 Z" fill="url(#ha-suit)" />
            {/* Shirt V */}
            <path d="M104 168 L120 196 L136 168 L136 240 L104 240 Z" fill={C.shirt} />
            {/* Tie */}
            <path d="M120 196 L112 206 L120 236 L128 206 Z" fill={C.tie} />
            {/* Lapels */}
            <path d="M104 168 L120 196 L108 200 L92 178 Z" fill={C.suit} opacity="0.9" />
            <path d="M136 168 L120 196 L132 200 L148 178 Z" fill={C.suit} opacity="0.9" />

            {/* Neck */}
            <rect x="108" y="140" width="24" height="30" rx="10" fill={C.skinShade} />

            {/* Head */}
            <ellipse cx="120" cy="104" rx="42" ry="46" fill={C.skin} />
            {/* Ears */}
            <ellipse cx="79" cy="106" rx="7" ry="11" fill={C.skin} />
            <ellipse cx="161" cy="106" rx="7" ry="11" fill={C.skinShade} />
            {/* Hair */}
            <path d="M78 94 Q80 50 120 48 Q160 50 162 94 Q150 74 120 72 Q90 74 78 94 Z" fill={C.hair} />
            <path d="M78 94 Q76 78 84 66 L88 88 Z" fill={C.hair} />

            {/* Eyebrows */}
            <path d="M96 96 Q104 91 112 95" stroke={C.brow} strokeWidth="3" fill="none" strokeLinecap="round" />
            <path d="M128 95 Q136 91 144 96" stroke={C.brow} strokeWidth="3" fill="none" strokeLinecap="round" />

            {/* Eyes */}
            <motion.g
              variants={reduced ? undefined : { breathe: { scaleY: [1, 1, 0.1, 1, 1] } }}
              transition={{ duration: 4.5, repeat: Infinity, times: [0, 0.46, 0.5, 0.54, 1] }}
              style={{ transformOrigin: "120px 106px" }}
            >
              <ellipse cx="104" cy="106" rx="4.5" ry="5" fill={C.eye} />
              <ellipse cx="136" cy="106" rx="4.5" ry="5" fill={C.eye} />
              <circle cx="105.5" cy="104.5" r="1.4" fill="#fff" opacity="0.8" />
              <circle cx="137.5" cy="104.5" r="1.4" fill="#fff" opacity="0.8" />
            </motion.g>

            {/* Nose */}
            <path d="M120 108 Q121 118 115 121" stroke={C.skinShade} strokeWidth="2.5" fill="none" strokeLinecap="round" />
            {/* Smile */}
            <path d="M106 128 Q120 138 134 128" stroke={C.mouth} strokeWidth="3" fill="none" strokeLinecap="round" />
          </motion.svg>
        </div>

        {/* Caption */}
        <p className="text-center text-caption text-primary-foreground/80 mt-1">
          {isAr ? "متاح 24/7 لإرشادك المهني" : "Here 24/7 to guide your career"}
        </p>
      </motion.div>

      {/* Deliberately-placed capability chips */}
      {chips.map((chip, i) => (
        <motion.div
          key={chip.en}
          className={`absolute ${chip.pos} inline-flex items-center gap-1.5 rounded-full bg-card/95 border border-border/60 px-3 py-1.5 text-caption font-medium text-foreground shadow-lg backdrop-blur-sm`}
          initial={reduced ? {} : { opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.6 + i * 0.15, type: "spring", stiffness: 200, damping: 16 }}
          {...float(i * 0.6)}
        >
          <chip.icon className="h-3.5 w-3.5 text-primary" />
          {isAr ? chip.ar : chip.en}
        </motion.div>
      ))}
    </div>
  );
}
