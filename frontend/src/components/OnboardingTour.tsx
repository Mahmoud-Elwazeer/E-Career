import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { X, ArrowRight, ArrowLeft, Check } from "lucide-react";
import { RasheedAvatar } from "@/components/rashid/RasheedAvatar";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/use-theme";

/**
 * OnboardingTour — a REAL post-signup guided tour.
 *
 * Unlike the old preference modals, this actually navigates the user through the
 * key sections of the app and has Rasheed explain each one. It:
 *  - starts on the `usam:start-tour` event (fired after preference onboarding)
 *    or once automatically for authenticated users who haven't seen it,
 *  - routes to each section as the user advances (real navigation),
 *  - shows a bottom-anchored explanation card with Rasheed,
 *  - persists completion in `usam_tour_done`.
 */

const TOUR_KEY = "usam_tour_done";

interface Step {
  to: string;
  /** Warms the route's lazy chunk before we navigate, so "Next" is instant. */
  preload?: () => Promise<unknown>;
  en: { title: string; body: string };
  ar: { title: string; body: string };
}

const STEPS: Step[] = [
  {
    to: "/app/jobs",
    en: { title: "Find verified jobs", body: "Search roles aggregated from trusted sources — each links straight to the employer, no middlemen." },
    ar: { title: "اعثر على وظائف موثوقة", body: "ابحث في وظائف مجمّعة من مصادر موثوقة — كل وظيفة مرتبطة مباشرة بصاحب العمل بدون وسطاء." },
  },
  {
    to: "/app/recommendations",
    preload: () => import("@/pages/Recommendations"),
    en: { title: "Matches picked for you", body: "I rank roles against your profile and explain why each one fits." },
    ar: { title: "توصيات مختارة لك", body: "أرتّب الوظائف حسب ملفك وأشرح لماذا تناسبك كل واحدة." },
  },
  {
    to: "/app/resume",
    preload: () => import("@/pages/ResumeBuilder"),
    en: { title: "Build a standout CV", body: "Create and export an ATS-ready resume — I'll review and improve it with you." },
    ar: { title: "أنشئ سيرة مميزة", body: "أنشئ سيرة متوافقة مع أنظمة التوظيف — وسأراجعها وأحسّنها معك." },
  },
  {
    to: "/app/interviews",
    preload: () => import("@/pages/InterviewPractice"),
    en: { title: "Practice interviews", body: "Rehearse with an AI voice coach and get feedback before the real thing." },
    ar: { title: "تدرّب على المقابلات", body: "تدرّب مع مدرب صوتي ذكي واحصل على ملاحظات قبل المقابلة الحقيقية." },
  },
  {
    to: "/app/profile",
    preload: () => import("@/pages/ProfilePage"),
    en: { title: "Complete your profile", body: "Upload your CV and fill your profile so matches and Talent Score get sharper." },
    ar: { title: "أكمل ملفك", body: "ارفع سيرتك واملأ ملفك لتصبح التوصيات ونقاط الموهبة أدق." },
  },
];

export function OnboardingTour() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const reduced = useReducedMotion();
  const navigate = useNavigate();

  const [active, setActive] = useState(false);
  const [i, setI] = useState(0);

  const start = useCallback(() => {
    setI(0);
    setActive(true);
    navigate(STEPS[0].to);
  }, [navigate]);

  const finish = useCallback(() => {
    setActive(false);
    localStorage.setItem(TOUR_KEY, "true");
  }, []);

  const go = useCallback((next: number) => {
    if (next < 0 || next >= STEPS.length) return;
    setI(next);
    navigate(STEPS[next].to);
  }, [navigate]);

  // Warm the NEXT step's lazy route chunk while the user reads the current card,
  // so advancing navigates instantly instead of blocking on a chunk download.
  useEffect(() => {
    if (!active) return;
    STEPS[i + 1]?.preload?.().catch(() => {});
  }, [active, i]);

  // Explicit trigger from the preference flow.
  useEffect(() => {
    const handler = () => start();
    window.addEventListener("usam:start-tour", handler);
    return () => window.removeEventListener("usam:start-tour", handler);
  }, [start]);

  // NOTE: we intentionally do NOT auto-start the tour on a timer. Auto-starting
  // yanked authenticated users to /app/jobs from whatever page they were on.
  // The tour now starts ONLY from the explicit `usam:start-tour` event fired
  // right after preference onboarding completes (see OnboardingWrapper).

  if (!active) return null;
  const step = STEPS[i];
  const t = isAr ? step.ar : step.en;
  const isLast = i === STEPS.length - 1;

  return (
    <>
      {/* Dim scrim (non-blocking click closes). No backdrop-blur: blurring a
          full-screen layer over pages that are simultaneously mounting/fetching
          during tour navigation was a real jank source on lower-end devices. */}
      <motion.div
        className="fixed inset-0 z-[90] bg-black/40"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={finish}
        aria-hidden
      />

      {/* Coach card, bottom-anchored */}
      <div className="fixed inset-x-0 bottom-6 z-[91] flex justify-center px-4 pointer-events-none">
        <AnimatePresence mode="wait">
          <motion.div
            key={i}
            initial={reduced ? { opacity: 0 } : { opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduced ? { opacity: 0 } : { opacity: 0, y: -12 }}
            transition={{ type: "spring", stiffness: 260, damping: 24 }}
            className="pointer-events-auto w-full max-w-lg rounded-3xl border border-border bg-card p-5 shadow-2xl"
          >
            <div className="flex items-start gap-4">
              <RasheedAvatar expression="greeting" size={56} ring={false} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-caption font-medium text-primary">
                    {isAr ? `الخطوة ${i + 1} من ${STEPS.length}` : `Step ${i + 1} of ${STEPS.length}`}
                  </p>
                  <button onClick={finish} aria-label={isAr ? "إنهاء الجولة" : "End tour"} className="rounded-full p-1 text-muted-foreground hover:bg-accent">
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <h3 className="text-heading-3 font-semibold mt-1">{t.title}</h3>
                <p className="text-body text-muted-foreground mt-1">{t.body}</p>

                {/* Progress dots */}
                <div className="mt-4 flex items-center gap-1.5">
                  {STEPS.map((_, idx) => (
                    <span
                      key={idx}
                      className={`h-1.5 rounded-full transition-all ${idx === i ? "w-6 bg-primary" : "w-1.5 bg-border"}`}
                    />
                  ))}
                </div>

                <div className="mt-4 flex items-center justify-between gap-2">
                  <button onClick={finish} className="text-caption text-muted-foreground hover:text-foreground">
                    {isAr ? "تخطي" : "Skip tour"}
                  </button>
                  <div className="flex items-center gap-2">
                    {i > 0 && (
                      <Button variant="outline" size="sm" onClick={() => go(i - 1)} className="gap-1 press-feedback">
                        {isAr ? <ArrowRight className="h-3.5 w-3.5" /> : <ArrowLeft className="h-3.5 w-3.5" />}
                        {isAr ? "السابق" : "Back"}
                      </Button>
                    )}
                    <Button
                      size="sm"
                      onClick={() => (isLast ? finish() : go(i + 1))}
                      className="gap-1 press-feedback"
                    >
                      {isLast ? (
                        <>{isAr ? "تم" : "Done"} <Check className="h-3.5 w-3.5" /></>
                      ) : (
                        <>{isAr ? "التالي" : "Next"} {isAr ? <ArrowLeft className="h-3.5 w-3.5" /> : <ArrowRight className="h-3.5 w-3.5" />}</>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </>
  );
}
