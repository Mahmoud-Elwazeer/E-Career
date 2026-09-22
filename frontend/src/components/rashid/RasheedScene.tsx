import { useState, useEffect } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Search, Sparkles, FileText, CheckCircle2 } from "lucide-react";
import { useTheme } from "@/hooks/use-theme";

/**
 * RasheedScene — an interactive, animated half-body Rasheed who HOLDS a live
 * device panel. Arms, head, eyes and the in-hand screen all move; the screen
 * cycles through real product moments (search → match → CV → interview) with
 * cards that swipe/update. Hand-authored SVG + framer-motion (Path B).
 *
 * Designed asset-agnostic: if a rigged Rive/Lottie Rasheed is provided later,
 * swap the <figure> internals without changing the consuming layout.
 */

const C = {
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
  iris: "#3B2C21",
  mouth: "#A85C54",
  device: "#0A2F2C",
  deviceEdge: "#16403C",
};

type Screen = {
  key: string;
  icon: React.ComponentType<{ className?: string }>;
  en: string;
  ar: string;
  metaEn: string;
  metaAr: string;
};

const SCREENS: Screen[] = [
  { key: "search", icon: Search, en: "Frontend Engineer", ar: "مهندس واجهات", metaEn: "128 new roles", metaAr: "١٢٨ وظيفة جديدة" },
  { key: "match", icon: Sparkles, en: "Match 94%", ar: "توافق ٩٤٪", metaEn: "React · TypeScript", metaAr: "React · TypeScript" },
  { key: "cv", icon: FileText, en: "CV reviewed", ar: "تمت مراجعة السيرة", metaEn: "+12 improvements", metaAr: "+١٢ تحسيناً" },
  { key: "done", icon: CheckCircle2, en: "Application sent", ar: "تم إرسال الطلب", metaEn: "Direct to employer", metaAr: "مباشرة لصاحب العمل" },
];

