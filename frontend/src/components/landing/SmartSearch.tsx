import { useState, useRef, useEffect, useMemo } from "react";
import { Search, Clock, X, MapPin, Sparkles } from "lucide-react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { TypewriterPlaceholder } from "@/components/motion";

import { useTheme } from "@/hooks/use-theme";
import { useRecentSearches } from "@/hooks/use-recent-searches";
import { MOTION } from "@/lib/motion-tokens";

interface SmartSearchProps {
  query: string;
  setQuery: (q: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  onFocusChange?: (focused: boolean) => void;
  onHoverSearch?: (hovering: boolean) => void;
  onClickSearch?: () => void;
}

const JOB_TITLES = ["Frontend Developer","Data Analyst","UX Designer","Backend Engineer","Product Manager","DevOps Engineer","Machine Learning Engineer","Financial Analyst","Sales Executive","QA Engineer"];
const LOCATIONS = ["Dubai, UAE","Cairo, Egypt","Amman, Jordan","Riyadh, KSA","Doha, Qatar","Remote","Abu Dhabi, UAE","Beirut, Lebanon"];

const SUGGESTED_CHIPS = [
  { en: "Remote", ar: "عن بعد" },
  { en: "React", ar: "React" },
  { en: "Dubai", ar: "دبي" },
  { en: "Data Analyst", ar: "محلل بيانات" },
];

export function SmartSearch({ query, setQuery, onSubmit, onFocusChange, onHoverSearch, onClickSearch }: SmartSearchProps) {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const reduced = useReducedMotion();
  const [focused, setFocusedState] = useState(false);
  const [hoveredSuggestion, setHoveredSuggestion] = useState<string | null>(null);
  const { recentSearches, addRecentSearch, clearRecentSearches } = useRecentSearches();
  const wrapperRef = useRef<HTMLFormElement>(null);

  const setFocused = (v: boolean) => {
    setFocusedState(v);
    onFocusChange?.(v);
  };

  // Combine title + location suggestions
  const suggestions = useMemo(() => {
    if (query.length < 2) return [];
    const q = query.toLowerCase();
    const titleMatches = JOB_TITLES.filter((t) => t.toLowerCase().includes(q)).slice(0, 4);
    const locMatches = LOCATIONS.filter((l) => l.toLowerCase().includes(q)).slice(0, 2);
    return [...titleMatches.map((t) => ({ text: t, type: "role" as const })), ...locMatches.map((l) => ({ text: l, type: "location" as const }))].slice(0, 5);
  }, [query]);

  // Preview job data for hovered suggestion
  const previewJob = useMemo(() => {
    if (!hoveredSuggestion) return null;
    // Static preview — no live lookup in landing mode
    if (!hoveredSuggestion) return null;
    return null;
  }, [hoveredSuggestion]);

  const showDropdown = focused && (suggestions.length > 0 || (query.length < 2 && recentSearches.length > 0));

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setFocused(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    if (query.trim()) addRecentSearch(query.trim());
    onClickSearch?.();
    onSubmit(e);
  };

  const selectSuggestion = (text: string) => {
    setQuery(text);
    addRecentSearch(text);
    setFocused(false);
  };

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="flex gap-2 max-w-lg" ref={wrapperRef}>
        <div className="relative flex-1">
          <Search className="absolute start-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground z-10" />
          <div className="relative">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setFocused(true)}
              className={`ps-11 bg-card text-card-foreground border-0 h-13 shadow-lg text-body-lg rounded-xl transition-shadow duration-200 ${
                focused ? "ring-2 ring-secondary/50 shadow-xl" : ""
              }`}
            />
            {!query && (
              <div className="absolute inset-0 flex items-center ps-11 pointer-events-none text-muted-foreground text-body-lg">
                <TypewriterPlaceholder
                  phrases={
                    isAr
                      ? ["مطور React", "مدير تسويق", "وظائف عن بعد في دبي", "محلل بيانات"]
                      : ["React Developer", "Marketing Manager", "Remote jobs in Dubai", "Data Analyst"]
                  }
                  typeSpeed={55}
                  deleteSpeed={25}
                  pauseDuration={2200}
                />
              </div>
            )}
          </div>

