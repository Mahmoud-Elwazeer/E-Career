import { createContext, useContext, useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import { UserRound, Building2, Landmark } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTheme } from "@/hooks/use-theme";
import { cn } from "@/lib/utils";

/**
 * AudienceSwitcher — a landing-page segmented control that reframes the page for
 * Individuals vs Businesses. A "Governments" segment is shown honestly as
 * "coming soon" (disabled) rather than faked, because no government-specific
 * product exists yet — it is wired to drop in the moment one does, without any
 * fabricated content.
 */

export type Audience = "individuals" | "businesses" | "governments";

interface AudienceCtx {
  audience: Audience;
  setAudience: (a: Audience) => void;
}

const Ctx = createContext<AudienceCtx | null>(null);

export function AudienceProvider({ children }: { children: ReactNode }) {
  const [audience, setAudience] = useState<Audience>("individuals");
  return <Ctx.Provider value={{ audience, setAudience }}>{children}</Ctx.Provider>;
}

export function useAudience(): AudienceCtx {
  const ctx = useContext(Ctx);
  if (!ctx) return { audience: "individuals", setAudience: () => {} };
  return ctx;
}

const SEGMENTS: {
  key: Audience;
  en: string;
  ar: string;
  icon: typeof UserRound;
  available: boolean;
  /** dedicated forward page for this audience, if any */
  to?: string;
}[] = [
  { key: "individuals", en: "For Individuals", ar: "للأفراد", icon: UserRound, available: true, to: "/for-individuals" },
  { key: "businesses", en: "For Businesses", ar: "للشركات", icon: Building2, available: true, to: "/for-businesses" },
  { key: "governments", en: "For Governments", ar: "للحكومات", icon: Landmark, available: false },
];

/**
 * AudienceSwitcher
 * - default (tab mode): flips the landing page's audience framing in place.
 * - `linkMode`: clicking a segment navigates to that audience's dedicated
 *   page (used in the navbar / anywhere we want forward navigation).
 */
export function AudienceSwitcher({
  className = "",
  linkMode = false,
}: {
  className?: string;
  linkMode?: boolean;
}) {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const { audience, setAudience } = useAudience();
  const navigate = useNavigate();

  const handleSelect = (s: (typeof SEGMENTS)[number]) => {
    if (!s.available) return;
    if (linkMode && s.to) {
      navigate(s.to);
      return;
    }
    setAudience(s.key);
  };

  return (
    <div className={cn("flex justify-center", className)}>
      <div
        role="tablist"
        aria-label={isAr ? "اختر جمهورك" : "Choose your audience"}
        className="inline-flex items-center gap-1 rounded-full border border-border bg-surface-2/60 p-1 backdrop-blur-sm"
      >
        {SEGMENTS.map((s) => {
          const active = !linkMode && audience === s.key;
          const Icon = s.icon;
          return (
            <button
              key={s.key}
              role="tab"
              aria-selected={active}
              disabled={!s.available}
              onClick={() => handleSelect(s)}
              className={cn(
                "relative inline-flex items-center gap-1.5 rounded-full px-3.5 py-2 text-caption font-medium transition-colors",
                active ? "text-primary-foreground" : "text-muted-foreground hover:text-foreground",
                !s.available && "cursor-not-allowed opacity-55",
              )}
              title={!s.available ? (isAr ? "قريباً" : "Coming soon") : undefined}
            >
              {active && (
                <motion.span
                  layoutId="audience-pill"
                  className="absolute inset-0 rounded-full bg-primary"
                  transition={{ type: "spring", stiffness: 400, damping: 32 }}
                />
              )}
              <Icon className="relative h-3.5 w-3.5" />
              <span className="relative whitespace-nowrap">{isAr ? s.ar : s.en}</span>
              {!s.available && (
                <span className="relative ms-1 rounded-full bg-signal/20 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-signal-foreground">
                  {isAr ? "قريباً" : "Soon"}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
