import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Admin-grade motion primitives.
 * Restrained timings: faster durations, minimal overshoot, no spring bounce.
 * All GPU-composited (transform + opacity only).
 */

/* ── Bulk Actions Bar ── */
export function BulkActionsBar({
  visible,
  children,
  className,
}: {
  visible: boolean;
  children: ReactNode;
  className?: string;
}) {
  const reduced = useReducedMotion();

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={reduced ? { opacity: 0 } : { opacity: 0, y: -8, scaleY: 0.95 }}
          animate={{ opacity: 1, y: 0, scaleY: 1 }}
          exit={reduced ? { opacity: 0 } : { opacity: 0, y: -8, scaleY: 0.95 }}
          transition={{ duration: 0.2, ease: [0.25, 0.1, 0.25, 1] }}
          className={cn("origin-top", className)}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/* ── Status Badge (animated color transition) ── */
const statusStyles: Record<string, string> = {
  draft: "bg-muted text-muted-foreground",
  review: "bg-warning/15 text-warning border-warning/25",
  published: "bg-success/15 text-success border-success/25",
  active: "bg-success/15 text-success border-success/25",
  expired: "bg-destructive/15 text-destructive border-destructive/25",
  error: "bg-destructive/15 text-destructive border-destructive/25",
};

export function AnimatedStatusBadge({
  status,
  label,
}: {
  status: string;
  label: string;
}) {
  const reduced = useReducedMotion();

  return (
    <motion.span
      key={status}
      initial={reduced ? false : { opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.2, ease: [0.25, 0.1, 0.25, 1] }}
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border",
        "transition-colors duration-200",
        statusStyles[status] || statusStyles.draft
      )}
    >
      {label}
    </motion.span>
  );
}

/* ── Animated Progress Bar (for charts) ── */
export function AnimatedProgressBar({
  value,
  className,
}: {
  value: number;
  className?: string;
}) {
  const reduced = useReducedMotion();

  return (
    <div className={cn("relative h-2 w-full overflow-hidden rounded-full bg-secondary", className)}>
      <motion.div
        className="h-full bg-primary rounded-full"
        initial={reduced ? { width: `${value}%` } : { width: "0%" }}
        whileInView={{ width: `${value}%` }}
        viewport={{ once: true }}
        transition={{
          duration: reduced ? 0 : 0.6,
          delay: 0.1,
          ease: [0.25, 0.1, 0.25, 1],
        }}
      />
    </div>
  );
}
