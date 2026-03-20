import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

interface UnderlineSweepProps {
  children: ReactNode;
  className?: string;
  /** Trigger on viewport or hover */
  trigger?: "view" | "hover";
  /** Color CSS variable */
  color?: string;
}

/**
 * Directional underline sweep — "arrow progress" motion.
 * Sweeps from inline-start → inline-end. Auto-flips in RTL.
 */
export function UnderlineSweep({
  children,
  className,
  trigger = "view",
  color = "hsl(var(--primary))",
}: UnderlineSweepProps) {
  const reduced = useReducedMotion();
  const dir = document.documentElement.dir || "ltr";
  const origin = dir === "rtl" ? "100% 50%" : "0% 50%";

  if (reduced) {
    return <span className={className}>{children}</span>;
  }

  const underlineStyle = {
    position: "absolute" as const,
    bottom: 0,
    insetInlineStart: 0,
    width: "100%",
    height: "2px",
    backgroundColor: color,
    transformOrigin: origin,
  };

  const animateProps =
    trigger === "view"
      ? {
          initial: { scaleX: 0 },
          whileInView: { scaleX: 1 },
          viewport: { once: true, amount: 0.5 },
        }
      : {
          initial: { scaleX: 0 },
          whileHover: { scaleX: 1 },
        };

  return (
    <span className={`relative inline-block ${className || ""}`}>
      {children}
      <motion.span
        style={underlineStyle}
        {...animateProps}
        transition={{ duration: 0.4, ease: [0, 0, 0.2, 1] }}
      />
    </span>
  );
}

interface HighlightChipProps {
  children: ReactNode;
  className?: string;
  color?: string;
}

/**
 * Background color wipe fills behind text — inline emphasis.
 * Direction-aware: sweeps from inline-start.
 */
export function HighlightChip({
  children,
  className,
  color = "hsl(var(--primary) / 0.12)",
}: HighlightChipProps) {
  const reduced = useReducedMotion();
  const dir = document.documentElement.dir || "ltr";
  const bgPosition = dir === "rtl" ? "right center" : "left center";

  if (reduced) {
    return (
      <span
        className={`px-1.5 py-0.5 rounded ${className || ""}`}
        style={{ backgroundColor: color }}
      >
        {children}
      </span>
    );
  }

  return (
    <motion.span
      className={`px-1.5 py-0.5 rounded inline-block ${className || ""}`}
      style={{
        backgroundImage: `linear-gradient(${color}, ${color})`,
        backgroundRepeat: "no-repeat",
        backgroundPosition: bgPosition,
      }}
      initial={{ backgroundSize: "0% 100%" }}
      whileInView={{ backgroundSize: "100% 100%" }}
      viewport={{ once: true, amount: 0.5 }}
      transition={{ duration: 0.35, ease: [0, 0, 0.2, 1] }}
    >
      {children}
    </motion.span>
  );
}
