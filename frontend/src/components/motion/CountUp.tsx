import { useEffect, useRef, useState, useMemo } from "react";
import { motion, useReducedMotion, useInView } from "framer-motion";

interface CountUpProps {
  /** Target number (e.g., 2500) */
  target: number;
  /** Static suffix appended after the number (e.g., "+", "K") */
  suffix?: string;
  /** Static prefix before the number (e.g., "$") */
  prefix?: string;
  /** Duration in ms */
  duration?: number;
  /** Additional CSS class */
  className?: string;
  /** Format with locale separators */
  separator?: boolean;
}

/**
 * Animated count-up number — "arrow progress" reaching its mark.
 * Uses requestAnimationFrame for smooth 60fps counting.
 * Reduced motion: shows final value instantly.
 */
export function CountUp({
  target,
  suffix = "",
  prefix = "",
  duration = 1200,
  className,
  separator = true,
}: CountUpProps) {
  const reduced = useReducedMotion();
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.5 });
  const [display, setDisplay] = useState(reduced ? target : 0);
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (!inView || hasAnimated.current || reduced) return;
    hasAnimated.current = true;

    const start = performance.now();
    const from = 0;

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out: fast start, slow settle
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(from + (target - from) * eased);
      setDisplay(current);

      if (progress < 1) {
        requestAnimationFrame(tick);
      }
    }

    requestAnimationFrame(tick);
  }, [inView, target, duration, reduced]);

  const formatted = useMemo(() => {
    if (separator) return display.toLocaleString();
    return String(display);
  }, [display, separator]);

  if (reduced) {
    return (
      <span ref={ref} className={className}>
        {prefix}{separator ? target.toLocaleString() : target}{suffix}
      </span>
    );
  }

  return (
    <motion.span
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.5 }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 24,
        delay: 0,
      }}
    >
      {prefix}{formatted}{suffix}
    </motion.span>
  );
}
