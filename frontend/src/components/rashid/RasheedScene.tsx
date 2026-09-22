import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Search, Sparkles, FileText, CheckCircle2 } from "lucide-react";
import { useTheme } from "@/hooks/use-theme";

/**
 * RasheedScene — Rasheed, the platform's AI career coach, as a LIVE character.
 *
 * This is a deliberate, categorical redesign away from the earlier realistic-
 * illustration face (which read as generic/uncanny at hero scale). Rasheed is
 * now a confident, modern, geometric assistant with a support headset — a
 * clear "coach who's on your side" signal — rendered in the brand palette.
 *
 * He is genuinely alive:
 *  • eyes track a moving gaze target and blink on their own timer
 *  • head + body breathe and tilt toward the device when he "presents"
 *  • the raised hand lifts on each new tip (a real presenting gesture)
 *  • the phone he holds cycles real product moments with swiping cards
 *  • the headset mic-light and a status chip pulse to show he's active
 *
 * Hand-authored SVG + framer-motion. Asset-agnostic: if a rigged Rive/Lottie/
 * GLB Rasheed is provided later, swap the <figure> internals; the layout and
 * the consuming components stay the same.
 */

const C = {
  // Brand-forward character palette (teal identity + warm signal accent).
  bodyHi: "#1E7E77",
  body: "#0E5852",
  bodyDeep: "#0A403C",
  face: "#F4E9DC",
  faceShade: "#E4D3C0",
  visor: "#0A3A37",
  visorEdge: "#1C6D66",
  eye: "#0B2E2C",
  eyeGlow: "#5FE0D2",
  accent: "#F2B44C", // warm amber — headset light + accents
  accentDeep: "#D89327",
  hand: "#F4E9DC",
  device: "#0A2F2C",
  deviceEdge: "#1C6D66",
  screen: "#06201E",
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
  const figureRef = useRef<HTMLElement>(null);

  // Cycle the in-hand screen content.
  useEffect(() => {
    if (reduced) return;
    const t = setInterval(() => setI((v) => (v + 1) % SCREENS.length), 2600);
    return () => clearInterval(t);
  }, [reduced]);

  // Eyes follow the pointer when it's over the hero; drift gently otherwise.
  useEffect(() => {
    if (reduced) return;
    const el = figureRef.current;
    if (!el) return;
    const onMove = (e: PointerEvent) => {
      const r = el.getBoundingClientRect();
      const cx = r.left + r.width * 0.5;
      const cy = r.top + r.height * 0.42;
      const dx = (e.clientX - cx) / (r.width * 0.5);
      const dy = (e.clientY - cy) / (r.height * 0.5);
      setGaze({
        x: Math.max(-1, Math.min(1, dx)) * 3.2,
        y: Math.max(-1, Math.min(1, dy)) * 2.2,
      });
    };
    window.addEventListener("pointermove", onMove);
    return () => window.removeEventListener("pointermove", onMove);
  }, [reduced]);

  // Idle micro-saccades when the pointer isn't driving the gaze.
  useEffect(() => {
    if (reduced) return;
    const t = setInterval(() => {
      setGaze((g) =>
        Math.abs(g.x) < 0.4 && Math.abs(g.y) < 0.4
          ? { x: (Math.random() - 0.5) * 3, y: (Math.random() - 0.5) * 2 }
          : g,
      );
    }, 3600);
    return () => clearInterval(t);
  }, [reduced]);

  const screen = SCREENS[i];
  // Rasheed "presents" (hand rises, head tilts to device) on odd tips.
  const presenting = i % 2 === 1;

  return (
    <figure
      ref={figureRef}
      className={`relative mx-auto w-full max-w-[440px] ${className}`}
      aria-label="Rasheed, your AI career coach, presenting the platform"
    >
      {/* Ambient glow */}
      <div
        className="absolute inset-0 -z-10 rounded-[2.5rem]"
        style={{ background: "radial-gradient(circle at 52% 38%, hsl(var(--secondary) / 0.28), transparent 70%)" }}
        aria-hidden
      />

      <motion.svg
        viewBox="0 0 400 400"
        width="100%"
        height="100%"
        initial={false}
        animate={reduced ? undefined : { y: [0, -5, 0] }}
        transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
        role="img"
      >
        <defs>
          <linearGradient id="rs-body" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor={C.bodyHi} />
            <stop offset="1" stopColor={C.bodyDeep} />
          </linearGradient>
          <radialGradient id="rs-face" cx="0.42" cy="0.34" r="0.75">
            <stop offset="0" stopColor="#FBF3E9" />
            <stop offset="0.7" stopColor={C.face} />
            <stop offset="1" stopColor={C.faceShade} />
          </radialGradient>
          <linearGradient id="rs-visor" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={C.visorEdge} />
            <stop offset="1" stopColor={C.visor} />
          </linearGradient>
          <radialGradient id="rs-ground" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0" stopColor="#000" stopOpacity="0.16" />
            <stop offset="1" stopColor="#000" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="rs-eyeglow" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0" stopColor={C.eyeGlow} stopOpacity="0.9" />
            <stop offset="1" stopColor={C.eyeGlow} stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Ground shadow */}
        <ellipse cx="200" cy="388" rx="118" ry="14" fill="url(#rs-ground)" />

        {/* ── Torso ── */}
        <motion.g
          animate={reduced ? undefined : { rotate: presenting ? -1.5 : 0 }}
          transition={{ type: "spring", stiffness: 60, damping: 14 }}
          style={{ transformOrigin: "200px 250px" }}
        >
          {/* Rounded, friendly shoulders/torso */}
          <path d="M104 400 Q108 300 200 288 Q292 300 296 400 Z" fill="url(#rs-body)" />
          {/* Subtle chest zip + collar seam */}
          <path d="M200 300 V392" stroke={C.bodyDeep} strokeWidth="3" opacity="0.5" strokeLinecap="round" />
          <path d="M168 306 Q200 296 232 306" stroke={C.bodyHi} strokeWidth="3" fill="none" opacity="0.55" strokeLinecap="round" />
          {/* Lanyard/badge — a coach credential, brand touch */}
          <path d="M186 300 L182 348" stroke={C.accent} strokeWidth="4" strokeLinecap="round" />
          <path d="M214 300 L218 348" stroke={C.accent} strokeWidth="4" strokeLinecap="round" />
          <rect x="180" y="346" width="40" height="28" rx="6" fill={C.face} />
          <rect x="186" y="352" width="28" height="4" rx="2" fill={C.body} opacity="0.7" />
          <rect x="186" y="360" width="20" height="4" rx="2" fill={C.body} opacity="0.4" />

          {/* Left arm — resting */}
          <path d="M118 322 Q98 356 110 392" stroke="url(#rs-body)" strokeWidth="30" strokeLinecap="round" fill="none" />

          {/* Right arm — holds device, lifts when presenting */}
          <motion.g
            animate={reduced ? undefined : { rotate: presenting ? -16 : -5 }}
            transition={{ type: "spring", stiffness: 70, damping: 12 }}
            style={{ transformOrigin: "284px 318px" }}
          >
            <path d="M284 318 Q322 340 302 372" stroke="url(#rs-body)" strokeWidth="30" strokeLinecap="round" fill="none" />
            <ellipse cx="300" cy="372" rx="16" ry="13" fill={C.hand} />
          </motion.g>
        </motion.g>

        {/* Neck */}
        <path d="M184 250 h32 v24 q-16 11 -32 0 Z" fill={C.faceShade} />

        {/* ── Head ── */}
        <motion.g
          animate={reduced ? undefined : { rotate: presenting ? 3 : 0, y: [0, -1.5, 0] }}
          transition={{
            rotate: { type: "spring", stiffness: 60, damping: 14 },
            y: { duration: 5, repeat: Infinity, ease: "easeInOut" },
          }}
          style={{ transformOrigin: "200px 190px" }}
        >
          {/* Rounded head */}
          <rect x="140" y="118" width="120" height="132" rx="52" fill="url(#rs-face)" />
          {/* soft cheek shading */}
          <ellipse cx="168" cy="196" rx="14" ry="10" fill={C.accent} opacity="0.14" />
          <ellipse cx="232" cy="196" rx="14" ry="10" fill={C.accent} opacity="0.14" />

          {/* Hair cap — clean modern top, brand teal */}
          <path d="M140 168 Q140 112 200 110 Q260 112 260 168 Q260 150 246 140 Q232 122 200 122 Q168 122 154 140 Q140 150 140 168 Z" fill="url(#rs-body)" />
          <path d="M152 150 Q172 130 200 130 Q188 137 172 141 Q158 145 152 156 Z" fill={C.bodyHi} opacity="0.5" />

          {/* Visor / smart glasses band — the "AI" signal, houses the eyes */}
          <rect x="150" y="168" width="100" height="42" rx="21" fill="url(#rs-visor)" />
          <rect x="150" y="168" width="100" height="42" rx="21" fill="none" stroke={C.visorEdge} strokeWidth="2" />
          {/* visor sheen */}
          <path d="M158 176 Q186 170 214 174" stroke="#fff" strokeOpacity="0.18" strokeWidth="3" fill="none" strokeLinecap="round" />

          {/* Eyes — glowing, tracking, blinking */}
          <motion.g
            style={{ transformOrigin: "200px 189px" }}
            animate={reduced ? undefined : { scaleY: [1, 1, 0.08, 1, 1] }}
            transition={{ duration: 4.6, repeat: Infinity, times: [0, 0.62, 0.66, 0.7, 1] }}
          >
            <motion.g
              animate={reduced ? undefined : { x: (presenting ? 2 : 0) + gaze.x, y: (presenting ? 1 : 0) + gaze.y }}
              transition={{ type: "spring", stiffness: 120, damping: 16 }}
            >
              {/* left */}
              <circle cx="178" cy="189" r="12" fill="url(#rs-eyeglow)" />
              <circle cx="178" cy="189" r="7" fill={C.eye} />
              <circle cx="178" cy="189" r="4.6" fill={C.eyeGlow} />
              <circle cx="179.6" cy="187" r="1.8" fill="#fff" />
              {/* right */}
              <circle cx="222" cy="189" r="12" fill="url(#rs-eyeglow)" />
              <circle cx="222" cy="189" r="7" fill={C.eye} />
              <circle cx="222" cy="189" r="4.6" fill={C.eyeGlow} />
              <circle cx="223.6" cy="187" r="1.8" fill="#fff" />
            </motion.g>
          </motion.g>

          {/* Friendly smile */}
          <motion.path
            d="M182 228 Q200 240 218 228"
            stroke={C.accentDeep}
            strokeWidth="4"
            fill="none"
            strokeLinecap="round"
            animate={reduced ? undefined : { d: presenting ? "M180 226 Q200 244 220 226" : "M182 229 Q200 239 218 229" }}
            transition={{ type: "spring", stiffness: 80, damping: 14 }}
          />

          {/* ── Support headset — coach signal ── */}
          {/* headband */}
          <path d="M150 172 Q150 120 200 118 Q250 120 250 172" stroke={C.bodyDeep} strokeWidth="7" fill="none" strokeLinecap="round" opacity="0.9" />
          {/* ear cups */}
          <rect x="134" y="176" width="18" height="30" rx="8" fill={C.bodyDeep} />
          <rect x="248" y="176" width="18" height="30" rx="8" fill={C.bodyDeep} />
          {/* mic boom + live light */}
          <path d="M150 200 Q126 210 132 236 Q136 252 158 252" stroke={C.bodyDeep} strokeWidth="5" fill="none" strokeLinecap="round" />
          <motion.circle
            cx="160" cy="252" r="5" fill={C.accent}
            animate={reduced ? undefined : { opacity: [1, 0.35, 1] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
          />
        </motion.g>

        {/* ── Device in hand ── */}
        <motion.g
          animate={reduced ? undefined : { rotate: presenting ? -9 : -3, y: presenting ? -6 : 0 }}
          transition={{ type: "spring", stiffness: 70, damping: 12 }}
          style={{ transformOrigin: "300px 300px" }}
        >
          <rect x="260" y="228" width="96" height="152" rx="18" fill={C.device} stroke={C.deviceEdge} strokeWidth="2" />
          <rect x="268" y="238" width="80" height="132" rx="10" fill={C.screen} />
          {/* speaker notch */}
          <rect x="298" y="234" width="20" height="3" rx="1.5" fill={C.deviceEdge} />
        </motion.g>
      </motion.svg>

      {/* Live screen content overlaid on the phone (HTML for crisp text/icons) */}
      <div
        className="pointer-events-none absolute"
        style={{ left: "68%", top: "60%", width: "19.5%", transform: "translateY(-50%) rotate(-3deg)" }}
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

      {/* Floating status chip — a clean, well-anchored card that swaps with the
          in-hand screen; shows Rasheed is live and what he's doing. */}
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
