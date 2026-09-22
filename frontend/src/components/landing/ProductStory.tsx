import { useRef } from "react";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";
import {
  Search, Sparkles, Send, Mic, TrendingUp, CheckCircle2, MapPin,
  Building2, ArrowRight, ArrowLeft,
} from "lucide-react";
import { ScrollReveal } from "@/components/motion";
import { useTheme } from "@/hooks/use-theme";
import { useAudience } from "./AudienceSwitcher";
import { cn } from "@/lib/utils";

/**
 * ProductStory — interactive, scroll-linked product demonstration. Instead of
 * generic marketing cards, each step reveals a realistic, design-system-styled
 * MOCK of the actual feature UI (job card, match breakdown, application status,
 * interview feedback), so a visitor understands the product by "experiencing"
 * the workflow. Content adapts to the selected audience (candidate vs employer
 * journey). Illustrative preview UI only — no fabricated statistics/testimonials.
 */

/* ── Small mock UI panels (design-system styled) ─────────────────────────── */

function MockJobCard({ isAr }: { isAr: boolean }) {
  return (
    <div className="paper-card p-4 w-full max-w-sm">
      <div className="flex items-start gap-3">
        <div className="icon-tile h-10 w-10 shrink-0"><Building2 className="h-5 w-5 text-primary" /></div>
        <div className="min-w-0 flex-1">
          <p className="text-body font-medium truncate">{isAr ? "مهندس واجهات أمامية" : "Frontend Engineer"}</p>
          <p className="text-caption text-muted-foreground flex items-center gap-1">
            <MapPin className="h-3 w-3" /> {isAr ? "دبي · عن بُعد" : "Dubai · Remote"}
          </p>
        </div>
        <span className="pill-tag pill-tag-signal shrink-0">{isAr ? "موثّق" : "Verified"}</span>
      </div>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {["React", "TypeScript", "UI"].map((t) => (
          <span key={t} className="pill-tag text-[10px] py-0.5">{t}</span>
        ))}
      </div>
    </div>
  );
}

