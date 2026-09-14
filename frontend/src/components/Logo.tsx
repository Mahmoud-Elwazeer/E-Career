import { cn } from "@/lib/utils";

interface LogoProps {
  /** Height utility class, e.g. "h-8". Width auto-scales. */
  className?: string;
  /**
   * Rendering context:
   * - "auto" (default): black wordmark that inverts to white in dark/night themes.
   * - "onDark": always render the white (inverted) wordmark, for placement on the
   *   primary/teal background (e.g. footer) regardless of theme.
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
