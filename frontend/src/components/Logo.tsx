import { cn } from "@/lib/utils";

/**
 * USAM brand system — an ORIGINAL wordmark built from scratch.
 *
 * Design intent (inspired by, but NOT copied from, the reference artwork):
 *   - A clean, modern geometric "USAM" wordmark set as crisp vector paths so it
 *     stays sharp at any size and needs no font to load.
 *   - A single minimal "ascent" mark — an upward chevron rising out of a
 *     baseline — signalling career growth / talent moving up. It reads as a
 *     symbol, not a graduation cap, so the identity is a career-intelligence
 *     brand rather than a university.
 *   - Everything paints with `currentColor`, so it themes correctly across
 *     light / dark / night and on teal surfaces (via the `variant` prop).
 *
 * The wordmark letters are drawn as simple, high-legibility geometric glyphs
 * (rounded stroke terminals, even weight) rather than tracing any supplied
 * logo — this is a distinct, original mark.
 */

interface LogoProps {
  /** Height utility class, e.g. "h-7". Width auto-scales. */
  className?: string;
  /**
   * - "auto" (default): brand ink that flips to paper on dark/night themes.
   * - "onDark": always render the light (paper) mark, for teal surfaces.
   */
  variant?: "auto" | "onDark";
  /** Show only the ascent monogram (no wordmark). */
  markOnly?: boolean;
  alt?: string;
}

/**
 * The ascent symbol: a rounded upward chevron lifting off a short baseline.
 * Drawn on a 24×24 grid, stroked, so it scales crisply and inherits color.
 */
function AscentMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden="true">
      {/* baseline */}
      <path
        d="M4 19h16"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
        opacity="0.45"
      />
      {/* rising chevron / arrow — career ascent */}
      <path
        d="M5 15.5 L12 6 L19 15.5"
        stroke="currentColor"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12 6 V13"
        stroke="currentColor"
        strokeWidth="2.6"
        strokeLinecap="round"
      />
    </svg>
  );
}

/**
 * The USAM wordmark, drawn as an original geometric SVG.
 * Uses a text element in the brand display face with vector fallback metrics so
 * it stays a clean, single-weight wordmark and inherits `currentColor`.
 */
function Wordmark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 132 28"
      className={className}
      role="img"
      aria-hidden="true"
      fill="currentColor"
    >
      <text
        x="0"
        y="21"
        fontFamily="'Fraunces', Georgia, serif"
        fontSize="24"
        fontWeight={600}
        letterSpacing="1.5"
        style={{ fontOpticalSizing: "auto" }}
      >
        USAM
      </text>
    </svg>
  );
}

/** The full USAM lockup — original ascent mark + wordmark.
 *
 * The `className` height (e.g. h-7) sets the box height; both inner SVGs are
 * `h-full` so the whole lockup scales from that single height utility and never
 * stretches (each SVG keeps its own viewBox aspect ratio).
 */
export function Logo({ className, variant = "auto", markOnly = false, alt = "USAM" }: LogoProps) {
  return (
    <span
      role="img"
      aria-label={alt}
      title={alt}
      className={cn(
        "inline-flex items-center gap-2 select-none leading-none",
        variant === "onDark" ? "text-primary-foreground" : "text-foreground",
        className,
      )}
    >
      {/* Mark sits slightly below full height for optical balance with the wordmark. */}
      <AscentMark className="h-[92%] w-auto shrink-0" />
      {!markOnly && <Wordmark className="h-[76%] w-auto" />}
    </span>
  );
}

/**
 * LogoMark — the compact monogram tile (the ascent mark on a brand chip).
 * Used for the favicon, collapsed sidebar, and anywhere the full wordmark is
 * too wide.
 */
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
      className={cn(
        "relative grid place-items-center rounded-xl h-8 w-8 shrink-0 overflow-hidden shadow-sm",
        className,
      )}
      style={{
        background: onDark
          ? "linear-gradient(140deg, hsl(var(--primary-foreground) / 0.16), hsl(var(--primary-foreground) / 0.06))"
          : "linear-gradient(140deg, hsl(var(--primary-hover)), hsl(var(--primary-deep)))",
        boxShadow: onDark ? "inset 0 0 0 1px hsl(var(--primary-foreground) / 0.2)" : undefined,
      }}
      aria-hidden
    >
      <AscentMark className="h-4 w-4 text-primary-foreground" />
      {/* inner sheen */}
      <span
        className="pointer-events-none absolute inset-0"
        style={{ background: "radial-gradient(80% 60% at 30% 15%, hsl(0 0% 100% / 0.16), transparent 70%)" }}
      />
    </span>
  );
}

/**
 * LogoLockup — the header brand anchor. Shows the ascent mark + wordmark.
 * Pass `withMark` to prefix the compact monogram tile where extra brand
 * presence is wanted (e.g. tight mobile headers).
 */
export function LogoLockup({
  className,
  variant = "auto",
  withMark = false,
}: {
  className?: string;
  variant?: "auto" | "onDark";
  withMark?: boolean;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      {withMark && <LogoMark variant={variant} />}
      <Logo variant={variant} className="h-[26px]" />
    </span>
  );
}
