import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

interface JobCardMotionProps {
  children: ReactNode;
  index: number;
  /** Only stagger-animate the first N cards (default 8). Cards beyond this render instantly. */
  staggerLimit?: number;
}

/**
 * Motion wrapper for job cards on the listing page.
 *
 * Hover: lift -2px + border-glow via box-shadow (GPU-only, no filter/blur).
 * Entrance: staggered fade+slide for first N items only — safe for pagination/infinite scroll.
 * Press: subtle scale feedback.
 * Reduced motion: instant opacity, no transforms.
 */
export function JobCardMotion({ children, index, staggerLimit = 8 }: JobCardMotionProps) {
  const reduced = useReducedMotion();
  const shouldAnimate = index < staggerLimit;
  const delay = shouldAnimate ? index * 0.05 : 0;

  if (reduced) {
    return <div>{children}</div>;
  }

  return (
    <motion.div
      initial={shouldAnimate ? { opacity: 0, y: 16 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.35,
        delay,
        ease: [0, 0, 0.2, 1],
      }}
      whileHover={{
        y: -2,
        boxShadow: "0 0 0 1px hsl(var(--primary) / 0.15), var(--shadow-md)",
        transition: { duration: 0.2, type: "spring", stiffness: 300, damping: 24 },
      }}
      whileTap={{
        scale: 0.985,
        transition: { duration: 0.08 },
      }}
    >
      {children}
    </motion.div>
  );
}
