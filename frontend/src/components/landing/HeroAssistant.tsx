import { useEffect } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useTheme } from "@/hooks/use-theme";
import { Rasheed3DOrFallback } from "@/components/rashid/Rasheed3DOrFallback";
import { useRasheed } from "@/components/rashid/rasheed-state";

/**
 * HeroAssistant — landing hero composition featuring the interactive Rasheed
 * character. Uses the drop-in <Rasheed3DOrFallback/>: renders the real 3D
 * avatar once the GLB asset exists, otherwise the animated vector scene. Either
 * way it is driven by SEMANTIC STATE via useRasheed (greeting on mount, then
 * presenting), so the app code never couples to animation timelines.
 * Clean single identity badge; brand palette only, bilingual, reduced-motion safe.
 */

interface HeroAssistantProps {
  className?: string;
}

export function HeroAssistant({ className = "" }: HeroAssistantProps) {
  const reduced = useReducedMotion();
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const rasheed = useRasheed();

  // Greet on mount, then settle into presenting the platform.
  useEffect(() => {
    rasheed.react("greeting");
    const t = setTimeout(() => rasheed.setState("holdingScreen"), 2600);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <motion.div
      className={`relative w-full max-w-[440px] mx-auto ${className}`}
      initial={reduced ? {} : { opacity: 0, scale: 0.96, y: 16 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 70, damping: 18, delay: 0.35 }}
    >
      {/* Framed product surface — Rasheed lives inside a glass console with a
          real header, so the hero's right column reads as a designed product
          panel rather than a floating figure. */}
      <div className="glass-panel relative overflow-hidden rounded-[1.75rem] p-3">
        {/* Header bar: persona identity + live status */}
        <div className="flex items-center justify-between px-2 pt-1 pb-3">
          <span className="flex items-center gap-2.5">
            <span className="signal-dot" />
            <span className="flex items-baseline gap-1.5">
              <span className="font-display text-base font-semibold text-primary-foreground leading-none">
                {isAr ? "رشيد" : "Rasheed"}
              </span>
              <span className="text-caption text-primary-foreground/70">
                {isAr ? "مساعدك المهني" : "AI Career Coach"}
              </span>
            </span>
          </span>
          <span className="font-mono-data text-[10px] uppercase tracking-widest text-primary-foreground/50">
            {isAr ? "متصل" : "ONLINE"}
          </span>
        </div>

        {/* Interactive scene inside the console */}
        <div className="relative rounded-2xl bg-primary-foreground/5 border border-primary-foreground/10 overflow-hidden">
          <Rasheed3DOrFallback frame="bust" />
        </div>
      </div>
    </motion.div>
  );
}
