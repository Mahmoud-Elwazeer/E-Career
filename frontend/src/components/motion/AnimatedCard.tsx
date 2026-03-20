import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

interface AnimatedCardProps {
  children: ReactNode;
  className?: string;
}

export function AnimatedCard({ children, className }: AnimatedCardProps) {
  const reduced = useReducedMotion();

  if (reduced) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      whileHover={{
        y: -2,
        boxShadow: "var(--shadow-md)",
        transition: { duration: 0.2, type: "spring", stiffness: 300, damping: 24 },
      }}
      whileTap={{
        scale: 0.98,
        transition: { duration: 0.05 },
      }}
    >
      {children}
    </motion.div>
  );
}
