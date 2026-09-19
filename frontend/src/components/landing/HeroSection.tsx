import { motion, useReducedMotion } from "framer-motion";
import { CheckCircle2, ArrowRight, ArrowLeft } from "lucide-react";
import { SmartSearch } from "@/components/landing/SmartSearch";
import { HeroAssistant } from "@/components/landing/HeroAssistant";
import { useTheme } from "@/hooks/use-theme";
import type { LandingData } from "@/hooks/use-landing-data";

/**
 * HeroSection — rebuilt from zero.
 *
 * Fixes the two problems in the previous version:
 *   1) NAVBAR OVERLAP — the header is sticky, so the hero opens on a LIGHT paper
 *      canvas with explicit top clearance (no giant headline hiding under the
 *      nav on first paint).
 *   2) ALL-DARK WALL — instead of a full teal block, the opener sits on the warm
 *      paper canvas (brand ink on paper), and the deep-teal "chamber" is used
 *      only for the product-proof panel below. This gives real light↔dark
 *      rhythm using the SAME brand colours (teal primary, warm paper, amber
 *      signal), per the design system (Increase/Subframe/Wispr direction).
 *
 * Layout: centered editorial opener → search (primary action) → trust row,
 * then a full-width teal chamber card holding live metrics + the Rasheed console.
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
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;

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
    <section className="relative overflow-hidden bg-background">
      {/* Soft warm-paper wash + faint teal aura (light, not a dark wall) */}
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden
        style={{
          background:
            "radial-gradient(60% 55% at 50% 0%, hsl(var(--primary) / 0.06) 0%, transparent 70%)",
        }}
      />
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-px"
        aria-hidden
        style={{ background: "linear-gradient(90deg, transparent, hsl(var(--border)), transparent)" }}
      />

      {/* pt clears the sticky navbar (h-16) with room to breathe */}
      <div className="container relative z-10 pt-16 md:pt-20 pb-16 md:pb-24">
        {/* ── Centered editorial opener on paper ── */}
        <div className="mx-auto max-w-3xl text-center">
          <motion.span
            className="eyebrow-mono justify-center mb-6"
            initial={reduced ? {} : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.05 }}
          >
            <span className="signal-dot" />
            {isAr ? "منصة المسار المهني الذكية" : "THE AI CAREER OPERATING SYSTEM"}
          </motion.span>

          <motion.h1
            className="text-hero-serif text-foreground"
            initial={reduced ? {} : { opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 82, damping: 18, mass: 1.05, delay: 0.12 }}
          >
            {isAr ? (
              <>بحث واحد، <span className="serif-accent text-primary">كل الفرص.</span></>
            ) : (
              <>One search, <span className="serif-accent text-primary">every opportunity.</span></>
            )}
          </motion.h1>

          <motion.p
            className="mx-auto mt-6 max-w-xl text-body-lg text-muted-foreground"
            initial={reduced ? {} : { opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            {isAr
              ? "وظائف موثقة مجمّعة من أفضل المصادر عبر الشرق الأوسط — مع رشيد، مساعدك المهني الذكي، من البحث حتى التوظيف والنمو."
              : "Verified jobs aggregated from top sources across MENA — plus Rasheed, your AI career coach, from search to hire to growth."}
          </motion.p>

          {/* Search — the primary action */}
          <motion.div
            className="mx-auto mt-8 max-w-xl"
            initial={reduced ? {} : { opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.42 }}
          >
            <SmartSearch query={query} setQuery={setQuery} onSubmit={onSubmit} />
          </motion.div>

          {/* Trust row */}
          <motion.div
            className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-caption text-muted-foreground"
            initial={reduced ? {} : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.55 }}
          >
            {trust.map((t) => (
              <span key={t} className="inline-flex items-center gap-1.5">
                <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
                {t}
              </span>
            ))}
          </motion.div>
        </div>

        {/* ── Product-proof panel: the single teal chamber (light→dark rhythm) ── */}
        <motion.div
          className="chamber chamber-grid relative mx-auto mt-14 max-w-5xl overflow-hidden rounded-[2rem] text-primary-foreground shadow-xl"
          initial={reduced ? {} : { opacity: 0, y: 32 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.6, ease: [0, 0, 0.2, 1] }}
        >
          <div className="grid items-center gap-8 p-6 md:grid-cols-[1fr_0.9fr] md:p-9">
            {/* Left: headline + live metrics + CTA */}
            <div className="order-2 md:order-1">
              <p className="eyebrow-mono text-primary-foreground/60 mb-4">
                <span className="signal-dot" /> {isAr ? "المنصة الآن" : "PLATFORM · LIVE"}
              </p>
              <h2 className="font-display text-2xl md:text-3xl font-semibold leading-tight mb-6">
                {isAr ? "كل ما تحتاجه لمسارك المهني في مكان واحد" : "Everything for your career, in one place"}
              </h2>
              <div className="grid grid-cols-2 gap-x-6 gap-y-6 mb-7">
                {metrics.map((m) => (
                  <div key={m.l}>
                    <div className="font-mono-data text-3xl font-medium leading-none">
                      {m.v}
                      {m.s}
                    </div>
                    <div className="mt-1.5 text-[11px] uppercase tracking-widest text-primary-foreground/55">
                      {m.l}
                    </div>
                  </div>
                ))}
              </div>
              <a
                href="#platform"
                className="inline-flex items-center gap-2 rounded-full bg-secondary px-5 py-2.5 text-body font-medium text-[hsl(var(--primary))] shadow-sm transition-transform hover:scale-[1.02] press-feedback w-fit"
              >
                {isAr ? "اكتشف المنصة" : "Explore the platform"} <Arrow className="h-4 w-4" />
              </a>
            </div>

            {/* Right: framed Rasheed console */}
            <div className="order-1 md:order-2">
              <HeroAssistant />
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