          {/* Premium dropdown */}
          <AnimatePresence>
            {showDropdown && (
              <motion.div
                initial={reduced ? { opacity: 0 } : { opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: MOTION.duration.fast }}
                className="absolute top-full mt-1.5 inset-x-0 bg-card border rounded-xl shadow-xl z-20 overflow-hidden"
              >
                {/* Recent searches (when empty query) */}
                {query.length < 2 && recentSearches.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between px-4 pt-3 pb-1.5">
                      <span className="text-caption text-muted-foreground font-medium flex items-center gap-1.5">
                        <Clock className="h-3 w-3" />
                        {isAr ? "بحث سابق" : "Recent"}
                      </span>
                      <button
                        type="button"
                        onClick={clearRecentSearches}
                        className="text-caption text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {isAr ? "مسح" : "Clear"}
                      </button>
                    </div>
                    {recentSearches.map((term) => (
                      <button
                        key={term}
                        type="button"
                        onClick={() => selectSuggestion(term)}
                        className="flex items-center gap-2.5 w-full px-4 py-2 text-body text-start hover:bg-accent transition-colors"
                      >
                        <Clock className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                        <span>{term}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Autocomplete suggestions */}
                {suggestions.length > 0 && (
                  <div>
                    {query.length >= 2 && (
                      <div className="px-4 pt-3 pb-1.5">
                        <span className="text-caption text-muted-foreground font-medium flex items-center gap-1.5">
                          <Sparkles className="h-3 w-3" />
                          {isAr ? "اقتراحات" : "Suggestions"}
                        </span>
                      </div>
                    )}
                    <div className="flex">
                      <div className="flex-1">
                        {suggestions.map((s) => (
                          <button
                            key={s.text}
                            type="button"
                            onClick={() => selectSuggestion(s.text)}
                            onMouseEnter={() => setHoveredSuggestion(s.text)}
                            onMouseLeave={() => setHoveredSuggestion(null)}
                            className="flex items-center gap-2.5 w-full px-4 py-2.5 text-body text-start hover:bg-accent transition-colors"
                          >
                            {s.type === "location" ? (
                              <MapPin className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                            ) : (
                              <Search className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                            )}
                            <span>{s.text}</span>
                            {s.type === "location" && (
                              <span className="text-caption text-muted-foreground ms-auto">{isAr ? "موقع" : "Location"}</span>
                            )}
                          </button>
                        ))}
                      </div>

                      {/* Quick preview panel */}
                      <AnimatePresence>
                        {previewJob && (
                          <motion.div
                            initial={{ opacity: 0, width: 0 }}
                            animate={{ opacity: 1, width: 200 }}
                            exit={{ opacity: 0, width: 0 }}
                            transition={{ duration: MOTION.duration.fast }}
                            className="border-s bg-accent/30 overflow-hidden"
                          >
                            <div className="p-3 w-[200px]">
                              <div className="flex items-center gap-2 mb-2">
                                {previewJob.logo && (
                                  <img src={previewJob.logo} alt="" className="h-8 w-8 rounded-md object-cover" />
                                )}
                                <div className="min-w-0">
                                  <p className="text-caption font-medium truncate">{previewJob.title}</p>
                                  <p className="text-caption text-muted-foreground truncate">{previewJob.company}</p>
                                </div>
                              </div>
                              <div className="flex items-center gap-1 text-caption text-muted-foreground">
                                <MapPin className="h-3 w-3 shrink-0" />
                                <span className="truncate">{previewJob.location}</span>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        <Button
          type="submit"
          size="lg"
          className="bg-secondary text-secondary-foreground hover:bg-secondary/90 h-13 px-7 press-feedback rounded-xl font-medium"
          onMouseEnter={() => onHoverSearch?.(true)}
          onMouseLeave={() => onHoverSearch?.(false)}
        >
          {isAr ? "بحث" : "Search"}
        </Button>
      </form>

      {/* Suggested chips */}
      <div className="flex flex-wrap gap-2 max-w-lg">
        {SUGGESTED_CHIPS.map((chip) => (
          <button
            key={chip.en}
            type="button"
            onClick={() => {
              setQuery(isAr ? chip.ar : chip.en);
            }}
            className="px-3 py-1 text-caption rounded-full border border-primary-foreground/20 text-primary-foreground/70 hover:text-primary-foreground hover:border-primary-foreground/40 hover:bg-primary-foreground/5 transition-all"
          >
            {isAr ? chip.ar : chip.en}
          </button>
        ))}
      </div>
    </div>
  );
}
