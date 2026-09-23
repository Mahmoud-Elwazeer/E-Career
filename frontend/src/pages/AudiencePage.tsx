import { Link } from "react-router-dom";
import { ArrowRight, ArrowLeft, CheckCircle2 } from "lucide-react";
import { Layout } from "@/components/Layout";
import { RasheedScene } from "@/components/rashid/RasheedScene";
import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/motion";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";
import { usePageMeta } from "@/hooks/use-seo";
import { INDIVIDUALS, BUSINESSES, type AudienceContent } from "@/components/landing/audience-content";

/**
 * AudiencePage — the dedicated, forward-navigable page for a single audience
 * (Individuals or Businesses). Reached from the navbar audience switcher.
 * Content is driven entirely by the shared audience-content module so it stays
 * in lockstep with the landing switcher and feature showcase.
 */
export function AudiencePage({ content }: { content: AudienceContent }) {
  const { lang, dir } = useTheme();
  const { isAuthenticated } = useAuth();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;

  usePageMeta(
    isAr ? content.titleAr : content.titleEn,
    isAr ? content.leadAr : content.leadEn,
  );

  // Gated app routes route through /login carrying the intended destination.
  const gate = (to: string) => (isAuthenticated ? to : "/login");
  const gateState = (to: string) => (isAuthenticated ? {} : { state: { from: to } });

  return (
    <Layout>
      {/* Hero */}
      <section className="chamber chamber-grid relative overflow-hidden text-primary-foreground">
        <div className="glow-blob" style={{ width: 360, height: 360, top: -120, insetInlineEnd: -80, background: "hsl(var(--secondary) / 0.28)" }} />
        <div className="container relative z-10 grid items-center gap-10 py-16 md:grid-cols-2 md:py-24">
          <div>
            <span className="eyebrow-mono text-primary-foreground/70 mb-4">
              <span className="signal-dot" /> {isAr ? content.eyebrowAr : content.eyebrowEn}
            </span>
            <h1 className="text-display-serif mt-3 mb-4">{isAr ? content.titleAr : content.titleEn}</h1>
            <p className="text-body-lg opacity-80 max-w-lg">{isAr ? content.leadAr : content.leadEn}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to={gate(content.primaryCta.to)}
                {...gateState(content.primaryCta.to)}
                className="inline-flex items-center gap-2 rounded-xl bg-secondary px-6 h-12 text-body font-medium text-[hsl(var(--primary))] shadow-sm press-feedback"
              >
                {isAr ? content.primaryCta.ar : content.primaryCta.en} <Arrow className="h-4 w-4" />
              </Link>
              <Link
                to="/pricing"
                className="inline-flex items-center gap-2 rounded-xl border border-primary-foreground/25 px-6 h-12 text-body font-medium text-primary-foreground press-feedback"
              >
                {isAr ? "الأسعار" : "See pricing"}
              </Link>
            </div>
          </div>
          <div className="relative">
            <RasheedScene />
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="section-y">
        <div className="container">
          <ScrollReveal>
            <div className="mb-10 text-center">
              <h2 className="text-display-serif">
                {isAr ? "ما الذي ستحصل عليه" : "What you get"}
              </h2>
            </div>
          </ScrollReveal>
          <StaggerContainer className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 md:gap-5" staggerDelay={0.06}>
            {content.features.map((f) => (
              <StaggerItem key={f.en}>
                <Link
                  to={gate(f.to)}
                  {...gateState(f.to)}
                  className="card-premium card-accent-top group flex h-full flex-col p-6"
                >
                  <span className="icon-tile mb-4 h-12 w-12">
                    <f.icon className="h-6 w-6 text-primary" />
                  </span>
                  <h3 className="text-heading-3 font-semibold mb-2 group-hover:text-primary transition-colors">
                    {isAr ? f.ar : f.en}
                  </h3>
                  <p className="text-body text-muted-foreground leading-relaxed">{isAr ? f.descAr : f.descEn}</p>
                  <span className="mt-4 inline-flex items-center gap-1 text-caption font-medium text-primary">
                    {isAr ? "اكتشف" : "Explore"}
                    <Arrow className="h-3.5 w-3.5 group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5 transition-transform" />
                  </span>
                </Link>
              </StaggerItem>
            ))}
          </StaggerContainer>
        </div>
      </section>

      {/* How it works */}
      <section className="section-y bg-surface-2/40">
        <div className="container">
          <ScrollReveal>
            <div className="mb-10 text-center">
              <span className="eyebrow-mono mb-4">{isAr ? "كيف تعمل" : "HOW IT WORKS"}</span>
              <h2 className="text-display-serif">{isAr ? "أربع خطوات" : "Four simple steps"}</h2>
            </div>
          </ScrollReveal>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {content.steps.map((s, i) => (
              <div key={s.en} className="card-premium relative p-6">
                <span className="mb-3 inline-flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-body font-semibold text-primary">
                  {i + 1}
                </span>
                <h3 className="text-heading-3 font-semibold mb-1.5">{isAr ? s.ar : s.en}</h3>
                <p className="text-body text-muted-foreground leading-relaxed">{isAr ? s.descAr : s.descEn}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="section-y">
        <div className="container">
          <div className="hero-gradient relative overflow-hidden rounded-3xl p-10 text-center text-primary-foreground md:p-16">
            <div className="glow-blob" style={{ width: 300, height: 300, bottom: -120, insetInlineStart: -60, background: "hsl(var(--secondary) / 0.3)" }} />
            <h2 className="text-display-serif relative mb-4">
              {isAr ? "جاهز تبدأ؟" : "Ready to start?"}
            </h2>
            <ul className="relative mx-auto mb-6 flex max-w-md flex-col gap-2 text-start">
              {content.steps.slice(0, 3).map((s) => (
                <li key={s.en} className="flex items-center gap-2 text-body opacity-90">
                  <CheckCircle2 className="h-4 w-4 text-secondary shrink-0" /> {isAr ? s.ar : s.en}
                </li>
              ))}
            </ul>
            <Link
              to={gate(content.primaryCta.to)}
              {...gateState(content.primaryCta.to)}
              className="relative inline-flex items-center gap-2 rounded-xl bg-secondary px-8 h-12 text-body font-medium text-[hsl(var(--primary))] shadow-sm press-feedback"
            >
              {isAr ? content.primaryCta.ar : content.primaryCta.en} <Arrow className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
}

export default function ForIndividualsPage() {
  return <AudiencePage content={INDIVIDUALS} />;
}

export function ForBusinessesPage() {
  return <AudiencePage content={BUSINESSES} />;
}
