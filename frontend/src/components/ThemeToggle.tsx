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

export function LangToggle() {
  const { lang, toggleLang } = useTheme();

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        {/* <Button
          variant="ghost"
          size="sm"
          onClick={toggleLang}
          className="press-feedback gap-1 text-xs font-medium"
          aria-label={`Switch language to ${lang === "en" ? "Arabic" : "English"}`}
        >
          <Languages className="h-3.5 w-3.5" />
          {lang === "en" ? "عربي" : "EN"}
        </Button> */}
      </TooltipTrigger>
      <TooltipContent>{lang === "en" ? "Switch to Arabic" : "Switch to English"}</TooltipContent>
    </Tooltip>
  );
}
