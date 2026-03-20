import { motion, useReducedMotion, AnimatePresence } from "framer-motion";
import type { ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { useDirectionalMotion } from "@/hooks/use-directional-motion";

interface RouteTransitionProps {
  children: ReactNode;
}

/**
 * Wraps route content with AnimatePresence for enter/exit transitions.
 * Uses directional-aware slide (flips in RTL) with reduced-motion fallback.
 */
export function RouteTransition({ children }: RouteTransitionProps) {
  const location = useLocation();
  const { pageEnter, pageVisible, pageExit, pageTransition } = useDirectionalMotion();
  const reduced = useReducedMotion();

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={location.pathname}
        initial={pageEnter}
        animate={pageVisible}
        exit={pageExit}
        transition={pageTransition}
        style={{ willChange: reduced ? "opacity" : "opacity, transform" }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
