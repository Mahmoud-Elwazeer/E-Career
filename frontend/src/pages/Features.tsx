/**
 * Features / Explore — the central discovery surface for every major
 * platform capability (USAM Master Ecosystem integration).
 *
 * Reads from the canonical `feature-catalog.ts` so this page can never drift
 * from the nav menus / audience pages — they all draw from the same list.
 * Public page: anonymous visitors see the full catalog and can read what
 * each feature does; clicking a gated feature routes through /login with a
 * safe `?next=`/state deep link so they land on the right screen right after
 * signing in.
 */
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Search, Sparkles, MessageCircle, FileText, Mic, Target, Network,
  DollarSign, Award, Bookmark, ClipboardList, Building2, BadgeCheck,
  PlusCircle, Users, LayoutDashboard, BarChart3, CreditCard, Settings,
  Bell, User, Code2, TrendingUp, type LucideIcon,
  ArrowRight, ArrowLeft, Lock, CheckCircle2, Filter,
} from "lucide-react";
import { Layout } from "@/components/Layout";
import { PageHeader } from "@/components/PageHeader";
import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/motion";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";
import { usePageMeta } from "@/hooks/use-seo";
import {
  FEATURES, type FeatureAudience, type FeatureEntry,
} from "@/data/feature-catalog";

const ICONS: Record<string, LucideIcon> = {
  Search, Sparkles, MessageCircle, FileText, Mic, Target, Network,
  DollarSign, Award, Bookmark, ClipboardList, Building2, BadgeCheck,
  PlusCircle, Users, LayoutDashboard, BarChart3, CreditCard, Settings,
  Bell, User, Code2, TrendingUp,
};

type FilterKey = "all" | FeatureAudience;

const FILTERS: { key: FilterKey; en: string; ar: string }[] = [
  { key: "all", en: "All", ar: "الكل" },
  { key: "individual", en: "For Individuals", ar: "للأفراد" },
  { key: "employer", en: "For Employers", ar: "لأصحاب العمل" },
  { key: "admin", en: "Platform", ar: "المنصة" },
];

function FeatureCard({ feature, isAr, Arrow, isAuthenticated, userRole }: {
  feature: FeatureEntry;
  isAr: boolean;
  Arrow: typeof ArrowRight;
  isAuthenticated: boolean;
  userRole?: string;
}) {
  const Icon = ICONS[feature.icon] ?? Sparkles;
  const needsRole = feature.access === "employer" || feature.access === "admin";
  const roleMismatch =
    isAuthenticated &&
    ((feature.access === "employer" && userRole !== "employer" && userRole !== "admin") ||
      (feature.access === "admin" && userRole !== "admin"));

  // Gated destination: anonymous visitors go through /login carrying the
  // real target as router state (same-tab navigation preserves state).
  const linkTo = !isAuthenticated && feature.access !== "public" ? "/login" : feature.to;
  const linkState = !isAuthenticated && feature.access !== "public" ? { from: feature.to } : undefined;

  return (
    <Link
      to={linkTo}
      state={linkState}
      className="card-premium card-accent-top group flex h-full flex-col p-6"
    >
      <div className="flex items-start justify-between mb-4">
        <span className="icon-tile h-12 w-12">
          <Icon className="h-6 w-6 text-primary" />
        </span>
        {needsRole && (
          <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-1 text-[11px] font-medium text-muted-foreground">
            <Lock className="h-3 w-3" />
            {feature.access === "admin" ? (isAr ? "إدارة" : "Admin") : (isAr ? "صاحب عمل" : "Employer")}
          </span>
        )}
      </div>
      <h3 className="text-heading-3 font-semibold mb-2 group-hover:text-primary transition-colors">
        {isAr ? feature.nameAr : feature.nameEn}
      </h3>
      <p className="text-body text-muted-foreground leading-relaxed flex-1">
        {isAr ? feature.shortDescAr : feature.shortDescEn}
      </p>
      <span className="mt-4 inline-flex items-center gap-1 text-caption font-medium text-primary">
        {roleMismatch
          ? (isAr ? "يتطلب حساب مختلف" : "Requires a different account")
          : (isAr ? "اكتشف" : "Explore")}
        <Arrow className="h-3.5 w-3.5 group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5 transition-transform" />
      </span>
    </Link>
  );
}

