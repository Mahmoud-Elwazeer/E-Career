import { Sun, Moon, Stars, Languages } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme, Theme } from "@/hooks/use-theme";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const themeIcons: Record<Theme, React.ElementType> = {
  light: Sun,
  dark: Moon,
  night: Stars,
};

const themeLabels: Record<Theme, string> = {
  light: "Light",
  dark: "Dark",
  night: "Night",
};

export function ThemeToggle() {
  const { theme, cycleTheme } = useTheme();
  const Icon = themeIcons[theme];

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          onClick={(e) => cycleTheme(e)}
          className="press-feedback"
          aria-label={`Switch theme. Current: ${themeLabels[theme]}`}
        >
          <Icon className="h-4 w-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent>{themeLabels[theme]} mode</TooltipContent>
    </Tooltip>
  );
}

interface LangToggleProps {
  /**
   * Called right after the language actually changes. Used by the mobile
   * hamburger Sheet to close itself immediately — the Sheet's `side` is
   * tied to the active language (left for RTL, right for LTR), so leaving
   * it open while the language flips mid-animation detaches/repositions
   * the Sheet's own DOM nodes. Closing it as part of the same action
   * avoids that race instead of fighting it with timeouts elsewhere.
   */
  onToggled?: () => void;
}

export function LangToggle({ onToggled }: LangToggleProps = {}) {
  const { lang, toggleLang } = useTheme();

  const handleClick = () => {
    toggleLang();
    onToggled?.();
  };

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleClick}
          className="press-feedback gap-1 text-xs font-medium"
          aria-label={`Switch language to ${lang === "en" ? "Arabic" : "English"}`}
        >
          <Languages className="h-3.5 w-3.5" />
          {lang === "en" ? "عربي" : "EN"}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{lang === "en" ? "Switch to Arabic" : "Switch to English"}</TooltipContent>
    </Tooltip>
  );
}
