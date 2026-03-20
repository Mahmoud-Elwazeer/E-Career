import { motion, useReducedMotion } from "framer-motion";
import { Search } from "lucide-react";
import { useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SearchBarMotionProps {
  children: ReactNode; // The actual <Input> element
  className?: string;
}

/**
 * Wraps a search input with a focus ring expansion + icon color shift.
 * GPU-only: transforms ring scale via CSS box-shadow transition.
 * Reduced motion: simple border-color change.
 */
export function SearchBarMotion({ children, className }: SearchBarMotionProps) {
  const [focused, setFocused] = useState(false);
  const reduced = useReducedMotion();

  return (
    <motion.div
      className={cn("relative flex-1", className)}
      onFocusCapture={() => setFocused(true)}
      onBlurCapture={() => setFocused(false)}
      animate={
        reduced
          ? {}
          : {
              boxShadow: focused
                ? "0 0 0 3px hsl(var(--ring) / 0.15)"
                : "0 0 0 0px hsl(var(--ring) / 0)",
            }
      }
      transition={{ duration: 0.25, ease: [0.25, 0.1, 0.25, 1] }}
      style={{ borderRadius: "var(--radius-xl)" }}
    >
      <motion.div
        className="absolute start-3.5 top-1/2 -translate-y-1/2 pointer-events-none z-10"
        animate={
          reduced
            ? {}
            : {
                scale: focused ? 1.1 : 1,
                color: focused
                  ? "hsl(var(--primary))"
                  : "hsl(var(--muted-foreground))",
              }
        }
        transition={{ type: "spring", stiffness: 400, damping: 24 }}
      >
        <Search className="h-4 w-4" />
      </motion.div>
      {children}
    </motion.div>
  );
}
