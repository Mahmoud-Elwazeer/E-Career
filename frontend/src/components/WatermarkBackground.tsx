import { useEffect, useRef, useCallback, useState } from "react";
import { useReducedMotion } from "framer-motion";
import { useTheme, type Theme } from "@/hooks/use-theme";

type WatermarkVariant = "drift" | "shimmer" | "tilt";

interface WatermarkBackgroundProps {
  /** Animation variant */
  variant?: WatermarkVariant;
  /** Override opacity (otherwise theme-driven) */
  opacity?: number;
  /** Use currentColor instead of foreground (for colored sections like hero) */
  inheritColor?: boolean;
  /** Pause animations (e.g. while user is typing) */
  paused?: boolean;
  /** Additional class */
  className?: string;
}

/* ── Theme opacity map ── */
const THEME_OPACITY: Record<Theme, number> = {
  light: 0.03,
  dark: 0.04,
  night: 0.025,
};

const SHIMMER_PEAK: Record<Theme, number> = {
  light: 0.05,
  dark: 0.07,
  night: 0.04,
};

/* ── SVG data-uri tile generator ── */
function createWatermarkTile(color: string, fontSize: number = 48): string {
  const w = fontSize * 4.5;
  const h = fontSize * 2.4;
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
      <text x="0" y="${fontSize * 0.85}" font-family="Poppins,sans-serif" font-weight="700" font-size="${fontSize}" fill="${color}" letter-spacing="${fontSize * 0.6}">US US US</text>
      <text x="${fontSize * 1.3}" y="${fontSize * 2.05}" font-family="Poppins,sans-serif" font-weight="700" font-size="${fontSize}" fill="${color}" letter-spacing="${fontSize * 0.6}">US US US</text>
    </svg>
  `.trim().replace(/\n\s*/g, "");

  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`;
}

/**
 * Animated "US" watermark background layer.
 * 
 * Variants:
 * - `drift`: Slow diagonal parallax translation (CSS keyframes)
 * - `shimmer`: Luminosity wave sweep across pattern (CSS gradient overlay)
 * - `tilt`: Cursor/gyro responsive parallax offset (rAF)
 * 
 * All variants are GPU-composited (transform/opacity only), respect
 * reduced-motion, and adapt opacity per Light/Dark/Night theme.
 */
export function WatermarkBackground({
  variant = "drift",
  opacity: opacityOverride,
  inheritColor = false,
  paused = false,
  className = "",
}: WatermarkBackgroundProps) {
  const { theme } = useTheme();
  const reduced = useReducedMotion();
  const tiltRef = useRef<HTMLDivElement>(null);
  const rafRef = useRef<number>();
  const mousePos = useRef({ x: 0, y: 0 });
  const currentOffset = useRef({ x: 0, y: 0 });

  const baseOpacity = opacityOverride ?? THEME_OPACITY[theme];
  const shimmerPeak = SHIMMER_PEAK[theme];

  // Color: use a neutral that works as SVG fill
  const color = inheritColor
    ? "currentColor"
    : theme === "light"
    ? "%230A3836"
    : "%23BECFCF";

  const tileUrl = createWatermarkTile(inheritColor ? "currentColor" : (theme === "light" ? "%230A3836" : "%23BECFCF"));

  /* ── Tilt: cursor tracking via rAF ── */
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (reduced) return;
    const rect = tiltRef.current?.parentElement?.getBoundingClientRect();
    if (!rect) return;
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    // Normalize to -1..1
    mousePos.current = {
      x: ((e.clientX - cx) / (rect.width / 2)) * 8,
      y: ((e.clientY - cy) / (rect.height / 2)) * 8,
    };
  }, [reduced]);

  useEffect(() => {
    if (variant !== "tilt" || reduced) return;

    const el = tiltRef.current?.parentElement;
    if (!el) return;

    el.addEventListener("mousemove", handleMouseMove, { passive: true });

    function tick() {
      // lerp toward target
      currentOffset.current.x += (mousePos.current.x - currentOffset.current.x) * 0.05;
      currentOffset.current.y += (mousePos.current.y - currentOffset.current.y) * 0.05;

      if (tiltRef.current) {
        tiltRef.current.style.transform = `translate3d(${currentOffset.current.x}px, ${currentOffset.current.y}px, 0)`;
      }
      rafRef.current = requestAnimationFrame(tick);
    }

    rafRef.current = requestAnimationFrame(tick);

    // Pause on hidden
    function onVisChange() {
      if (document.hidden && rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      } else if (!document.hidden) {
        rafRef.current = requestAnimationFrame(tick);
      }
    }
    document.addEventListener("visibilitychange", onVisChange);

    return () => {
      el.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("visibilitychange", onVisChange);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [variant, reduced, handleMouseMove]);

  /* ── Inline styles for the pattern layer ── */
  const patternStyle: React.CSSProperties = {
    position: "absolute",
    inset: variant === "drift" ? "-20%" : 0,
    backgroundImage: tileUrl,
    backgroundRepeat: "repeat",
    backgroundSize: "auto",
    opacity: baseOpacity,
    pointerEvents: "none",
    zIndex: 0,
    willChange: reduced ? "auto" : "transform",
    ...(inheritColor ? { color: "inherit" } : {}),
  };

  /* ── Drift: CSS animation via inline keyframes ── */
  const driftAnimation = !reduced && variant === "drift"
    ? {
        animation: "watermark-drift 60s linear infinite",
        animationPlayState: paused ? "paused" as const : "running" as const,
      }
    : {};

  /* ── Shimmer overlay ── */
  const shimmerOverlayStyle: React.CSSProperties | null =
    variant === "shimmer" && !reduced
      ? {
          position: "absolute" as const,
          inset: 0,
          background: `linear-gradient(
            110deg,
            transparent 30%,
            hsl(var(--primary) / ${shimmerPeak - baseOpacity}) 50%,
            transparent 70%
          )`,
          backgroundSize: "200% 100%",
          animation: "watermark-shimmer 4s ease-in-out infinite",
          animationPlayState: paused ? "paused" as const : "running" as const,
          pointerEvents: "none" as const,
          zIndex: 0,
          mixBlendMode: "screen" as const,
        }
      : null;

  return (
    <>
      {/* Inject keyframes */}
      <style>{`
        @keyframes watermark-drift {
          from { transform: translate3d(0, 0, 0); }
          to { transform: translate3d(-50%, -50%, 0); }
        }
        @keyframes watermark-shimmer {
          0%, 100% { background-position: 200% center; }
          50% { background-position: -200% center; }
        }
        @media (prefers-reduced-motion: reduce) {
          .watermark-layer {
            animation: none !important;
          }
        }
      `}</style>
      <div
        ref={tiltRef}
        className={`watermark-layer ${className}`}
        style={{ ...patternStyle, ...driftAnimation }}
        aria-hidden="true"
      />
      {shimmerOverlayStyle && (
        <div
          className="watermark-layer"
          style={shimmerOverlayStyle}
          aria-hidden="true"
        />
      )}
    </>
  );
}
