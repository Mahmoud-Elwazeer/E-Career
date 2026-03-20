import { ExternalLink } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { useTheme } from "@/hooks/use-theme";
import { cn } from "@/lib/utils";

/**
 * Signature "Apply Now" CTA with premium micro-interactions.
 *
 * States: idle → hover (arrow slides, progress bar fills) → press (scale) → redirect hint
 * RTL: arrow direction flips automatically via logical properties + flipX.
 * Reduced motion: simple opacity transition, no transform.
 */

interface ApplyNowButtonProps {
  href: string;
  disabled?: boolean;
  disabledLabel?: string;
  className?: string;
  size?: "default" | "compact";
}

export function ApplyNowButton({
  href,
  disabled = false,
  disabledLabel,
  className,
  size = "default",
}: ApplyNowButtonProps) {
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const isRTL = dir === "rtl";
  const reduced = useReducedMotion();
  const flipX = isRTL ? -1 : 1;

  const label = isAr ? "قدّم الآن" : "Apply Now";
  const expiredLabel = disabledLabel || (isAr ? "انتهت الصلاحية" : "Listing Expired");

  const isCompact = size === "compact";
  const height = isCompact ? "h-11" : "h-12";

  if (disabled) {
    return (
      <div
        className={cn(
          "inline-flex items-center justify-center rounded-xl font-medium",
          "bg-muted text-muted-foreground cursor-not-allowed select-none",
          height,
          isCompact ? "px-5 text-sm" : "px-6",
          className
        )}
      >
        {expiredLabel}
      </div>
    );
  }

  // Reduced-motion: clean fade, no transforms
  if (reduced) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-xl font-medium",
          "bg-primary text-primary-foreground",
          "hover:bg-primary-hover active:opacity-90 transition-colors duration-150",
          "shadow-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          height,
          isCompact ? "px-5 text-sm" : "px-6",
          className
        )}
      >
        {label}
        <ExternalLink className="h-4 w-4" />
      </a>
    );
  }

  return (
    <motion.a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "group/cta relative inline-flex items-center justify-center gap-2 rounded-xl font-medium overflow-hidden",
        "bg-primary text-primary-foreground",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        height,
        isCompact ? "px-5 text-sm" : "px-6",
        className
      )}
      // Idle glow
      initial="idle"
      whileHover="hover"
      whileTap="press"
      variants={{
        idle: { scale: 1, boxShadow: "0 0 20px hsl(178 72% 13% / 0.12)" },
        hover: { scale: 1.02, boxShadow: "0 0 28px hsl(178 72% 13% / 0.22)" },
        press: { scale: 0.97, boxShadow: "0 0 12px hsl(178 72% 13% / 0.18)" },
      }}
      transition={{ type: "spring", stiffness: 400, damping: 22, mass: 0.8 }}
    >
      {/* Progress bar fill on hover — the "progress" motif */}
      <motion.span
        className="absolute inset-0 bg-primary-hover origin-left"
        style={{ originX: isRTL ? 1 : 0 }}
        variants={{
          idle: { scaleX: 0 },
          hover: { scaleX: 1 },
          press: { scaleX: 1 },
        }}
        transition={{ duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
        aria-hidden
      />

      {/* Label */}
      <span className="relative z-10">{label}</span>

      {/* Arrow with directional slide */}
      <motion.span
        className="relative z-10 inline-flex"
        variants={{
          idle: { x: 0, opacity: 0.7 },
          hover: { x: 4 * flipX, opacity: 1 },
          press: { x: 6 * flipX, opacity: 1 },
        }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
      >
        <ExternalLink className="h-4 w-4" />
      </motion.span>

      {/* Bottom progress accent line — "progress bar" motif */}
      <motion.span
        className="absolute bottom-0 h-[2px] bg-primary-foreground/30"
        style={{
          [isRTL ? "right" : "left"]: 0,
        }}
        variants={{
          idle: { width: "0%" },
          hover: { width: "100%" },
          press: { width: "100%" },
        }}
        transition={{ duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
        aria-hidden
      />
    </motion.a>
  );
}
