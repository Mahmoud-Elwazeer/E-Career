import { cn } from "@/lib/utils";

/**
 * USAM brand system — pure SVG (no PNG). Renders crisp at any size, themes
 * correctly across light/dark/night, and gives the product a real brand anchor.
 *
 * The mark is a rounded-square tile holding a "career path" glyph: an upward
 * routing line with a node — reading as forward career motion / a path
 * (masar), tying the visual to the platform's mission. The wordmark is drawn
 * as SVG text in the display serif so it never renders as a broken raster.
 */

interface LogoProps {
  /** Height utility class, e.g. "h-8". Width auto-scales. */
  className?: string;
  /**
   * - "auto" (default): ink wordmark that flips to paper on dark/night themes.
   * - "onDark": always render the light (paper) wordmark, for teal surfaces.
   */
  variant?: "auto" | "onDark";
  alt?: string;
}

/** Wordmark only (USAM), SVG text so it's always crisp and theme-correct. */
export function Logo({ className, variant = "auto", alt = "USAM" }: LogoProps) {
  return (
    <svg
      role="img"
      aria-label={alt}
      viewBox="0 0 132 32"
      className={cn(
        "w-auto select-none",
        variant === "onDark" ? "text-primary-foreground" : "text-foreground",
        className,
      )}
      fill="none"
    >
      <text
        x="0"
        y="24"
        fontFamily="Fraunces, Georgia, serif"
        fontSize="27"
        fontWeight="600"
        letterSpacing="-0.5"
        fill="currentColor"
      >
        USAM
      </text>
    </svg>
  );
}

/** The standalone "U" path-monogram tile. */
export function LogoMark({
  className,
  variant = "auto",
}: {
  className?: string;
  variant?: "auto" | "onDark";
}) {
  const onDark = variant === "onDark";
  return (
    <span
      className={cn("relative grid place-items-center rounded-xl h-8 w-8 shrink-0 overflow-hidden shadow-sm", className)}
      style={{
        background: onDark
          ? "linear-gradient(140deg, hsl(var(--primary-foreground) / 0.16), hsl(var(--primary-foreground) / 0.06))"
          : "linear-gradient(140deg, hsl(var(--primary-hover)), hsl(var(--primary-deep)))",
        boxShadow: onDark ? "inset 0 0 0 1px hsl(var(--primary-foreground) / 0.2)" : undefined,
      }}
      aria-hidden
    >
      <svg viewBox="0 0 32 32" className="h-full w-full" fill="none">
        {/* Career path: an ascending route with a destination node. The 'U'
            base curve grounds it as the USAM monogram. */}
        <path
          d="M9 9 v7 a7 7 0 0 0 14 0 V9"
          stroke="hsl(var(--primary-foreground))"
          strokeWidth="2.4"
          strokeLinecap="round"
          fill="none"
          opacity="0.9"
        />
        <path
          d="M16 21 L20 15 L24 18"
          stroke="hsl(var(--signal))"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        <circle cx="24" cy="18" r="2.1" fill="hsl(var(--signal))" />
      </svg>
      {/* inner sheen */}
      <span
        className="pointer-events-none absolute inset-0"
        style={{ background: "radial-gradient(80% 60% at 30% 15%, hsl(0 0% 100% / 0.16), transparent 70%)" }}
      />
    </span>
  );
}

/**
 * LogoLockup — mark tile + USAM wordmark. The header brand anchor.
 */
export function LogoLockup({
  className,
  variant = "auto",
  showWordmark = true,
}: {
  className?: string;
  variant?: "auto" | "onDark";
  showWordmark?: boolean;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark variant={variant} />
      {showWordmark && <Logo variant={variant} className="h-[22px]" />}
    </span>
  );
}
