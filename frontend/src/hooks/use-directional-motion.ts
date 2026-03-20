import { useReducedMotion } from "framer-motion";

/**
 * Provides direction-aware motion values for RTL/LTR layouts.
 * All horizontal animations flip automatically in RTL.
 */
export function useDirectionalMotion() {
  const dir = document.documentElement.dir || "ltr";
  const isRTL = dir === "rtl";
  const reduced = useReducedMotion();

  const flipX = isRTL ? -1 : 1;

  return {
    isRTL,
    flipX,

    // Page enter: slide from inline-end
    pageEnter: reduced
      ? { opacity: 0 }
      : { opacity: 0, x: 20 * flipX, y: 8 },

    // Page visible
    pageVisible: { opacity: 1, x: 0, y: 0 },

    // Page exit: slide toward inline-start
    pageExit: reduced
      ? { opacity: 0 }
      : { opacity: 0, x: -10 * flipX, y: -4 },

    // Transition config
    pageTransition: {
      duration: reduced ? 0.1 : 0.25,
      ease: [0.25, 0.1, 0.25, 1] as const,
    },

    // Shared layout transition (for layoutId morphs)
    sharedTransition: {
      type: "spring" as const,
      stiffness: reduced ? 500 : 300,
      damping: reduced ? 40 : 26,
      mass: reduced ? 0.5 : 0.8,
    },
  };
}
