import { Link } from "react-router-dom";
import {
  MessageCircle, FileText, Mic, Sparkles, Target, ShieldCheck,
  ArrowRight, ArrowLeft, Building2, UserRound,
} from "lucide-react";
import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/motion";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";

/**
 * FeatureShowcase — surfaces the flagship product features that the landing
 * previously never mentioned (Rasheed AI, Resume Builder, Interview prep,
 * personalized recommendations, Talent Score, verification), plus a clear
 * dual-audience split (Individuals vs Employers) with real CTAs.
 */

interface FeatureCard {
  icon: React.ComponentType<{ className?: string }>;
  en: string; ar: string;
  descEn: string; descAr: string;
  to: string;
  span?: boolean; // wide (2-col) bento tile
}

export function FeatureShowcase() {
  const { lang, dir } = useTheme();
  const { isAuthenticated } = useAuth();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const gate = (to: string) => (isAuthenticated ? to : "/login");
  const gateState = (to: string) => (isAuthenticated ? {} : { state: { from: to } });

  const features: FeatureCard[] = [
    { icon: MessageCircle, en: "Rasheed — your AI career coach", ar: "رشيد — مساعدك المهني", descEn: "Chat 24/7 for CV feedback, job matches, cover letters and interview prep — grounded in your real profile.", descAr: "دردش على مدار الساعة للحصول على مراجعة سيرتك، وظائف مطابقة، ورسائل تقديم وتحضير للمقابلات.", to: "/app/rashid", span: true },
    { icon: FileText, en: "Resume Builder", ar: "منشئ السيرة الذاتية", descEn: "Craft and export an ATS-ready CV.", descAr: "أنشئ سيرة متوافقة مع أنظمة التوظيف.", to: "/app/resume" },
    { icon: Mic, en: "Interview Practice", ar: "تدريب المقابلات", descEn: "Rehearse with an AI voice coach.", descAr: "تدرّب بمساعدة مدرب صوتي ذكي.", to: "/app/interviews" },
    { icon: Sparkles, en: "Personalized matches", ar: "توصيات مخصصة", descEn: "See jobs picked for your skills, with reasons.", descAr: "وظائف مختارة لمهاراتك مع الأسباب.", to: "/app/recommendations" },
    { icon: Target, en: "Talent Score", ar: "نقاط الموهبة", descEn: "Measure and grow your employability.", descAr: "قِس جاهزيتك المهنية وطوّرها.", to: "/app/talent-score" },
    { icon: ShieldCheck, en: "Verified direct-apply", ar: "تقديم مباشر موثّق", descEn: "Every job links to the real employer source — no aggregator middlemen.", descAr: "كل وظيفة مرتبطة بالمصدر الأصلي لصاحب العمل — بدون وسطاء.", to: "/app/jobs", span: true },
  ];

  return (
    <section id="platform" className="section-y scroll-mt-20">
      <div className="container">
        <ScrollReveal>
          <div className="flex flex-col items-center text-center mb-12">
            <span className="eyebrow-mono mb-4">{isAr ? "منصة متكاملة" : "ONE PLATFORM"}</span>
            <h2 className="text-display-serif max-w-2xl">
              {isAr ? (
                <>أكثر من مجرد <span className="serif-accent text-primary">بحث</span> عن وظيفة</>
              ) : (
                <>More than a job search — a <span className="serif-accent text-primary">career OS</span></>
              )}
            </h2>
            <p className="text-body-lg text-muted-foreground mt-4 max-w-xl">
              {isAr
                ? "أدوات مدعومة بالذكاء الاصطناعي ترافقك من البحث حتى التوظيف والنمو."
                : "AI-powered tools that guide you from search to hire to growth."}
            </p>
          </div>
        </ScrollReveal>

        {/* Bento feature grid */}
        <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-5" staggerDelay={0.06}>
          {features.map((f) => (
            <StaggerItem key={f.en} className={f.span ? "md:col-span-2 lg:col-span-1 xl:col-span-1" : ""}>
              <Link
                to={gate(f.to)}
                {...gateState(f.to)}
                className={`card-premium card-accent-top group flex h-full flex-col p-6 ${f.span ? "md:col-span-2" : ""}`}
              >
                <span className="icon-tile mb-4 h-12 w-12">
                  <f.icon className="h-6 w-6 text-primary" />
                </span>
                <h3 className="text-heading-3 font-semibold mb-2 group-hover:text-primary transition-colors">
                  {isAr ? f.ar : f.en}
                </h3>
                <p className="text-body text-muted-foreground leading-relaxed">
                  {isAr ? f.descAr : f.descEn}
                </p>
                <span className="mt-4 inline-flex items-center gap-1 text-caption font-medium text-primary">
                  {isAr ? "اكتشف" : "Explore"}
                  <Arrow className="h-3.5 w-3.5 group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5 transition-transform" />
                </span>
              </Link>
            </StaggerItem>
          ))}
        </StaggerContainer>

        {/* Dual-audience split */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Individuals */}
          <div className="card-premium relative overflow-hidden p-8">
            <div className="glow-blob" style={{ width: 220, height: 220, top: -80, insetInlineEnd: -40, background: "hsl(var(--primary) / 0.10)" }} />
            <span className="icon-tile relative mb-4 h-11 w-11"><UserRound className="h-5 w-5 text-primary" /></span>
            <h3 className="text-heading-2 mb-2 relative">{isAr ? "للأفراد" : "For individuals"}</h3>
            <p className="text-body text-muted-foreground mb-5 relative max-w-sm">
              {isAr ? "ابحث، طابق، قدّم، وتطوّر مهنياً — كل ذلك في مكان واحد." : "Search, match, apply and grow — all in one place."}
            </p>
            <Link
              to={gate("/app/jobs")}
              {...gateState("/app/jobs")}
              className="relative inline-flex items-center gap-2 rounded-xl bg-primary px-6 h-11 text-body font-medium text-primary-foreground shadow-sm press-feedback"
            >
              {isAr ? "ابدأ مجاناً" : "Get started free"} <Arrow className="h-4 w-4" />
            </Link>
          </div>

          {/* Employers */}
          <div className="hero-gradient relative overflow-hidden rounded-2xl p-8 text-primary-foreground">
            <div className="glow-blob" style={{ width: 240, height: 240, bottom: -90, insetInlineStart: -50, background: "hsl(var(--secondary) / 0.3)" }} />
            <span className="relative mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-primary-foreground/10 border border-primary-foreground/15">
              <Building2 className="h-5 w-5" />
            </span>
            <h3 className="text-heading-2 mb-2 relative">{isAr ? "لأصحاب العمل" : "For employers"}</h3>
            <p className="text-body opacity-80 mb-5 relative max-w-sm">
              {isAr ? "انشر الوظائف، ابحث في قاعدة المواهب، ووظّف أسرع." : "Post jobs, search the talent pool, and hire faster."}
            </p>
            <Link
              to="/login"
              state={{ from: "/app/employer/register" }}
              className="relative inline-flex items-center gap-2 rounded-xl bg-secondary px-6 h-11 text-body font-medium text-[hsl(var(--primary))] shadow-sm press-feedback"
            >
              {isAr ? "ابدأ التوظيف" : "Start hiring"} <Arrow className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
