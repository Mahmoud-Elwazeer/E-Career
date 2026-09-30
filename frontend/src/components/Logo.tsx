import { cn } from "@/lib/utils";

/**
 * USAM brand system — an ORIGINAL animated wordmark.
 *
 * Design (inspired by the teal-arrow reference, redrawn from scratch):
 *   - Bold, rounded, geometric "USAM" letters drawn as INDIVIDUAL stroked SVG
 *     paths — so each character is its own element and can animate on its own.
 *   - A teal upward arrow rising through the "U" (career ascent / growth).
 *   - Letters inherit `currentColor` so the wordmark themes across
 *     light / dark / night; the arrow keeps the brand teal on every surface.
 *
 * "Living" behaviour (the whole point of this version): the letters do NOT move
 * as one block. Each letter draws in with a staggered stroke reveal, then holds
 * a gentle, individually-phased float; the arrow shoots up on a loop. On hover
 * the letters lift in sequence. All motion is gated behind
 * prefers-reduced-motion (static, fully-legible fallback).
 */

interface LogoProps {
  /** Height utility class, e.g. "h-7". Width auto-scales. */
  className?: string;
  /**
   * - "auto" (default): brand ink that flips to paper on dark/night themes.
   * - "onDark": always render the light (paper) mark, for teal surfaces.
   */
  variant?: "auto" | "onDark";
  /** Show only the U + arrow monogram (no S A M). */
  markOnly?: boolean;
  /** Enable the per-character "living" motion + hover interaction (default true). */
  animated?: boolean;
  alt?: string;
}

/**
 * Single-weight rounded geometric letterforms on a 0..200 × 0..64 grid.
 * Each glyph is a stroked path so terminals are round and every letter is an
 * independent, animatable node. Heights/positions tuned to read as one word.
 */
const STROKE = 13;

/** The animated USAM wordmark SVG (letters + teal arrow). */
function UsamMark({ animated }: { animated: boolean }) {
  const letterCls = (i: number) =>
    cn("usam-letter", animated && `usam-anim usam-anim-${i}`);
  return (
    <svg
      viewBox="0 0 232 64"
      className={cn("h-full w-auto overflow-visible", animated && "usam-svg")}
      fill="none"
      aria-hidden="true"
    >
      <g
        stroke="currentColor"
        strokeWidth={STROKE}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {/* U — a wide rounded cup */}
        <path className={letterCls(0)} d="M16 9 V34 a20 20 0 0 0 40 0 V9" />
        {/* S — a clean double curve */}
        <path
          className={letterCls(1)}
          d="M112 14 a16 13 0 0 0 -20 -2 a12.5 12.5 0 0 0 1 22 a12.5 12.5 0 0 1 1 22 a16 13 0 0 1 -20 -2"
        />
        {/* A — apex + crossbar */}
        <path className={letterCls(2)} d="M126 57 L145 9 L164 57" />
        <path className={letterCls(2)} d="M133.5 39 H156.5" />
        {/* M — four strokes */}
        <path className={letterCls(3)} d="M180 57 V11 L200 40 L220 11 V57" />
      </g>

      {/* Teal upward arrow rising through the U — the living accent, matching
          the reference (thick shaft + broad head sitting in the U's left well). */}
      <g
        className={cn("usam-arrow", animated && "usam-arrow-anim")}
        stroke="hsl(var(--secondary))"
        strokeWidth={STROKE}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      >
        <path d="M34 46 V7" />
        <path d="M19 22 L34 5 L49 22" />
      </g>
    </svg>
  );
}

/** The full USAM lockup — animated per-character wordmark. */
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
        "logo-lockup group inline-flex items-center select-none leading-none",
        variant === "onDark" ? "text-primary-foreground" : "text-foreground",
        className,
      )}
    >
      <UsamMark animated={animated} />
    </span>
  );
}

/**
 * LogoMark — the compact monogram tile (the U + teal arrow on a brand chip).
 * Used for the favicon, collapsed sidebar, and anywhere the full wordmark is
 * too wide.
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
        "logo-lockup group relative grid place-items-center rounded-xl h-8 w-8 shrink-0 overflow-hidden shadow-sm",
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
      {/* Just the U + arrow, cropped from the same drawing. */}
      <svg viewBox="0 0 64 64" className="h-[68%] w-[68%] overflow-visible text-primary-foreground" fill="none">
        <path
          d="M14 10 V36 a18 18 0 0 0 36 0 V10"
          stroke="currentColor"
          strokeWidth={STROKE}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <g
          className={cn("usam-arrow", animated && "usam-arrow-anim")}
          stroke="hsl(var(--secondary))"
          strokeWidth={STROKE}
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M32 44 V8" />
          <path d="M18 22 L32 6 L46 22" />
        </g>
      </svg>
      <span
        className="pointer-events-none absolute inset-0"
        style={{ background: "radial-gradient(80% 60% at 30% 15%, hsl(0 0% 100% / 0.16), transparent 70%)" }}
      />
    </span>
  );
}

/**
 * LogoLockup — the header brand anchor. Shows the animated wordmark.
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