export default function Features() {
  const { lang, dir } = useTheme();
  const { isAuthenticated, user } = useAuth();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const [filter, setFilter] = useState<FilterKey>("all");

  usePageMeta(
    isAr ? "استكشف المنصة" : "Explore the Platform",
    isAr
      ? "كل ميزات USAM في مكان واحد: البحث عن وظائف، مساعد رشيد الذكي، أدوات المسار المهني، وأدوات التوظيف لأصحاب العمل."
      : "Every USAM feature in one place: job search, Rasheed AI coach, career tools, and hiring tools for employers.",
  );

  const visible = useMemo(() => {
    if (filter === "all") return FEATURES;
    return FEATURES.filter((f) => f.audience === filter || f.audience === "everyone");
  }, [filter]);

  const grouped = useMemo(() => {
    const order: { category: FeatureEntry["category"]; en: string; ar: string }[] = [
      { category: "discover", en: "Discover opportunities", ar: "اكتشف الفرص" },
      { category: "career-tools", en: "Career tools", ar: "أدوات المسار المهني" },
      { category: "ai-coaching", en: "AI & preparation", ar: "الذكاء الاصطناعي والتحضير" },
      { category: "insights", en: "Insights", ar: "رؤى وتحليلات" },
      { category: "hiring", en: "Hiring", ar: "التوظيف" },
      { category: "account", en: "Account", ar: "الحساب" },
      { category: "platform", en: "Platform", ar: "المنصة" },
    ];
    return order
      .map((g) => ({ ...g, items: visible.filter((f) => f.category === g.category) }))
      .filter((g) => g.items.length > 0);
  }, [visible]);

  return (
    <Layout>
      {/* Hero */}
      <section className="chamber chamber-grid relative overflow-hidden text-primary-foreground">
        <div className="glow-blob" style={{ width: 360, height: 360, top: -120, insetInlineEnd: -80, background: "hsl(var(--secondary) / 0.28)" }} />
        <div className="container relative z-10 py-14 md:py-20">
          <nav aria-label={isAr ? "مسار التنقل" : "Breadcrumb"} className="mb-6 text-caption text-primary-foreground/70">
            <Link to="/" className="hover:text-primary-foreground transition-colors">{isAr ? "الرئيسية" : "Home"}</Link>
            <span className="mx-2">/</span>
            <span className="text-primary-foreground">{isAr ? "استكشف المنصة" : "Explore"}</span>
          </nav>
          <span className="eyebrow-mono text-primary-foreground/70 mb-4">
            <span className="signal-dot" /> {isAr ? "دليل المنصة الكامل" : "FULL PLATFORM GUIDE"}
          </span>
          <h1 className="text-display-serif mt-3 mb-4 max-w-2xl">
            {isAr ? "كل ما تقدر تعمله على USAM" : "Everything you can do on USAM"}
          </h1>
          <p className="text-body-lg opacity-80 max-w-xl">
            {isAr
              ? "من البحث عن وظيفة موثقة إلى بناء فريق التوظيف — هذه كل الأدوات الحقيقية المتاحة اليوم، بروابط مباشرة لكل واحدة."
              : "From finding a verified job to building your hiring team — these are every real tool available today, with a direct link to each."}
          </p>
        </div>
      </section>

      {/* Filters */}
      <section className="border-b border-border sticky top-16 z-30 bg-background/95 backdrop-blur-sm">
        <div className="container py-4 flex items-center gap-2 overflow-x-auto">
          <Filter className="h-4 w-4 text-muted-foreground shrink-0" aria-hidden />
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              aria-pressed={filter === f.key}
              className={`shrink-0 rounded-full px-4 py-1.5 text-caption font-medium transition-colors ${
                filter === f.key
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-accent hover:text-foreground"
              }`}
            >
              {isAr ? f.ar : f.en}
            </button>
          ))}
        </div>
      </section>

      {/* Feature groups */}
      <section className="section-y">
        <div className="container space-y-14">
          {grouped.map((group) => (
            <div key={group.category}>
              <ScrollReveal>
                <h2 className="text-heading-2 font-semibold mb-6">
                  {isAr ? group.ar : group.en}
                </h2>
              </ScrollReveal>
              <StaggerContainer className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 md:gap-5" staggerDelay={0.05}>
                {group.items.map((feature) => (
                  <StaggerItem key={feature.id}>
                    <FeatureCard
                      feature={feature}
                      isAr={isAr}
                      Arrow={Arrow}
                      isAuthenticated={isAuthenticated}
                      userRole={user?.role}
                    />
                  </StaggerItem>
                ))}
              </StaggerContainer>
            </div>
          ))}
        </div>
      </section>

      {/* Audience CTA */}
      <section className="section-y bg-surface-2/40">
        <div className="container grid gap-5 md:grid-cols-2">
          <Link to="/for-individuals" className="card-premium p-8 group">
            <div className="icon-tile mb-4 h-12 w-12"><User className="h-6 w-6 text-primary" /></div>
            <h3 className="text-heading-3 font-semibold mb-2 group-hover:text-primary transition-colors">
              {isAr ? "جديد على USAM كفرد؟" : "New to USAM as an individual?"}
            </h3>
            <p className="text-body text-muted-foreground mb-4">
              {isAr ? "تعرّف على كامل رحلتك المهنية من البحث إلى التوظيف." : "See your full career journey from search to hire."}
            </p>
            <span className="inline-flex items-center gap-1 text-caption font-medium text-primary">
              {isAr ? "استكشف الصفحة" : "Explore the page"} <Arrow className="h-3.5 w-3.5" />
            </span>
          </Link>
          <Link to="/for-businesses" className="card-premium p-8 group">
            <div className="icon-tile mb-4 h-12 w-12"><Building2 className="h-6 w-6 text-primary" /></div>
            <h3 className="text-heading-3 font-semibold mb-2 group-hover:text-primary transition-colors">
              {isAr ? "تريد التوظيف؟" : "Looking to hire?"}
            </h3>
            <p className="text-body text-muted-foreground mb-4">
              {isAr ? "تعرّف على أدوات التوظيف الذكية لأصحاب العمل." : "See the AI-powered hiring tools for employers."}
            </p>
            <span className="inline-flex items-center gap-1 text-caption font-medium text-primary">
              {isAr ? "استكشف الصفحة" : "Explore the page"} <Arrow className="h-3.5 w-3.5" />
            </span>
          </Link>
        </div>
      </section>
    </Layout>
  );
}
