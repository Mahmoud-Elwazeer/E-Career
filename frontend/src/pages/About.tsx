import { Link } from "react-router-dom";
import {
  Target, Users, ShieldCheck, Sparkles, Network, Building2,
  ArrowRight, ArrowLeft, MessageCircle,
} from "lucide-react";
import { Layout } from "@/components/Layout";
import { RasheedAvatar } from "@/components/rashid/RasheedAvatar";
import { ScrollReveal } from "@/components/motion";
import { useTheme } from "@/hooks/use-theme";
import { usePageMeta } from "@/hooks/use-seo";

/**
 * About — a production-grade story of what USAM is: mission, the ecosystem it
 * connects, the intelligence layer behind it, and the trust model. Every claim
 * maps to a real platform capability; no fabricated metrics or customers.
 */
export default function About() {
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;

  usePageMeta(
    isAr ? "عن USAM" : "About USAM",
    isAr
      ? "USAM نظام تشغيل مهني وتوظيفي يربط الأفراد بأصحاب العمل عبر وظائف موثقة وذكاء اصطناعي."
      : "USAM is a career + hiring operating system connecting people to employers through verified roles and applied AI.",
  );

  const pillars = [
    { icon: Target, titleEn: "Our mission", titleAr: "مهمتنا", descEn: "Make the path from talent to opportunity direct, honest and intelligent — for individuals and the companies hiring them.", descAr: "أن نجعل الطريق من الموهبة إلى الفرصة مباشراً وصادقاً وذكياً — للأفراد وللشركات التي توظّفهم." },
    { icon: Network, titleEn: "One connected graph", titleAr: "رسم واحد متصل", descEn: "Profiles, CVs, skills, jobs, matches and interviews live in one career graph — not disconnected tools.", descAr: "الملفات والسير والمهارات والوظائف والمطابقات والمقابلات في رسم مهني واحد — لا أدوات منفصلة." },
    { icon: Sparkles, titleEn: "Applied AI", titleAr: "ذكاء اصطناعي تطبيقي", descEn: "Rasheed and the matching engine work from your real profile — guidance grounded in evidence, not guesswork.", descAr: "يعمل رشيد ومحرك المطابقة من ملفك الحقيقي — إرشاد قائم على الأدلة لا التخمين." },
    { icon: ShieldCheck, titleEn: "Verified, direct", titleAr: "موثّق ومباشر", descEn: "Every role links to the real employer source. We reject aggregator middlemen so applications go where they should.", descAr: "كل وظيفة مرتبطة بمصدر صاحب العمل الحقيقي. نرفض الوسطاء لتصل الطلبات إلى وجهتها الصحيحة." },
  ];

  return (
    <Layout>
      {/* Hero */}
      <section className="chamber chamber-grid relative overflow-hidden text-primary-foreground">
        <div className="glow-blob" style={{ width: 360, height: 360, top: -120, insetInlineEnd: -80, background: "hsl(var(--secondary) / 0.28)" }} />
        <div className="container relative z-10 max-w-3xl py-20 text-center">
          <span className="eyebrow-mono text-primary-foreground/70 mb-4 justify-center"><span className="signal-dot" /> {isAr ? "عن USAM" : "ABOUT USAM"}</span>
          <h1 className="text-display-serif mt-3 mb-4">
            {isAr ? (<>ليس لوحة وظائف — بل <span className="serif-accent text-secondary">نظام مهني</span></>)
                  : (<>Not a job board — a <span className="serif-accent text-secondary">career operating system</span></>)}
          </h1>
          <p className="text-body-lg opacity-80">
            {isAr
              ? "يربط USAM الأفراد بأصحاب العمل عبر وظائف موثقة وذكاء اصطناعي يرافق الرحلة من البحث حتى التوظيف والنمو."
              : "USAM connects people to employers through verified roles and applied AI that guides the journey from search to hire to growth."}
          </p>
        </div>
      </section>

      {/* Pillars */}
      <section className="section-y">
        <div className="container">
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
            {pillars.map((p) => (
              <ScrollReveal key={p.titleEn}>
                <div className="card-premium h-full p-8">
                  <span className="icon-tile mb-4 h-12 w-12"><p.icon className="h-6 w-6 text-primary" /></span>
                  <h3 className="text-heading-2 mb-2">{isAr ? p.titleAr : p.titleEn}</h3>
                  <p className="text-body text-muted-foreground leading-relaxed">{isAr ? p.descAr : p.descEn}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      {/* Who we serve */}
      <section className="section-y bg-surface-2/40">
        <div className="container grid gap-5 md:grid-cols-2">
          <div className="card-premium relative overflow-hidden p-8">
            <span className="icon-tile mb-4 h-11 w-11"><Users className="h-5 w-5 text-primary" /></span>
            <h3 className="text-heading-2 mb-2">{isAr ? "للأفراد" : "For individuals"}</h3>
            <p className="text-body text-muted-foreground mb-5 max-w-sm">
              {isAr ? "طلاب، خريجون، ومحترفون يبحثون عن الخطوة التالية بثقة." : "Students, graduates and professionals looking for their next step with confidence."}
            </p>
            <Link to="/for-individuals" className="inline-flex items-center gap-1 text-caption font-medium text-primary link-underline">
              {isAr ? "استكشف للأفراد" : "Explore for individuals"} <Arrow className="h-3.5 w-3.5" />
            </Link>
          </div>
          <div className="hero-gradient relative overflow-hidden rounded-2xl p-8 text-primary-foreground">
            <div className="glow-blob" style={{ width: 220, height: 220, bottom: -80, insetInlineStart: -40, background: "hsl(var(--secondary) / 0.3)" }} />
            <span className="relative mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-primary-foreground/10 border border-primary-foreground/15"><Building2 className="h-5 w-5" /></span>
            <h3 className="text-heading-2 mb-2 relative">{isAr ? "لأصحاب العمل" : "For businesses"}</h3>
            <p className="text-body opacity-80 mb-5 relative max-w-sm">
              {isAr ? "شركات تريد التوظيف أسرع بذكاء ومصداقية." : "Companies that want to hire faster, with intelligence and trust."}
            </p>
            <Link to="/for-businesses" className="relative inline-flex items-center gap-1 text-caption font-medium text-secondary link-underline">
              {isAr ? "استكشف للشركات" : "Explore for businesses"} <Arrow className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Rasheed note + CTA */}
      <section className="section-y">
        <div className="container">
          <div className="card-premium flex flex-col items-center gap-6 p-10 text-center md:flex-row md:text-start">
            <RasheedAvatar expression="greeting" size={96} />
            <div className="flex-1">
              <div className="mb-2 inline-flex items-center gap-1.5 text-caption font-medium text-primary">
                <MessageCircle className="h-3.5 w-3.5" /> {isAr ? "قابل رشيد" : "Meet Rasheed"}
              </div>
              <h3 className="text-heading-2 mb-2">{isAr ? "مساعدك المهني الذكي" : "Your AI career coach"}</h3>
              <p className="text-body text-muted-foreground leading-relaxed">
                {isAr
                  ? "يرافقك رشيد عبر المنصة: مراجعة السيرة، المطابقة، رسائل التقديم، والتحضير للمقابلات — دائماً بناءً على ملفك الحقيقي."
                  : "Rasheed works with you across the platform — CV feedback, matches, cover letters and interview prep — always grounded in your real profile."}
              </p>
            </div>
            <Link to="/for-individuals" className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 h-11 text-body font-medium text-primary-foreground shadow-sm press-feedback">
              {isAr ? "ابدأ الآن" : "Get started"} <Arrow className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
}
