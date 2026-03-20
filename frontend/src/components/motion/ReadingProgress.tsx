import { motion, useScroll, useSpring, useReducedMotion } from "framer-motion";
import { useRef } from "react";
import { useTheme } from "@/hooks/use-theme";

/**
 * A thin progress bar fixed at the top of the viewport that tracks
 * how far the user has scrolled through a target container.
 *
 * RTL: progress fills from right. Reduced motion: hidden entirely
 * (screen-reader users get no benefit, and the bar is decorative).
 */
export function ReadingProgress({ containerRef }: { containerRef: React.RefObject<HTMLElement> }) {
  const reduced = useReducedMotion();
  const { dir } = useTheme();
  const isRTL = dir === "rtl";

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  const scaleX = useSpring(scrollYProgress, {
    stiffness: 120,
    damping: 30,
    restDelta: 0.001,
  });

  if (reduced) return null;

  return (
    <motion.div
      className="fixed top-0 inset-x-0 h-[3px] z-50 bg-primary/10"
      aria-hidden
    >
      <motion.div
        className="h-full bg-primary origin-left"
        style={{
          scaleX,
          originX: isRTL ? 1 : 0,
          transformOrigin: isRTL ? "right" : "left",
        }}
      />
    </motion.div>
  );
}
