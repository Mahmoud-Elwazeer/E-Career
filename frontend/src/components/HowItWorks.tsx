import { motion, useReducedMotion, useInView } from "framer-motion";
import { useRef } from "react";
import { cn } from "@/lib/utils";
import { MOTION } from "@/lib/motion-tokens";

interface Step {
  icon: React.ElementType;
  title: string;
  description: string;
}

interface HowItWorksProps {
  steps: Step[];
  sectionTitle: string;
  sectionSubtitle: string;
  className?: string;
}

export function HowItWorks({ steps, sectionTitle, sectionSubtitle, className }: HowItWorksProps) {
  const reduced = useReducedMotion();
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, amount: 0.15 });

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Header */}
      <motion.div
        className="text-center mb-10 md:mb-14"
        initial={reduced ? false : { opacity: 0, y: 20 }}
        animate={isInView ? { opacity: 1, y: 0 } : undefined}
        transition={{ duration: MOTION.duration.slow, ease: MOTION.ease.out }}
      >
        <h2 className="text-3xl sm:text-4xl lg:text-[2.5rem] font-bold tracking-tight mb-3 md:mb-4">
          {sectionTitle}
        </h2>
        <p className="text-body-lg text-muted-foreground max-w-md mx-auto">
          {sectionSubtitle}
        </p>
      </motion.div>

      {/* Desktop: 3-card grid */}
      <div className="hidden md:grid grid-cols-3 gap-6">
        {steps.map((step, i) => (
          <motion.div
            key={step.title}
            className="relative bg-card border rounded-xl p-6 text-center hover:shadow-md transition-shadow"
            initial={reduced ? false : { opacity: 0, y: 24 }}
            animate={isInView ? { opacity: 1, y: 0 } : undefined}
            transition={{
              duration: MOTION.duration.slow,
              delay: reduced ? 0 : 0.15 + i * 0.12,
              ease: MOTION.ease.out,
            }}
            whileHover={reduced ? {} : MOTION.presets.hoverLift}
          >
            {/* Number badge */}
            <div className="mx-auto w-16 h-16 rounded-full bg-primary-muted flex items-center justify-center relative mb-5">
              <step.icon className="h-7 w-7 text-primary" />
              <span className="absolute -top-1 -end-1 w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-semibold flex items-center justify-center shadow-sm">
                {i + 1}
              </span>
            </div>
            <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
            <p className="text-body text-muted-foreground leading-relaxed max-w-xs mx-auto">
              {step.description}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Mobile: vertical stepper */}
      <div className="md:hidden space-y-0">
        {steps.map((step, i) => (
          <motion.div
            key={step.title}
            className="relative flex gap-4"
            initial={reduced ? false : { opacity: 0, y: 16 }}
            animate={isInView ? { opacity: 1, y: 0 } : undefined}
            transition={{
              duration: MOTION.duration.slow,
              delay: reduced ? 0 : 0.1 + i * 0.12,
              ease: MOTION.ease.out,
            }}
          >
            {/* Step indicator column */}
            <div className="flex flex-col items-center shrink-0">
              <div className="w-10 h-10 rounded-full bg-primary text-primary-foreground text-sm font-semibold flex items-center justify-center shadow-sm z-10">
                {i + 1}
              </div>
              {i < steps.length - 1 && (
                <div className="w-px flex-1 bg-border my-1" />
              )}
            </div>

            {/* Content */}
            <div className={cn("pb-8", i === steps.length - 1 && "pb-0")}>
              <div className="flex items-center gap-2.5 mb-1.5">
                <div className="rounded-lg bg-primary-muted p-2">
                  <step.icon className="h-4 w-4 text-primary" />
                </div>
                <h3 className="text-lg font-semibold">{step.title}</h3>
              </div>
              <p className="text-body text-muted-foreground leading-relaxed">
                {step.description}
              </p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
