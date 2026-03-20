import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

interface TextRevealProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  /** Use "extralight" for Poppins 200 subtitle lines */
  weight?: "medium" | "extralight";
  /** Disable blur for perf on low-end */
  blur?: boolean;
}

/**
 * Kinetic title reveal — clip-path mask + vertical shift + optional blur.
 * Evokes the "cap toss" rising motion. Safe for Arabic (no text splitting).
 */
export function TextReveal({
  children,
  className,
  delay = 0,
  weight = "medium",
  blur = true,
}: TextRevealProps) {
  const reduced = useReducedMotion();

  if (reduced) {
    return (
      <div className={className} style={{ fontWeight: weight === "extralight" ? 200 : 500 }}>
        {children}
      </div>
    );
  }

  return (
    <div className={className} style={{ overflow: "hidden" }}>
      <motion.div
        style={{ fontWeight: weight === "extralight" ? 200 : 500 }}
        initial={{
          y: "110%",
          opacity: 0,
          filter: blur ? "blur(4px)" : "blur(0px)",
        }}
        whileInView={{
          y: "0%",
          opacity: 1,
          filter: "blur(0px)",
        }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{
          y: {
            type: "spring",
            stiffness: 80,
            damping: 18,
            mass: 1.2,
            delay,
          },
          opacity: {
            duration: 0.4,
            ease: [0, 0, 0.2, 1],
            delay,
          },
          filter: {
            duration: 0.5,
            ease: [0, 0, 0.2, 1],
            delay,
          },
        }}
      >
        {children}
      </motion.div>
    </div>
  );
}
