import { useRef } from "react";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";
import { CheckCircle2 } from "lucide-react";
import { SmartSearch } from "@/components/landing/SmartSearch";
import { HeroAssistant } from "@/components/landing/HeroAssistant";
import { WatermarkBackground } from "@/components/WatermarkBackground";
import { useTheme } from "@/hooks/use-theme";
import type { LandingData } from "@/hooks/use-landing-data";

/**
 * HeroSection — a from-scratch, CENTERED landing opener (replaces the previous
 * side-by-side split). Structure, top → bottom:
 *   1. centered mono eyebrow with live signal
 *   2. centered editorial serif headline
 *   3. centered subtext
 *   4. centered search (the primary action, front-and-centre)
 *   5. trust row
 *   6. a WIDE product-proof panel below the fold-line: framed Rasheed console
 *      flanked by a live metric readout — the "show the product" moment.
 *
 * All data is real (LandingData). Search is delegated to the parent via props.
 */

interface HeroSectionProps {
  query: string;
  setQuery: (q: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  landing?: LandingData;
  industryCount: number;
}

export function HeroSection({ query, setQuery, onSubmit, landing, industryCount }: HeroSectionProps) {
  const reduced = useReducedMotion();
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const isTyping = query.length > 0;

  const heroRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
  const proofY = useTransform(scrollYProgress, [0, 1], [0, 60]);

  const metrics = [
    { v: landing?.totalJobs ?? 0, s: "+", l: isAr ? "وظيفة" : "jobs" },
    { v: landing?.sourcesCount ?? 0, s: "", l: isAr ? "مصادر" : "sources" },
    { v: industryCount, s: "", l: isAr ? "قطاعات" : "industries" },
    { v: 10, s: "+", l: isAr ? "دول" : "countries" },
  ];

  const trust = [
    isAr ? "تقديم مباشر للمصدر" : "Direct-to-source apply",
    isAr ? "بدون وسطاء" : "No middleman",
    isAr ? "تحديث مستمر" : "Continuously verified",
  ];

  return (
    <section ref={heroRef} className="chamber chamber-grid relative overflow-hidden text-primary-foreground">
      <WatermarkBackground variant="shimmer" opacity={0.04} inheritColor paused={isTyping} />
      {/* Ambient depth */}
      <div className="glow-blob" style={{ width: 560, height: 560, top: -180, insetInlineStart: "50%", transform: "translateX(-50%)", background: "hsl(var(--secondary) / 0.25)" }} aria-hidden />
      <div className="glow-blob" style={{ width: 420, height: 420, bottom: -160, insetInlineEnd: -80, background: "hsl(var(--primary-hover) / 0.5)" }} aria-hidden />

      <div className="container relative z-10 pt-20 md:pt-28 pb-16 md:pb-20">
        {/* ── Centered editorial opener ── */}
        <div className="mx-auto max-w-3xl text-center">
          <motion.span
            className="inline-flex items-center gap-2 rounded-full border border-primary-foreground/15 bg-primary-foreground/10 px-3.5 py-1.5 text-overline tracking-widest font-mono-data backdrop-blur-sm mb-7"
            initial={reduced ? {} : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.05 }}
          >
            <span className="signal-dot" />
            {isAr ? "منصة المسار المهني الذكية" : "THE AI CAREER OPERATING SYSTEM"}
          </motion.span>

          <motion.h1
            className="text-hero-serif"
            initial={reduced ? {} : { opacity: 0, y: 36 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 82, damping: 18, mass: 1.05, delay: 0.15 }}
          >
            {isAr ? (
              <>بحث واحد، <span className="serif-accent text-secondary">كل الفرص.</span></>
            ) : (
              <>One search, <span className="serif-accent text-secondary">every opportunity.</span></>
            )}
          </motion.h1>

          <motion.p
            className="mx-auto mt-6 max-w-xl text-body-lg opacity-80"
            initial={reduced ? {} : { opacity: 0, y: 18 }}
            animate={{ opacity: 0.8, y: 0 }}
            transition={{ duration: 0.5, delay: 0.35 }}
          >
            {isAr
              ? "وظائف موثقة مجمّعة من أفضل المصادر عبر الشرق الأوسط — مع رشيد، مساعدك المهني الذكي، من البحث حتى التوظيف والنمو."
              : "Verified jobs aggregated from top sources across MENA — plus Rasheed, your AI career coach, from search to hire to growth."}
          </motion.p>

          {/* Search — the primary action, centred */}
          <motion.div
            className="mx-auto mt-9 max-w-xl"
            initial={reduced ? {} : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <SmartSearch query={query} setQuery={setQuery} onSubmit={onSubmit} />
          </motion.div>

          {/* Trust row */}
          <motion.div
            className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-caption text-primary-foreground/70"
            initial={reduced ? {} : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.65 }}
          >
            {trust.map((t) => (
              <span key={t} className="inline-flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-secondary" />
                {t}
              </span>
            ))}
          </motion.div>
        </div>

        {/* ── Product-proof panel (below the opener) ── */}
        <motion.div
          className="relative mx-auto mt-16 max-w-4xl"
          style={reduced ? {} : { y: proofY }}
          initial={reduced ? {} : { opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.6, ease: [0, 0, 0.2, 1] }}
        >
          <div className="grid items-center gap-6 rounded-[2rem] border border-primary-foreground/12 bg-primary-foreground/[0.04] p-4 backdrop-blur-sm md:grid-cols-[1fr_0.85fr] md:p-6">
            {/* Live metric readout */}
            <div className="order-2 px-2 md:order-1 md:px-4">
              <p className="eyebrow-mono text-primary-foreground/60 mb-5">
                {isAr ? "المنصة الآن" : "PLATFORM · LIVE"}
              </p>
              <div className="grid grid-cols-2 gap-x-6 gap-y-6">
                {metrics.map((m) => (
                  <div key={m.l}>
                    <div className="font-mono-data text-3xl font-medium leading-none text-primary-foreground">
                      {m.v}
                      {m.s}
                    </div>
                    <div className="mt-1.5 text-[11px] uppercase tracking-widest text-primary-foreground/55">
                      {m.l}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Framed Rasheed console */}
            <div className="order-1 md:order-2">
              <HeroAssistant />
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
