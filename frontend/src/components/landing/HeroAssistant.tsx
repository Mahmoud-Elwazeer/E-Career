import { useEffect } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Sparkles } from "lucide-react";
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
    <div className={`relative w-full max-w-[440px] mx-auto ${className}`}>
      {/* Identity badge */}
      <motion.div
        className="relative z-10 mx-auto mb-2 w-fit inline-flex items-center gap-1.5 rounded-full bg-secondary px-4 py-1.5 text-caption font-semibold text-[hsl(var(--primary))] shadow-md"
        initial={reduced ? {} : { opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.5 }}
      >
        <Sparkles className="h-3.5 w-3.5" />
        {isAr ? "رشيد · مساعدك المهني" : "Rasheed · AI Career Coach"}
      </motion.div>

      {/* Interactive scene */}
      <motion.div
        initial={reduced ? {} : { opacity: 0, scale: 0.94, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 70, damping: 18, delay: 0.35 }}
      >
        <Rasheed3DOrFallback frame="bust" />
      </motion.div>
    </div>
  );
}
