import { cn } from "@/lib/utils";

interface LogoProps {
  /** Height utility class, e.g. "h-8". Width auto-scales. */
  className?: string;
  /**
   * Rendering context:
   * - "auto" (default): black wordmark that inverts to white in dark/night themes.
   * - "onDark": always render the white (inverted) wordmark, for placement on the
   *   primary/teal background (e.g. footer, chambers) regardless of theme.
   */
  variant?: "auto" | "onDark";
  alt?: string;
}

/**
 * USAM wordmark. The source asset is a black mark on transparency, so we invert
 * it for dark surfaces via CSS rather than shipping multiple files.
 */
export function Logo({ className, variant = "auto", alt = "USAM" }: LogoProps) {
  return (
    <img
      src="/logo-usam.png"
      alt={alt}
      className={cn(
        "w-auto select-none object-contain",
        variant === "onDark" ? "invert" : "dark:invert night:invert",
        className,
      )}
      draggable={false}
    />
  );
}

/**
 * LogoLockup — a branded lockup pairing a compact teal "U" mark tile with the
 * USAM wordmark. Gives the header a real brand anchor instead of a bare image.
 * The mark uses the brand gradient; the wordmark reuses the Logo asset.
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
  const onDark = variant === "onDark";
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <span
        className={cn(
          "relative grid place-items-center rounded-xl h-8 w-8 shrink-0 overflow-hidden",
          "shadow-sm",
        )}
        style={{
          background: onDark
            ? "linear-gradient(140deg, hsl(var(--primary-foreground) / 0.16), hsl(var(--primary-foreground) / 0.06))"
            : "linear-gradient(140deg, hsl(var(--primary-hover)), hsl(var(--primary-deep)))",
          boxShadow: onDark ? "inset 0 0 0 1px hsl(var(--primary-foreground) / 0.2)" : undefined,
        }}
        aria-hidden
      >
        <span
          className={cn(
            "font-display text-[15px] font-semibold leading-none",
            onDark ? "text-primary-foreground" : "text-primary-foreground",
          )}
        >
          U
        </span>
        {/* subtle inner sheen */}
        <span
          className="pointer-events-none absolute inset-0"
          style={{ background: "radial-gradient(80% 60% at 30% 15%, hsl(0 0% 100% / 0.18), transparent 70%)" }}
        />
      </span>
      {showWordmark && <Logo variant={variant} className="h-6" />}
    </span>
  );
}
