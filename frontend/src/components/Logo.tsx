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
const STROKE = 17;

/** The animated USAM wordmark SVG (bold rounded letters + teal arrow).
 *
 * Letters are heavy, round-terminal strokes so the wordmark reads as a solid,
 * modern mark (an original geometry — not a trace of any reference file). Each
 * letter is its own path so it animates independently. */
function UsamMark({ animated }: { animated: boolean }) {
  const letterCls = (i: number) =>
    cn("usam-letter", animated && `usam-anim usam-anim-${i}`);
  return (
    <svg
      viewBox="0 0 236 68"
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
        {/* U — a wide, heavy rounded cup */}
        <path className={letterCls(0)} d="M18 12 V34 a22 22 0 0 0 44 0 V12" />
        {/* S — a bold clean double curve */}
        <path
          className={letterCls(1)}
          d="M118 18 a17 14 0 0 0 -22 -3 a13.5 13.5 0 0 0 1 24 a13.5 13.5 0 0 1 1 24 a17 14 0 0 1 -22 -3"
        />
        {/* A — apex + crossbar */}
        <path className={letterCls(2)} d="M130 58 L150 12 L170 58" />
        <path className={letterCls(2)} d="M138 40 H162" />
        {/* M — four strokes */}
        <path className={letterCls(3)} d="M186 58 V14 L207 42 L228 14 V58" />
      </g>

      {/* Teal upward arrow rising through the U — the living accent. */}
      <g
        className={cn("usam-arrow", animated && "usam-arrow-anim")}
        stroke="hsl(var(--secondary))"
        strokeWidth={STROKE}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      >
        <path d="M40 48 V9" />
        <path d="M22 26 L40 7 L58 26" />
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
      <svg viewBox="0 0 68 68" className="h-[70%] w-[70%] overflow-visible text-primary-foreground" fill="none">
        <path
          d="M16 12 V36 a18 18 0 0 0 36 0 V12"
          stroke="currentColor"
          strokeWidth={16}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <g
          className={cn("usam-arrow", animated && "usam-arrow-anim")}
          stroke="hsl(var(--secondary))"
          strokeWidth={16}
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M34 46 V10" />
          <path d="M19 26 L34 9 L49 26" />
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