export function RasheedScene({ className = "" }: { className?: string }) {
  const reduced = useReducedMotion();
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const [i, setI] = useState(0);
  const [gaze, setGaze] = useState({ x: 0, y: 0 });

  // Cycle the in-hand screen content.
  useEffect(() => {
    if (reduced) return;
    const t = setInterval(() => setI((v) => (v + 1) % SCREENS.length), 2600);
    return () => clearInterval(t);
  }, [reduced]);

  // Subtle life: occasional micro eye-saccades (small random gaze shifts).
  useEffect(() => {
    if (reduced) return;
    const t = setInterval(() => {
      setGaze({ x: (Math.random() - 0.5) * 2.4, y: (Math.random() - 0.5) * 1.6 });
      // settle back toward center shortly after
      setTimeout(() => setGaze({ x: 0, y: 0 }), 900);
    }, 3400);
    return () => clearInterval(t);
  }, [reduced]);

  const screen = SCREENS[i];
  // Rasheed "presents" (gesture arm rises) briefly whenever the screen changes.
  const presenting = i % 2 === 1;

  return (
    <figure className={`relative mx-auto w-full max-w-[440px] ${className}`} aria-label="Rasheed presenting the platform">
      {/* Ambient glow */}
      <div
        className="absolute inset-0 -z-10 rounded-[2.5rem]"
        style={{ background: "radial-gradient(circle at 55% 40%, hsl(var(--secondary) / 0.25), transparent 70%)" }}
        aria-hidden
      />

      <motion.svg
        viewBox="0 0 400 400"
        width="100%"
        height="100%"
        initial={false}
        animate={reduced ? undefined : { y: [0, -4, 0] }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
        role="img"
      >
        <defs>
          <linearGradient id="rs-suit" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor={C.suitHi} />
            <stop offset="1" stopColor={C.suit} />
          </linearGradient>
          <linearGradient id="rs-skin" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={C.skinLight} />
            <stop offset="1" stopColor={C.skinShade} />
          </linearGradient>
          <radialGradient id="rs-ground" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0" stopColor="#000" stopOpacity="0.16" />
            <stop offset="1" stopColor="#000" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Ground shadow */}
        <ellipse cx="200" cy="388" rx="120" ry="14" fill="url(#rs-ground)" />

        {/* ── Torso / suit ── */}
        <motion.g
          animate={reduced ? undefined : { rotate: presenting ? -1.5 : 0 }}
          transition={{ type: "spring", stiffness: 60, damping: 14 }}
          style={{ transformOrigin: "200px 240px" }}
        >
          <path d="M96 400 Q104 300 200 286 Q296 300 304 400 Z" fill="url(#rs-suit)" />
          {/* Shirt + tie */}
          <path d="M172 296 L200 340 L228 296 L228 400 L172 400 Z" fill={C.shirt} />
          <path d="M200 340 L190 352 L200 396 L210 352 Z" fill={C.tie} />
          <path d="M172 296 L200 340 L184 344 L156 312 Z" fill={C.suit} />
          <path d="M228 296 L200 340 L216 344 L244 312 Z" fill={C.suit} />

          {/* ── Left arm (static, resting) ── */}
          <path d="M110 320 Q92 356 104 392" stroke="url(#rs-suit)" strokeWidth="26" strokeLinecap="round" fill="none" />

          {/* ── Right arm — holds the device, rises when presenting ── */}
          <motion.g
            animate={reduced ? undefined : { rotate: presenting ? -14 : -4 }}
            transition={{ type: "spring", stiffness: 70, damping: 12 }}
            style={{ transformOrigin: "286px 316px" }}
          >
            <path d="M286 316 Q320 340 300 372" stroke="url(#rs-suit)" strokeWidth="26" strokeLinecap="round" fill="none" />
            {/* Hand */}
            <ellipse cx="298" cy="372" rx="15" ry="12" fill="url(#rs-skin)" />
          </motion.g>
        </motion.g>

        {/* Neck + head */}
        <path d="M182 250 h36 v26 q-18 12 -36 0 Z" fill={C.skinShade} />
        <motion.g
          animate={reduced ? undefined : { rotate: presenting ? 2 : 0, y: [0, -1.5, 0] }}
          transition={{ rotate: { type: "spring", stiffness: 60, damping: 14 }, y: { duration: 5, repeat: Infinity, ease: "easeInOut" } }}
          style={{ transformOrigin: "200px 200px" }}
        >
          {/* Head — tapered jaw for a mature, defined face (matches RasheedAvatar) */}
          <path d="M150 188 Q150 134 200 132 Q250 134 250 188 Q250 226 228 246 Q214 258 200 258 Q186 258 172 246 Q150 226 150 188 Z" fill="url(#rs-skin)" />
          {/* Ears */}
          <ellipse cx="150" cy="196" rx="8" ry="13" fill={C.skinShade} />
          <ellipse cx="250" cy="196" rx="8" ry="13" fill={C.skinShade} />

          {/* Groomed beard along the jaw */}
          <path d="M158 202 Q158 244 200 258 Q242 244 242 202 Q242 228 228 242 Q214 253 200 253 Q186 253 172 242 Q158 228 158 202 Z" fill={C.hair} />
          <path d="M166 198 Q182 220 200 222 Q218 220 234 198 Q220 208 200 208 Q180 208 166 198 Z" fill="url(#rs-skin)" />

          {/* Hair — modern short crop, defined hairline */}
          <path d="M149 188 Q147 133 200 130 Q253 133 251 188 Q251 176 240 166 Q231 148 200 147 Q169 148 160 166 Q149 176 149 188 Z" fill={C.hair} />
          <path d="M156 172 Q174 154 200 154 Q190 160 176 164 Q162 168 156 178 Z" fill={C.hairHi} opacity="0.55" />

          {/* Eyebrows (raise when presenting) */}
          <motion.g animate={reduced ? undefined : { y: presenting ? -2.5 : 0 }} transition={{ duration: 0.4 }}>
            <path d="M168 182 Q180 176 192 181" stroke={C.brow} strokeWidth="3.4" fill="none" strokeLinecap="round" />
            <path d="M208 181 Q220 176 232 182" stroke={C.brow} strokeWidth="3.4" fill="none" strokeLinecap="round" />
          </motion.g>

          {/* Eyes — almond shaped with lids (not round cartoon dots) */}
          <motion.g
            style={{ transformOrigin: "200px 196px" }}
            animate={reduced ? undefined : { scaleY: [1, 1, 0.08, 1, 1] }}
            transition={{ duration: 5, repeat: Infinity, times: [0, 0.6, 0.64, 0.68, 1] }}
          >
            <motion.g
              animate={reduced ? undefined : { x: (presenting ? 2.4 : 0) + gaze.x, y: (presenting ? 1 : 0) + gaze.y }}
              transition={{ type: "spring", stiffness: 120, damping: 16 }}
            >
              {/* left */}
              <path d="M170 196 Q182 189 194 196 Q182 202 170 196 Z" fill="#FCFAF6" />
              <circle cx="182" cy="196" r="4.4" fill={C.iris} />
              <circle cx="183.6" cy="194.2" r="1.5" fill="#fff" />
              <path d="M170 196 Q182 189 194 196" stroke={C.skinShade} strokeWidth="1.4" fill="none" opacity="0.7" />
              {/* right */}
              <path d="M206 196 Q218 189 230 196 Q218 202 206 196 Z" fill="#FCFAF6" />
              <circle cx="218" cy="196" r="4.4" fill={C.iris} />
              <circle cx="219.6" cy="194.2" r="1.5" fill="#fff" />
              <path d="M206 196 Q218 189 230 196" stroke={C.skinShade} strokeWidth="1.4" fill="none" opacity="0.7" />
            </motion.g>
          </motion.g>

          {/* Nose */}
          <path d="M200 200 L198 214 Q200 217 204 215" stroke={C.skinShade} strokeWidth="2.2" fill="none" strokeLinecap="round" />

          {/* Smile (sits within the beard) */}
          <path d="M184 226 Q200 236 216 226" stroke={C.mouth} strokeWidth="3.2" fill="none" strokeLinecap="round" />
        </motion.g>

        {/* ── The interactive device in hand ── */}
        <motion.g
          animate={reduced ? undefined : { rotate: presenting ? -8 : -3, y: presenting ? -6 : 0 }}
          transition={{ type: "spring", stiffness: 70, damping: 12 }}
          style={{ transformOrigin: "300px 300px" }}
        >
          {/* Phone body */}
          <rect x="262" y="230" width="92" height="150" rx="16" fill={C.device} stroke={C.deviceEdge} strokeWidth="2" />
          {/* Screen well is filled by the HTML overlay below via foreignObject */}
          <rect x="270" y="240" width="76" height="130" rx="9" fill="#06201E" />
        </motion.g>
      </motion.svg>

      {/* Live screen content overlaid on the phone (HTML for crisp text/icons) */}
      <div
        className="pointer-events-none absolute"
        style={{ left: "67.5%", top: "60%", width: "19%", transform: "translateY(-50%) rotate(-3deg)" }}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={screen.key}
            initial={reduced ? { opacity: 0 } : { opacity: 0, x: 14 }}
            animate={{ opacity: 1, x: 0 }}
            exit={reduced ? { opacity: 0 } : { opacity: 0, x: -14 }}
            transition={{ duration: 0.35 }}
            className="rounded-md bg-card/95 p-1.5 shadow-sm"
          >
            <div className="flex items-center gap-1">
              <span className="flex h-4 w-4 items-center justify-center rounded bg-primary/15">
                <screen.icon className="h-2.5 w-2.5 text-primary" />
              </span>
              <span className="text-[6px] font-semibold text-foreground leading-tight truncate">
                {isAr ? screen.ar : screen.en}
              </span>
            </div>
            <p className="mt-0.5 text-[5px] text-muted-foreground truncate">{isAr ? screen.metaAr : screen.metaEn}</p>
            <div className="mt-1 h-0.5 w-full rounded-full bg-primary/15">
              <motion.div
                key={screen.key + "-bar"}
                className="h-full rounded-full bg-primary"
                initial={{ width: "10%" }}
                animate={{ width: "80%" }}
                transition={{ duration: 2.2, ease: "easeOut" }}
              />
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Floating status chip — a single, clean, well-anchored card that swaps
          with the in-hand screen. Redesigned (was a cramped low-contrast pill)
          into a crisp paper chip with a live signal dot, matching the new
          editorial system. Positioned bottom-start so it never crowds the
          device or the hero identity badge. */}
      <AnimatePresence mode="wait">
        <motion.div
          key={screen.key + "-pill"}
          initial={reduced ? { opacity: 0 } : { opacity: 0, y: 10, scale: 0.94 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, scale: 0.94 }}
          transition={{ type: "spring", stiffness: 240, damping: 20 }}
          className="absolute bottom-6 start-0 inline-flex items-center gap-2 rounded-2xl border border-border bg-card/95 px-3.5 py-2 shadow-lg backdrop-blur-sm"
        >
          <span className="signal-dot" />
          <span className="flex flex-col leading-tight">
            <span className="text-caption font-semibold text-foreground">{isAr ? screen.ar : screen.en}</span>
            <span className="text-[10px] text-muted-foreground">{isAr ? screen.metaAr : screen.metaEn}</span>
          </span>
        </motion.div>
      </AnimatePresence>
    </figure>
  );
}
