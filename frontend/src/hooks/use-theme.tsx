import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";

export type Theme = "light" | "dark" | "night";
export type Dir = "ltr" | "rtl";
export type Lang = "en" | "ar";

interface ThemeContextValue {
  theme: Theme;
  setTheme: (t: Theme) => void;
  cycleTheme: (event?: React.MouseEvent) => void;
  dir: Dir;
  lang: Lang;
  toggleLang: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

const THEME_KEY = "usam-theme";
const LANG_KEY = "usam-lang";

const themeOrder: Theme[] = ["light", "dark", "night"];

/** Check if View Transition API is available */
function supportsViewTransitions(): boolean {
  return typeof document !== "undefined" && "startViewTransition" in document;
}

/** Check if user prefers reduced motion */
function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  root.classList.remove("light", "dark", "night");
  if (theme !== "light") root.classList.add(theme);
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === "undefined") return "light";
    return (localStorage.getItem(THEME_KEY) as Theme) || "light";
  });

  const [lang, setLang] = useState<Lang>(() => {
    if (typeof window === "undefined") return "en";
    return (localStorage.getItem(LANG_KEY) as Lang) || "en";
  });

  const dir: Dir = lang === "ar" ? "rtl" : "ltr";

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t);
    localStorage.setItem(THEME_KEY, t);
  }, []);

  /**
   * Cycle through themes with optional View Transition radial reveal.
   * Pass the click event to position the reveal origin at the toggle button.
   */
  const cycleTheme = useCallback((event?: React.MouseEvent) => {
    setThemeState((prev) => {
      const idx = themeOrder.indexOf(prev);
      const next = themeOrder[(idx + 1) % themeOrder.length];
      localStorage.setItem(THEME_KEY, next);

      // Set CSS custom properties for reveal origin
      if (event) {
        const x = event.clientX;
        const y = event.clientY;
        document.documentElement.style.setProperty(
          "--theme-toggle-x",
          `${x}px`
        );
        document.documentElement.style.setProperty(
          "--theme-toggle-y",
          `${y}px`
        );
      }

      // Use View Transition API for premium radial reveal
      if (supportsViewTransitions() && !prefersReducedMotion()) {
        (document as any).startViewTransition(() => {
          applyTheme(next);
        });
      } else {
        applyTheme(next);
      }

      return next;
    });
  }, []);

  const toggleLang = useCallback(() => {
    setLang((prev) => {
      const next = prev === "en" ? "ar" : "en";
      localStorage.setItem(LANG_KEY, next);
      return next;
    });
  }, []);

  useEffect(() => {
    applyTheme(theme);
    document.documentElement.setAttribute("dir", dir);
    document.documentElement.setAttribute("lang", lang);
  }, [theme, dir, lang]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, cycleTheme, dir, lang, toggleLang }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
