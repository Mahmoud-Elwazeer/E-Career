import { cn } from "@/lib/utils";

/**
 * USAM brand logo — the real brand artwork (public/usam-brand.jpg): the white
 * "USAM" wordmark with the teal upward arrow through the U.
 *
 * The artwork has a dark background baked in, so we present it inside a dark
 * rounded "brand chip" — the image's background blends into the chip, giving a
 * clean, intentional lockup that works on light AND dark navbars.
 *
 * "Living" motion: the chip gently floats/breathes continuously and lifts on
 * hover, with a soft shine sweep — so the brand feels alive. All motion is
 * gated behind prefers-reduced-motion (static fallback).
 */

const BRAND_SRC = "/usam-brand.jpg";

interface LogoProps {
  /** Height utility class, e.g. "h-7". Width auto-scales. */
  className?: string;
  /** Kept for API compatibility (the artwork is the same on all surfaces). */
  variant?: "auto" | "onDark";
  /** Show only the compact monogram chip (no effect here — same artwork). */
  markOnly?: boolean;
  /** Enable the subtle "living" motion + hover interaction (default true). */
  animated?: boolean;
  alt?: string;
}

/** The full USAM logo — real artwork in a living brand chip. */
export function Logo({
  className,
  animated = true,
  alt = "USAM",
}: LogoProps) {
  return (
    <span
      className={cn(
        "usam-logo group inline-flex items-center overflow-hidden rounded-xl align-middle",
        animated && "usam-logo-anim",
        className,
      )}
      role="img"
      aria-label={alt}
      title={alt}
    >
      <img
        src={BRAND_SRC}
        alt={alt}
        draggable={false}
        className="usam-logo-img h-full w-auto select-none object-contain"
      />
      {/* shine sweep on hover */}
      <span className="usam-logo-shine pointer-events-none absolute inset-0" aria-hidden />
    </span>
  );
}

/**
 * LogoMark — the compact square brand chip (same artwork, tight crop feel).
 * Used for the favicon area, collapsed sidebar, tight mobile headers.
 */
export function LogoMark({
  className,
  animated = true,
}: {
  className?: string;
  variant?: "auto" | "onDark";
  animated?: boolean;
}) {
  return (
    <span
      className={cn(
        "usam-logo group relative grid h-8 w-8 shrink-0 place-items-center overflow-hidden rounded-xl shadow-sm",
        animated && "usam-logo-anim",
        className,
      )}
      aria-hidden
    >
      <img
        src={BRAND_SRC}
        alt=""
        draggable={false}
        className="h-full w-full select-none object-cover"
      />
      <span className="usam-logo-shine pointer-events-none absolute inset-0" aria-hidden />
    </span>
  );
}

/**
 * LogoLockup — the header brand anchor. Shows the real USAM artwork.
 * Pass `withMark` to prefix the compact chip where extra brand presence is
 * wanted (e.g. tight mobile headers).
 */
export function LogoLockup({
  className,
  withMark = false,
}: {
  className?: string;
  variant?: "auto" | "onDark";
  withMark?: boolean;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      {withMark && <LogoMark />}
      <Logo className="h-8" />
    </span>
  );
}
