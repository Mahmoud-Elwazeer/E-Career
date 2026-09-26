import { Link } from "react-router-dom";
import { UserRound, Building2, Landmark, ArrowRight, ArrowLeft } from "lucide-react";
import { ScrollReveal } from "@/components/motion";
import { useTheme } from "@/hooks/use-theme";

/**
 * AudiencePathways — the Master Landing's routing component.
 *
 * Replaces the in-page audience toggle with two clear forward pathways so the
 * page's job is to ROUTE users to the correct product experience, not to mix
 * Individual + Business content on one page:
 *   Explore All Individuals -> /for-individuals
 *   Explore All Business    -> /for-businesses
 *   Government              -> Coming soon (disabled)
 */
export function AudiencePathways() {
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;

  return (
    <section className="section-y">
      <div className="container">
        <ScrollReveal>
          <div className="mb-8 text-center">
            <span className="eyebrow-mono mb-3">{isAr ? "منصة واحدة، تجربتان" : "ONE PLATFORM, TWO EXPERIENCES"}</span>
            <h2 className="text-display-serif mt-3">{isAr ? "اختر مسارك" : "Choose your path"}</h2>
            <p className="text-body-lg text-muted-foreground mt-2 max-w-xl mx-auto">
              {isAr
                ? "منظومة مهنية واحدة متصلة، بتجربتين مختلفتين تماماً للأفراد والشركات."
                : "One connected career ecosystem, with two distinct experiences for individuals and companies."}
            </p>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {/* For Individuals */}
          <Link to="/for-individuals" className="card-premium card-accent-top group relative overflow-hidden p-8 flex flex-col">
            <span className="icon-tile mb-4 h-12 w-12"><UserRound className="h-6 w-6 text-primary" /></span>
            <h3 className="text-heading-2 mb-2">{isAr ? "للأفراد" : "For Individuals"}</h3>
            <p className="text-body text-muted-foreground mb-6 flex-1">
              {isAr
                ? "ابحث عن وظائف موثقة، ابنِ سيرتك ومسارك المهني، وتدرّب مع رشيد."
                : "Find verified jobs, build your CV and career, and prepare with Rasheed — your AI coach."}
            </p>
            <span className="btn-green inline-flex items-center gap-2 rounded-xl px-6 h-11 text-body font-medium shadow-sm w-fit group-hover:gap-3">
              {isAr ? "استكشف كل خدمات الأفراد" : "Explore all Individuals"} <Arrow className="h-4 w-4" />
            </span>
          </Link>

          {/* For Businesses */}
          <Link to="/for-businesses" className="hero-gradient group relative overflow-hidden rounded-2xl p-8 text-primary-foreground flex flex-col">
            <div className="glow-blob" style={{ width: 220, height: 220, bottom: -80, insetInlineStart: -40, background: "hsl(var(--secondary) / 0.3)" }} />
            <span className="relative mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-primary-foreground/10 border border-primary-foreground/15"><Building2 className="h-6 w-6" /></span>
            <h3 className="text-heading-2 mb-2 relative">{isAr ? "للشركات" : "For Businesses"}</h3>
            <p className="text-body opacity-80 mb-6 relative flex-1">
              {isAr
                ? "انشر وظائف موثقة، اكتشف المواهب، ووظّف أسرع بذكاء عبر قاعدة المواهب ومطابقة الذكاء الاصطناعي."
                : "Post verified roles, discover talent, and hire faster with the talent pool and AI matching."}
            </p>
            <span className="relative inline-flex items-center gap-2 rounded-xl bg-secondary px-6 h-11 text-body font-medium text-[hsl(var(--primary))] shadow-sm w-fit group-hover:gap-3 transition-all">
              {isAr ? "استكشف كل خدمات الشركات" : "Explore all Business"} <Arrow className="h-4 w-4" />
            </span>
          </Link>
        </div>

        {/* Government — coming soon */}
        <div className="mt-4 flex items-center justify-center gap-2 rounded-2xl border border-dashed border-border bg-surface-2/40 px-5 py-3 text-caption text-muted-foreground">
          <Landmark className="h-4 w-4" />
          {isAr ? "للحكومات والمؤسسات" : "For Governments & Institutions"}
          <span className="rounded-full bg-signal/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-signal-foreground">
            {isAr ? "قريباً" : "Soon"}
          </span>
        </div>
      </div>
    </section>
  );
}
