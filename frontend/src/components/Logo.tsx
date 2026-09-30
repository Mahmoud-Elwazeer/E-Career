import { cn } from "@/lib/utils";

/**
 * USAM Career — logo system (vector, single source of truth).
 *
 * CONCEPT ("rising counter"): a clean geometric USAM wordmark where the career
 * signal is BUILT INTO the letterform, not pasted on. The leading "U" is drawn
 * as an open channel and a teal ascent bar rises inside its counter, tipped
 * with a small upward notch — reading as "opportunity opening upward / career
 * ascent" at the first letter. The rest (S A M) are matched single-weight
 * rounded strokes so the mark stays one balanced word and shrinks to a crisp
 * favicon (the U + ascent alone).
 *
 * Everything is currentColor for the letters (themes light/dark/night) with the
 * ascent locked to the brand teal (--secondary/--primary in dark). One system
 * powers: primary lockup, compact navbar, icon/monogram, favicon.
 *
 * Motion lives in index.css (.usam-*). It is per-letter + accent-driven, not a
 * whole-logo move, and is fully disabled under prefers-reduced-motion.
 */

/** Shared letter geometry on a 0..208 × 0..64 grid. Stroke-drawn, round caps. */
const STROKE = 12;

interface LogoProps {
  /** Height utility class, e.g. "h-7". Width auto-scales. */
  className?: string;
  /** "auto" = ink on paper (themes); "onDark" = always the light mark. */
  variant?: "auto" | "onDark";
  /** Render only the U + ascent monogram (compact / favicon contexts). */
  markOnly?: boolean;
  /** Enable the load reveal + hover micro-motion (default true). */
  animated?: boolean;
  alt?: string;
}

/** The U + ascent — the reusable core mark (used standalone for the icon). */
function CoreU({ animated }: { animated: boolean }) {
  return (
    <g>
      {/* U channel */}
      <path
        className={cn("usam-letter", animated && "usam-anim usam-anim-0")}
        d="M12 8 V34 a20 20 0 0 0 40 0 V8"
        stroke="currentColor"
        strokeWidth={STROKE}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      {/* Teal ascent rising inside the U's counter (the career signal). */}
      <g
        className={cn("usam-ascent", animated && "usam-ascent-anim")}
        stroke="hsl(var(--secondary))"
        strokeWidth={STROKE}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      >
        <path d="M32 40 V12" />
        <path d="M22 24 L32 12 L42 24" />
      </g>
    </g>
  );
}

/** The full USAM wordmark SVG. */
function UsamWordmark({ animated, markOnly }: { animated: boolean; markOnly?: boolean }) {
  const letter = (i: number) => cn("usam-letter", animated && `usam-anim usam-anim-${i}`);
  return (
    <svg
      viewBox={markOnly ? "0 0 64 64" : "0 0 212 64"}
      className={cn("h-full w-auto overflow-visible", animated && "usam-svg")}
      fill="none"
      aria-hidden="true"
    >
      {markOnly ? (
        <CoreU animated={animated} />
      ) : (
        <>
          <CoreU animated={animated} />
          <g
            stroke="currentColor"
            strokeWidth={STROKE}
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            {/* S */}
            <path
              className={letter(1)}
              d="M104 14 a15 12 0 0 0 -19 -2 a12 12 0 0 0 1 22 a12 12 0 0 1 1 22 a15 12 0 0 1 -19 -2"
            />
            {/* A */}
            <path className={letter(2)} d="M116 56 L134 10 L152 56" />
            <path className={letter(2)} d="M123 40 H145" />
            {/* M */}
            <path className={letter(3)} d="M166 56 V12 L185 38 L204 12 V56" />
          </g>
        </>
      )}
    </svg>
  );
}

/** Primary lockup / navbar logo. */
export function Logo({
  className,
  variant = "auto",
  markOnly = false,
  animated = true,
  alt = "USAM",
}: LogoProps) {
  return (
    <span
      role="img"
      aria-label={alt}
      title={alt}
      className={cn(
        "usam-logo group inline-flex items-center leading-none",
        variant === "onDark" ? "text-primary-foreground" : "text-foreground",
        className,
      )}
    >
      <UsamWordmark animated={animated} markOnly={markOnly} />
    </span>
  );
}

/**
 * LogoMark — compact square chip carrying the U + ascent monogram. For the
 * collapsed sidebar, tight mobile headers, and app-icon contexts.
 */
export function LogoMark({
  className,
  variant = "auto",
  animated = true,
}: {
  className?: string;
  variant?: "auto" | "onDark";
  animated?: boolean;
}) {
  const onDark = variant === "onDark";
  return (
    <span
      className={cn(
        "usam-logo group relative grid h-8 w-8 shrink-0 place-items-center rounded-xl overflow-hidden shadow-sm",
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
      <span className="grid h-[64%] w-[64%] place-items-center text-primary-foreground">
        <UsamWordmark animated={animated} markOnly />
      </span>
      <span
        className="pointer-events-none absolute inset-0"
        style={{ background: "radial-gradient(80% 60% at 30% 15%, hsl(0 0% 100% / 0.16), transparent 70%)" }}
      />
    </span>
  );
}

/**
 * LogoLockup — header brand anchor. The wordmark alone by default; pass
 * `withMark` to prefix the monogram chip in tight contexts.
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
      <Logo variant={variant} className="h-[24px]" />
    </span>
  );
}
