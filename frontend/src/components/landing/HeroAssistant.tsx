import { motion, useReducedMotion } from "framer-motion";
import { Sparkles, Search, FileText, Mic } from "lucide-react";
import { useTheme } from "@/hooks/use-theme";
import { RasheedAvatar } from "@/components/rashid/RasheedAvatar";

/**
 * HeroAssistant — landing hero composition featuring the polished, professional
 * Rasheed avatar inside a glass card with an identity label and intentionally-
 * placed capability chips. Brand palette only, bilingual, reduced-motion safe.
 */

interface HeroAssistantProps {
  className?: string;
}

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

        {/* Persona — polished professional avatar */}
        <div className="mx-auto flex w-full max-w-[240px] items-center justify-center py-2">
          <RasheedAvatar expression="greeting" size={200} />
        </div>

        {/* Caption */}
        <p className="text-center text-caption text-primary-foreground/80 mt-3">
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