function MockMatch({ isAr }: { isAr: boolean }) {
  const dims = [
    { en: "Skills", ar: "المهارات", v: 92 },
    { en: "Experience", ar: "الخبرة", v: 85 },
    { en: "Education", ar: "التعليم", v: 78 },
  ];
  return (
    <div className="paper-card p-4 w-full max-w-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-body font-medium flex items-center gap-1.5"><Sparkles className="h-4 w-4 text-signal" />{isAr ? "توافق" : "Match"}</span>
        <span className="font-mono-data text-heading-3 text-primary leading-none">94%</span>
      </div>
      <div className="space-y-2">
        {dims.map((d) => (
          <div key={d.en}>
            <div className="flex justify-between text-caption mb-0.5">
              <span className="text-muted-foreground">{isAr ? d.ar : d.en}</span>
              <span className="font-mono-data">{d.v}%</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
              <motion.div className="h-full rounded-full bg-primary" initial={{ width: 0 }} whileInView={{ width: `${d.v}%` }} viewport={{ once: true }} transition={{ duration: 0.8 }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MockApplication({ isAr }: { isAr: boolean }) {
  const steps = [
    { en: "Applied", ar: "تم التقديم", done: true },
    { en: "Reviewing", ar: "قيد المراجعة", done: true },
    { en: "Interview", ar: "مقابلة", done: false },
  ];
  return (
    <div className="paper-card p-4 w-full max-w-sm">
      <p className="text-body font-medium mb-3">{isAr ? "حالة الطلب" : "Application status"}</p>
      <ol className="space-y-2.5">
        {steps.map((s) => (
          <li key={s.en} className="flex items-center gap-2.5">
            <span className={cn("flex h-5 w-5 items-center justify-center rounded-full", s.done ? "bg-success/15 text-success" : "bg-muted text-muted-foreground")}>
              <CheckCircle2 className="h-3.5 w-3.5" />
            </span>
            <span className={cn("text-caption", s.done ? "text-foreground" : "text-muted-foreground")}>{isAr ? s.ar : s.en}</span>
          </li>
        ))}
      </ol>
      <div className="mt-3 pill-tag pill-tag-signal inline-flex text-[10px]">{isAr ? "مباشرة لصاحب العمل" : "Direct to employer"}</div>
    </div>
  );
}

function MockInterview({ isAr }: { isAr: boolean }) {
  const dims = [
    { en: "Clarity", ar: "الوضوح", v: 88 },
    { en: "Depth", ar: "العمق", v: 76 },
    { en: "Structure", ar: "التنظيم", v: 82 },
  ];
  return (
    <div className="paper-card p-4 w-full max-w-sm">
      <div className="flex items-center gap-1.5 mb-3">
        <Mic className="h-4 w-4 text-primary" />
        <span className="text-body font-medium">{isAr ? "تقييم المقابلة" : "Interview feedback"}</span>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {dims.map((d) => (
          <div key={d.en} className="text-center">
            <div className="font-mono-data text-heading-3 text-primary leading-none">{d.v}</div>
            <div className="text-[10px] text-muted-foreground mt-1">{isAr ? d.ar : d.en}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MockEmployerRank({ isAr }: { isAr: boolean }) {
  const cands = [
    { n: "A. Hassan", v: 91 },
    { n: "M. Salah", v: 84 },
    { n: "L. Adel", v: 79 },
  ];
  return (
    <div className="paper-card p-4 w-full max-w-sm">
      <p className="text-body font-medium mb-3">{isAr ? "ترتيب المرشحين" : "Ranked candidates"}</p>
      <ol className="space-y-2">
        {cands.map((c, i) => (
          <li key={c.n} className="flex items-center gap-2.5">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-[10px] font-semibold text-primary">{i + 1}</span>
            <span className="text-caption flex-1 truncate">{c.n}</span>
            <span className="font-mono-data text-caption font-semibold text-primary">{c.v}%</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

/* ── Step definitions per audience ───────────────────────────────────────── */

type Step = { icon: typeof Search; en: string; ar: string; descEn: string; descAr: string; mock: (p: { isAr: boolean }) => JSX.Element };

const CANDIDATE_STEPS: Step[] = [
  { icon: Search, en: "Search once", ar: "ابحث مرة واحدة", descEn: "One search covers verified jobs from every top source across MENA.", descAr: "بحث واحد يغطي وظائف موثقة من كل المصادر الكبرى في المنطقة.", mock: MockJobCard },
  { icon: Sparkles, en: "See why you match", ar: "اعرف سبب توافقك", descEn: "Rasheed explains each match with real skill, experience and education signals.", descAr: "يشرح رشيد كل توافق بإشارات حقيقية للمهارات والخبرة والتعليم.", mock: MockMatch },
  { icon: Send, en: "Apply direct", ar: "قدّم مباشرة", descEn: "Apply straight to the employer's source — track every application's status.", descAr: "قدّم مباشرة لمصدر صاحب العمل — وتابع حالة كل طلب.", mock: MockApplication },
  { icon: Mic, en: "Practise & improve", ar: "تدرّب وتحسّن", descEn: "Rehearse interviews with an AI coach and get scored, actionable feedback.", descAr: "تدرّب على المقابلات مع مدرب ذكي واحصل على تقييم قابل للتنفيذ.", mock: MockInterview },
];

const EMPLOYER_STEPS: Step[] = [
  { icon: Send, en: "Post a verified role", ar: "انشر وظيفة موثقة", descEn: "Publish to a candidate base — your apply link stays on your own domain.", descAr: "انشر لقاعدة مرشحين — ويبقى رابط التقديم على نطاقك الرسمي.", mock: MockJobCard },
  { icon: Sparkles, en: "Auto-rank candidates", ar: "ترتيب تلقائي للمرشحين", descEn: "Rank applicants by skill, experience and fit — with knockout rules and evidence.", descAr: "رتّب المتقدمين حسب المهارة والخبرة والملاءمة — بقواعد استبعاد وأدلة.", mock: MockEmployerRank },
  { icon: TrendingUp, en: "Search the talent pool", ar: "ابحث في قاعدة المواهب", descEn: "Build pools and surface the strongest candidates against each job.", descAr: "أنشئ قوائم مواهب واستخرج أقوى المرشحين لكل وظيفة.", mock: MockMatch },
  { icon: CheckCircle2, en: "Hire faster", ar: "وظّف أسرع", descEn: "Move from shortlist to offer with the intelligence surfaced for every candidate.", descAr: "انتقل من القائمة المختصرة إلى العرض بذكاء مُتاح لكل مرشح.", mock: MockApplication },
];

/* ── The section ─────────────────────────────────────────────────────────── */

export function ProductStory() {
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const reduced = useReducedMotion();
  const { audience } = useAudience();
  const containerRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({ target: containerRef, offset: ["start center", "end center"] });
  const lineScale = useTransform(scrollYProgress, [0, 1], [0, 1]);

  const steps = audience === "businesses" ? EMPLOYER_STEPS : CANDIDATE_STEPS;

  return (
    <section className="section-y section-band">
      <div className="container">
        <ScrollReveal>
          <div className="flex flex-col items-center text-center mb-12">
            <span className="eyebrow-mono mb-4">{isAr ? "كيف يعمل" : "SEE IT WORK"}</span>
            <h2 className="text-display-serif max-w-2xl">
              {audience === "businesses"
                ? (isAr ? <>من النشر إلى <span className="serif-accent text-primary">التوظيف</span></> : <>From posting to <span className="serif-accent text-primary">hire</span></>)
                : (isAr ? <>من البحث إلى <span className="serif-accent text-primary">النمو</span></> : <>From search to <span className="serif-accent text-primary">growth</span></>)}
            </h2>
            <p className="text-body-lg text-muted-foreground mt-4 max-w-xl">
              {audience === "businesses"
                ? (isAr ? "شاهد رحلة التوظيف الحقيقية داخل المنصة." : "Watch the real hiring workflow inside the platform.")
                : (isAr ? "شاهد رحلتك المهنية الحقيقية خطوة بخطوة." : "Watch your real career workflow, step by step.")}
            </p>
          </div>
        </ScrollReveal>

        {/* Timeline */}
        <div ref={containerRef} className="relative mx-auto max-w-4xl">
          {/* Progress rail (desktop) */}
          <div className="pointer-events-none absolute start-[19px] top-0 bottom-0 hidden w-px bg-border md:block" aria-hidden>
            <motion.div className="absolute inset-x-0 top-0 w-px origin-top bg-primary" style={{ scaleY: reduced ? 1 : lineScale, height: "100%" }} />
          </div>

          <div className="space-y-10 md:space-y-14">
            {steps.map((step, i) => {
              const Mock = step.mock;
              const Icon = step.icon;
              return (
                <motion.div
                  key={`${audience}-${step.en}`}
                  initial={reduced ? { opacity: 0 } : { opacity: 0, y: 28 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.4 }}
                  transition={{ duration: 0.5, delay: (i % 2) * 0.05 }}
                  className="relative grid gap-5 md:grid-cols-[40px_1fr_auto] md:items-center"
                >
                  {/* Node */}
                  <div className="hidden md:flex">
                    <span className="relative z-10 flex h-10 w-10 items-center justify-center rounded-full border border-primary/20 bg-card">
                      <Icon className="h-4 w-4 text-primary" />
                    </span>
                  </div>
                  {/* Copy */}
                  <div>
                    <span className="md:hidden icon-tile mb-3 inline-flex h-9 w-9"><Icon className="h-4 w-4 text-primary" /></span>
                    <h3 className="text-heading-3 font-semibold mb-1.5">
                      <span className="font-mono-data text-caption text-primary me-2">{String(i + 1).padStart(2, "0")}</span>
                      {isAr ? step.ar : step.en}
                    </h3>
                    <p className="text-body text-muted-foreground max-w-md">{isAr ? step.descAr : step.descEn}</p>
                  </div>
                  {/* Live mock */}
                  <div className="md:justify-self-end">
                    <Mock isAr={isAr} />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* CTA under the story */}
        <ScrollReveal>
          <div className="mt-12 text-center">
            <a
              href={audience === "businesses" ? "/login" : "#platform"}
              className="inline-flex items-center gap-2 rounded-full bg-primary px-6 h-12 text-body font-medium text-primary-foreground shadow-sm press-feedback"
            >
              {audience === "businesses"
                ? (isAr ? "ابدأ التوظيف" : "Start hiring")
                : (isAr ? "استكشف الأدوات" : "Explore the tools")}
              <Arrow className="h-4 w-4" />
            </a>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
