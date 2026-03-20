import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { X, ChevronRight, ChevronLeft, MapPin, Briefcase, Globe, Wifi, Building2, Code2, Palette, Database, Megaphone, Stethoscope, GraduationCap, TrendingUp, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/use-theme";

const ONBOARDING_KEY = "usam_onboarding_complete";

/* ── Step data ── */
const CAREER_TRACKS = [
  { id: "tech", icon: Code2, en: "Tech & Engineering", ar: "التكنولوجيا والهندسة" },
  { id: "design", icon: Palette, en: "Design & Creative", ar: "التصميم والإبداع" },
  { id: "data", icon: Database, en: "Data & Analytics", ar: "البيانات والتحليلات" },
  { id: "marketing", icon: Megaphone, en: "Marketing & Sales", ar: "التسويق والمبيعات" },
  { id: "healthcare", icon: Stethoscope, en: "Healthcare", ar: "الرعاية الصحية" },
  { id: "finance", icon: TrendingUp, en: "Finance & Business", ar: "المالية والأعمال" },
];

const WORK_MODES = [
  { id: "remote", icon: Wifi, en: "Remote", ar: "عن بعد" },
  { id: "hybrid", icon: Globe, en: "Hybrid", ar: "هجين" },
  { id: "onsite", icon: Building2, en: "On-site", ar: "في المكتب" },
  { id: "any", icon: Briefcase, en: "No preference", ar: "لا تفضيل" },
];

const LOCATIONS = [
  { id: "uae", en: "UAE", ar: "الإمارات" },
  { id: "ksa", en: "Saudi Arabia", ar: "السعودية" },
  { id: "egypt", en: "Egypt", ar: "مصر" },
  { id: "jordan", en: "Jordan", ar: "الأردن" },
  { id: "qatar", en: "Qatar", ar: "قطر" },
  { id: "global", en: "Global / Anywhere", ar: "عالمي" },
];

interface OnboardingFlowProps {
  onComplete: (preferences: { track: string; mode: string; location: string }) => void;
}

/* ── Mini character SVG ── */
function MiniGuide({ phase }: { phase: "wave" | "think" | "point" | "celebrate" }) {
  const reduced = useReducedMotion();
  const P = { primary: "#0A3836", skin: "#D4C4B0", skinShadow: "#C4B09A", white: "#fff", neutral3: "#BECFCF", dark: "#1A1A1A", primaryLight: "#134E4A" };

  const armRotation = phase === "wave" ? [0, -25, 0] : phase === "point" ? -15 : phase === "celebrate" ? [0, -30, -15, -30, 0] : 0;

  return (
    <svg viewBox="0 0 120 160" fill="none" className="w-24 h-32 mx-auto" aria-hidden="true">
      <defs>
        <linearGradient id="ob-skin" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={P.skin} />
          <stop offset="100%" stopColor={P.skinShadow} />
        </linearGradient>
        <linearGradient id="ob-body" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={P.primaryLight} />
          <stop offset="100%" stopColor={P.primary} />
        </linearGradient>
      </defs>

      {/* Body */}
      <path d="M40 88 Q40 78 50 74 L70 74 Q80 78 80 88 L83 130 Q83 136 77 136 L43 136 Q37 136 37 130 Z" fill="url(#ob-body)" />
      {/* Collar */}
      <path d="M50 74 L60 82 L70 74" stroke={P.neutral3} strokeWidth="1.2" fill="none" strokeLinecap="round" />

      {/* Left arm */}
      <path d="M37 95 Q32 108 35 120" stroke={P.primary} strokeWidth="5" strokeLinecap="round" fill="none" />
      <circle cx="35" cy="120" r="3.5" fill="url(#ob-skin)" />

      {/* Right arm — animated */}
      <motion.g
        animate={{ rotate: armRotation }}
        transition={
          Array.isArray(armRotation)
            ? { duration: phase === "celebrate" ? 0.8 : 1.2, repeat: reduced ? 0 : phase === "wave" ? 2 : 0, ease: "easeInOut" }
            : { type: "spring", stiffness: 120, damping: 14 }
        }
        style={{ originX: "83px", originY: "95px" }}
      >
        <path d="M83 95 Q88 108 85 120" stroke={P.primary} strokeWidth="5" strokeLinecap="round" fill="none" />
        <circle cx="85" cy="120" r="3.5" fill="url(#ob-skin)" />
      </motion.g>

      {/* Head */}
      <ellipse cx="60" cy="56" rx="20" ry="24" fill="url(#ob-skin)" />
      {/* Hair */}
      <path d="M40 52 Q40 35 60 30 Q80 35 80 52 L80 46 Q80 34 60 30 Q40 34 40 46 Z" fill={P.primary} />
      {/* Cap detail */}
      <path d="M32 44 L88 44 L84 39 Q60 32 36 39 Z" fill={P.primaryLight} opacity="0.7" />

      {/* Glasses */}
      <rect x="44" y="50" width="11" height="9" rx="3" stroke={P.dark} strokeWidth="0.8" fill={`${P.neutral3}20`} />
      <rect x="65" y="50" width="11" height="9" rx="3" stroke={P.dark} strokeWidth="0.8" fill={`${P.neutral3}20`} />
      <path d="M55 54 Q60 52 65 54" stroke={P.dark} strokeWidth="0.7" fill="none" />

      {/* Eyes */}
      <motion.g
        animate={{ scaleY: phase === "celebrate" ? [1, 0.05, 1] : 1 }}
        transition={{ duration: 0.15, delay: phase === "celebrate" ? 0.3 : 0 }}
        style={{ originY: "55px" }}
      >
        <circle cx="50" cy="55" r="2" fill={P.dark} />
        <circle cx="70" cy="55" r="2" fill={P.dark} />
        <circle cx="50.8" cy="54.3" r="0.7" fill={P.white} opacity="0.8" />
        <circle cx="70.8" cy="54.3" r="0.7" fill={P.white} opacity="0.8" />
      </motion.g>

      {/* Mouth */}
      <motion.path
        stroke={P.dark}
        strokeWidth="1"
        strokeLinecap="round"
        fill="none"
        animate={{
          d: phase === "celebrate"
            ? "M52 66 Q60 73 68 66"
            : phase === "wave"
            ? "M53 66 Q60 71 67 66"
            : "M54 66 Q60 69 66 66",
        }}
        transition={{ duration: 0.3 }}
      />

      {/* Legs */}
      <rect x="47" y="136" width="8" height="16" rx="4" fill={P.dark} />
      <rect x="65" y="136" width="8" height="16" rx="4" fill={P.dark} />
      <ellipse cx="51" cy="153" rx="6" ry="3" fill={P.primary} />
      <ellipse cx="69" cy="153" rx="6" ry="3" fill={P.primary} />
    </svg>
  );
}

/* ── Main component ── */
export function OnboardingFlow({ onComplete }: OnboardingFlowProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState(0); // 0=track, 1=mode, 2=location
  const [track, setTrack] = useState("");
  const [mode, setMode] = useState("");
  const [location, setLocation] = useState("");
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const reduced = useReducedMotion();

  useEffect(() => {
    const done = localStorage.getItem(ONBOARDING_KEY);
    if (!done) {
      const timer = setTimeout(() => setIsOpen(true), 1800);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleComplete = useCallback(() => {
    localStorage.setItem(ONBOARDING_KEY, "true");
    setIsOpen(false);
    onComplete({ track, mode, location });
  }, [track, mode, location, onComplete]);

  const handleSkip = useCallback(() => {
    localStorage.setItem(ONBOARDING_KEY, "true");
    setIsOpen(false);
  }, []);

  const canNext = step === 0 ? !!track : step === 1 ? !!mode : !!location;

  const guidePhase = step === 0 ? "wave" : step === 1 ? "think" : step === 2 && !location ? "point" : "celebrate";

  const STEPS = [
    {
      title: isAr ? "ما المجال الذي يهمك؟" : "What field interests you?",
      subtitle: isAr ? "اختر مسارك المهني" : "Choose your career track",
    },
    {
      title: isAr ? "ما نمط العمل المفضل؟" : "Preferred work mode?",
      subtitle: isAr ? "حدد طريقة العمل المثالية" : "Pick your ideal work style",
    },
    {
      title: isAr ? "أين تريد العمل؟" : "Where do you want to work?",
      subtitle: isAr ? "اختر المنطقة المفضلة" : "Select your preferred region",
    },
  ];

  const slideVariants = {
    enter: (d: number) => ({
      x: reduced ? 0 : d > 0 ? 60 : -60,
      opacity: 0,
    }),
    center: { x: 0, opacity: 1 },
    exit: (d: number) => ({
      x: reduced ? 0 : d > 0 ? -60 : 60,
      opacity: 0,
    }),
  };

  const [slideDirection, setSlideDirection] = useState(1);

  const goNext = () => {
    if (step < 2) {
      setSlideDirection(1);
      setStep(step + 1);
    } else {
      handleComplete();
    }
  };

  const goBack = () => {
    if (step > 0) {
      setSlideDirection(-1);
      setStep(step - 1);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-foreground/40"
            style={{ backdropFilter: "blur(6px)" }}
            onClick={handleSkip}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />

          {/* Modal */}
          <motion.div
            className="relative w-full max-w-md bg-card rounded-2xl shadow-xl overflow-hidden border"
            initial={reduced ? { opacity: 0 } : { opacity: 0, scale: 0.92, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={reduced ? { opacity: 0 } : { opacity: 0, scale: 0.95, y: 10 }}
            transition={{ type: "spring", stiffness: 200, damping: 22 }}
            dir={dir}
          >
            {/* Header bar */}
            <div className="flex items-center justify-between px-5 pt-4 pb-0">
              {/* Progress dots */}
              <div className="flex gap-1.5">
                {[0, 1, 2].map((s) => (
                  <motion.div
                    key={s}
                    className="h-1.5 rounded-full"
                    animate={{
                      width: s === step ? 24 : 8,
                      backgroundColor: s <= step ? "hsl(var(--primary))" : "hsl(var(--border))",
                    }}
                    transition={{ duration: 0.3 }}
                  />
                ))}
              </div>
              <button
                onClick={handleSkip}
                className="text-muted-foreground hover:text-foreground transition-colors p-1 rounded-lg"
                aria-label="Skip onboarding"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Character */}
            <div className="pt-2 pb-1">
              <MiniGuide phase={guidePhase} />
            </div>

            {/* Step content */}
            <div className="px-6 pb-6 overflow-hidden" style={{ minHeight: 300 }}>
              <AnimatePresence mode="wait" custom={slideDirection}>
                <motion.div
                  key={step}
                  custom={slideDirection}
                  variants={slideVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{ duration: 0.25, ease: [0, 0, 0.2, 1] }}
                >
                  {/* Title */}
                  <div className="text-center mb-5">
                    <h3 className="text-heading-3 mb-1">{STEPS[step].title}</h3>
                    <p className="text-caption text-muted-foreground">{STEPS[step].subtitle}</p>
                  </div>

                  {/* Step 0: Career track */}
                  {step === 0 && (
                    <div className="grid grid-cols-2 gap-2.5">
                      {CAREER_TRACKS.map((t) => {
                        const selected = track === t.id;
                        return (
                          <motion.button
                            key={t.id}
                            type="button"
                            onClick={() => setTrack(t.id)}
                            className={`flex items-center gap-2.5 p-3 rounded-xl border text-start transition-all duration-200 ${
                              selected
                                ? "border-primary bg-primary-muted ring-1 ring-primary/20"
                                : "border-border hover:border-primary/30 bg-card"
                            }`}
                            whileTap={reduced ? {} : { scale: 0.97 }}
                          >
                            <div className={`rounded-lg p-2 ${selected ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"} transition-colors`}>
                              <t.icon className="h-4 w-4" />
                            </div>
                            <span className="text-body font-medium">{isAr ? t.ar : t.en}</span>
                            {selected && (
                              <motion.div
                                className="ms-auto"
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ type: "spring", stiffness: 500, damping: 25 }}
                              >
                                <Check className="h-3.5 w-3.5 text-primary" />
                              </motion.div>
                            )}
                          </motion.button>
                        );
                      })}
                    </div>
                  )}

                  {/* Step 1: Work mode */}
                  {step === 1 && (
                    <div className="grid grid-cols-2 gap-2.5">
                      {WORK_MODES.map((m) => {
                        const selected = mode === m.id;
                        return (
                          <motion.button
                            key={m.id}
                            type="button"
                            onClick={() => setMode(m.id)}
                            className={`flex flex-col items-center gap-2 p-4 rounded-xl border text-center transition-all duration-200 ${
                              selected
                                ? "border-primary bg-primary-muted ring-1 ring-primary/20"
                                : "border-border hover:border-primary/30 bg-card"
                            }`}
                            whileTap={reduced ? {} : { scale: 0.97 }}
                          >
                            <div className={`rounded-lg p-2.5 ${selected ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"} transition-colors`}>
                              <m.icon className="h-5 w-5" />
                            </div>
                            <span className="text-body font-medium">{isAr ? m.ar : m.en}</span>
                            {selected && (
                              <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ type: "spring", stiffness: 500, damping: 25 }}
                              >
                                <Check className="h-3.5 w-3.5 text-primary" />
                              </motion.div>
                            )}
                          </motion.button>
                        );
                      })}
                    </div>
                  )}

                  {/* Step 2: Location */}
                  {step === 2 && (
                    <div className="grid grid-cols-2 gap-2.5">
                      {LOCATIONS.map((loc) => {
                        const selected = location === loc.id;
                        return (
                          <motion.button
                            key={loc.id}
                            type="button"
                            onClick={() => setLocation(loc.id)}
                            className={`flex items-center gap-2.5 p-3 rounded-xl border text-start transition-all duration-200 ${
                              selected
                                ? "border-primary bg-primary-muted ring-1 ring-primary/20"
                                : "border-border hover:border-primary/30 bg-card"
                            }`}
                            whileTap={reduced ? {} : { scale: 0.97 }}
                          >
                            <MapPin className={`h-4 w-4 ${selected ? "text-primary" : "text-muted-foreground"}`} />
                            <span className="text-body font-medium">{isAr ? loc.ar : loc.en}</span>
                            {selected && (
                              <motion.div
                                className="ms-auto"
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                transition={{ type: "spring", stiffness: 500, damping: 25 }}
                              >
                                <Check className="h-3.5 w-3.5 text-primary" />
                              </motion.div>
                            )}
                          </motion.button>
                        );
                      })}
                    </div>
                  )}
                </motion.div>
              </AnimatePresence>

              {/* Navigation */}
              <div className="flex items-center justify-between mt-6">
                <button
                  type="button"
                  onClick={step > 0 ? goBack : handleSkip}
                  className="text-caption text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
                >
                  {step > 0 ? (
                    <>
                      {dir === "rtl" ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
                      {isAr ? "رجوع" : "Back"}
                    </>
                  ) : (
                    isAr ? "تخطّي" : "Skip"
                  )}
                </button>

                <Button
                  onClick={goNext}
                  disabled={!canNext}
                  size="sm"
                  className="rounded-xl px-6 press-feedback"
                >
                  {step === 2
                    ? (isAr ? "اعرض النتائج" : "Show results")
                    : (isAr ? "التالي" : "Next")}
                  {dir === "rtl" ? <ChevronLeft className="h-3.5 w-3.5 ms-1" /> : <ChevronRight className="h-3.5 w-3.5 ms-1" />}
                </Button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/** Hook to check and reset onboarding */
export function useOnboardingReset() {
  return () => localStorage.removeItem(ONBOARDING_KEY);
}
