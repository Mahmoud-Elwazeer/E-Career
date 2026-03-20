/**
 * Centralized motion tokens for consistent animations across the app.
 * All durations in seconds (for framer-motion).
 */
export const MOTION = {
  duration: {
    instant: 0.05,
    fast: 0.15,
    normal: 0.3,
    slow: 0.5,
    slower: 0.6,
  },
  ease: {
    default: [0.25, 0.1, 0.25, 1] as const,
    out: [0, 0, 0.2, 1] as const,
    in: [0.4, 0, 1, 1] as const,
    spring: { type: "spring" as const, stiffness: 300, damping: 24 },
    springGentle: { type: "spring" as const, stiffness: 200, damping: 20 },
    springBouncy: { type: "spring" as const, stiffness: 500, damping: 25 },
  },
  stagger: {
    fast: 0.04,
    normal: 0.08,
    slow: 0.14,
  },
  /** Common animation presets */
  presets: {
    fadeUp: {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.45, ease: [0, 0, 0.2, 1] as const },
    },
    fadeIn: {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      transition: { duration: 0.3 },
    },
    scaleIn: {
      initial: { opacity: 0, scale: 0.92 },
      animate: { opacity: 1, scale: 1 },
      transition: { type: "spring" as const, stiffness: 300, damping: 24 },
    },
    hoverLift: {
      y: -3,
      transition: { type: "spring" as const, stiffness: 300, damping: 24 },
    },
    pressFeedback: {
      scale: 0.97,
      transition: { duration: 0.05 },
    },
  },
} as const;
