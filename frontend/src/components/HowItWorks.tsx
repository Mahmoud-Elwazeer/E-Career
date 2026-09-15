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
        className="flex flex-col items-center text-center mb-12 md:mb-16"
        initial={reduced ? false : { opacity: 0, y: 20 }}
        animate={isInView ? { opacity: 1, y: 0 } : undefined}
        transition={{ duration: MOTION.duration.slow, ease: MOTION.ease.out }}
      >
        <span className="eyebrow mb-4">{sectionTitle}</span>
        <h2 className="text-heading-1 tracking-tight mb-3 max-w-xl">
          {sectionSubtitle}
        </h2>
      </motion.div>

      {/* Desktop: 3 connected steps */}
      <div className="hidden md:block relative">
        {/* Connector line behind the cards */}
        <div className="absolute top-[52px] left-[16%] right-[16%] h-px bg-gradient-to-r from-transparent via-primary/25 to-transparent" aria-hidden="true" />
        <div className="grid grid-cols-3 gap-8">
          {steps.map((step, i) => (
            <motion.div
              key={step.title}
              className="relative flex flex-col items-center text-center px-4"
              initial={reduced ? false : { opacity: 0, y: 24 }}
              animate={isInView ? { opacity: 1, y: 0 } : undefined}
              transition={{
                duration: MOTION.duration.slow,
                delay: reduced ? 0 : 0.15 + i * 0.14,
                ease: MOTION.ease.out,
              }}
            >
              {/* Numbered gradient tile */}
              <div className="relative mb-6">
                <div
                  className="flex h-[104px] w-[104px] items-center justify-center rounded-2xl text-primary-foreground shadow-lg"
                  style={{ background: "linear-gradient(145deg, hsl(var(--primary-hover)), hsl(var(--primary)))" }}
                >
                  <step.icon className="h-10 w-10" strokeWidth={1.6} />
                </div>
                <span className="absolute -top-2 -end-2 flex h-8 w-8 items-center justify-center rounded-full bg-secondary text-sm font-bold text-[hsl(var(--primary))] shadow-md ring-4 ring-[hsl(var(--surface-2))]">
                  {i + 1}
                </span>
              </div>
              <h3 className="text-heading-3 font-semibold mb-2">{step.title}</h3>
              <p className="text-body text-muted-foreground leading-relaxed max-w-[15rem]">
                {step.description}
              </p>
            </motion.div>
          ))}
        </div>
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
