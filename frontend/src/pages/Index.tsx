import { useState, useCallback } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useNavigate, Link } from "react-router-dom";
import { ArrowRight, ArrowLeft, Laptop, Stethoscope, PenTool, DollarSign, GraduationCap, Wrench, Users, TrendingUp, MousePointerClick, Filter, Send, Building2 } from "lucide-react";
import { StatsStrip, WhyUsamSection } from "@/components/landing/ScrollSections";
import { HeroSection } from "@/components/landing/HeroSection";
import { FeatureShowcase } from "@/components/landing/FeatureShowcase";
import { RasheedAvatar } from "@/components/rashid/RasheedAvatar";
import { Button } from "@/components/ui/button";
import { Layout } from "@/components/Layout";
import { HowItWorks } from "@/components/HowItWorks";
import { OnboardingFlow } from "@/components/landing/OnboardingFlow";
import { QuickFilters } from "@/components/landing/QuickFilters";
import { FeaturedCarousel } from "@/components/landing/FeaturedCarousel";
import { CareerTracks } from "@/components/landing/CareerTracks";
import { CompanySpotlight } from "@/components/landing/CompanySpotlight";
import { SavedJobsTeaser } from "@/components/landing/SavedJobsTeaser";
import { FaqSection } from "@/components/landing/FaqSection";
import { ScrollReveal, StaggerContainer, StaggerItem, AnimatedCard, TextReveal, CountUp } from "@/components/motion";
import { useLandingData } from "@/hooks/use-landing-data";
import { useAuth } from "@/hooks/use-auth";
import { useTheme } from "@/hooks/use-theme";
import { usePageMeta } from "@/hooks/use-seo";
// Industry type removed - use string literals

const categoryMeta: { label: string; labelAr: string; value: Industry; icon: React.ElementType }[] = [
  { label: "Technology", labelAr: "التكنولوجيا", value: "technology", icon: Laptop },
  { label: "Finance", labelAr: "المالية", value: "finance", icon: DollarSign },
  { label: "Healthcare", labelAr: "الرعاية الصحية", value: "healthcare", icon: Stethoscope },
  { label: "Design", labelAr: "التصميم", value: "design", icon: PenTool },
  { label: "Marketing", labelAr: "التسويق", value: "marketing", icon: TrendingUp },
  { label: "Education", labelAr: "التعليم", value: "education", icon: GraduationCap },
  { label: "Engineering", labelAr: "الهندسة", value: "engineering", icon: Wrench },
  { label: "Sales", labelAr: "المبيعات", value: "sales", icon: Users },
];

export default function Index() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const jobsPath = isAuthenticated ? "/app/jobs" : "/login";
  const reduced = useReducedMotion();

  const { data: landing } = useLandingData();

  const featuredJobs = landing?.featuredJobs ?? [];
  const industryCounts = landing?.industryCounts ?? {};
  const categories = categoryMeta.map((cat) => ({ ...cat, count: industryCounts[cat.value] || 0 }));


  // useOrganizationStructuredData();
  // useWebSiteStructuredData();
  usePageMeta(
    "One search. Every opportunity",
    "Discover thousands of jobs aggregated from multiple leading job sources across MENA."
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (isAuthenticated) {
      navigate(`/app/jobs?q=${encodeURIComponent(query)}`);
    } else {
      navigate("/login", { state: { from: `/app/jobs?q=${encodeURIComponent(query)}` } });
    }
  };

  const howItWorksSteps = [
    {
      icon: MousePointerClick,
      title: isAr ? "ابحث" : "Search",
      description: isAr
        ? "اكتب المسمى الوظيفي أو المهارة — نبحث في كل المنصات دفعة واحدة"
        : "Type a job title or skill — we search all platforms at once",
    },
    {
      icon: Filter,
      title: isAr ? "صفّي" : "Filter",
      description: isAr
        ? "استخدم الفلاتر الذكية لتضييق النتائج حسب الموقع والقطاع والخبرة"
        : "Use smart filters to narrow by location, industry, and experience level",
    },
    {
      icon: Send,
      title: isAr ? "قدّم" : "Apply",
      description: isAr
        ? "اضغط على 'قدّم الآن' — ننقلك مباشرة للمصدر الأصلي بدون وسيط"
        : "Click 'Apply Now' — we take you directly to the original source",
    },
  ];

  const handleOnboardingComplete = useCallback((prefs: { track: string; mode: string; location: string }) => {
    const params = new URLSearchParams();
    if (prefs.track) params.set("q", prefs.track);
    if (prefs.mode && prefs.mode !== "any") params.set("locationType", prefs.mode);
    if (isAuthenticated) {
      navigate(`/app/jobs?${params.toString()}`);
    } else {
      navigate("/login", { state: { from: `/app/jobs?${params.toString()}` } });
    }
  }, [isAuthenticated, navigate]);

  return (
    <Layout>
      {/* ═══ ONBOARDING FLOW ═══
          Only for anonymous visitors on the landing page. Authenticated
          onboarding is owned exclusively by <OnboardingWrapper> in App.tsx,
          so the two never render simultaneously. */}
      {!isAuthenticated && <OnboardingFlow onComplete={handleOnboardingComplete} />}
      {/* ═══ HERO — centered editorial opener + product-proof panel ═══ */}
      <HeroSection
        query={query}
        setQuery={setQuery}
        onSubmit={handleSearch}
        landing={landing}
        industryCount={Object.keys(industryCounts).length || 0}
      />

      {/* ═══ QUICK FILTERS ═══ */}
      <QuickFilters />

      {/* ═══ FEATURED JOBS CAROUSEL ═══ */}
      <section className="featured-jobs">
        <FeaturedCarousel jobs={featuredJobs} />
      </section>

      {/* ═══ HOW IT WORKS ═══ */}
      <section className="how-it-works section-band section-y">
        <div className="mx-auto max-w-[1120px] px-6">
          <HowItWorks
            steps={howItWorksSteps}
            sectionTitle={isAr ? "كيف يعمل" : "How it works"}
            sectionSubtitle={isAr ? "ثلاث خطوات بسيطة للوصول لوظيفتك" : "Three simple steps to your next role"}
          />
        </div>
      </section>

      {/* ═══ PLATFORM FEATURE SHOWCASE ═══ */}
      <FeatureShowcase />

      {/* ═══ CAREER TRACKS ═══ */}
      <CareerTracks />

      {/* ═══ CATEGORIES ═══ */}
      <section className="section-band section-y">
        <div className="container">
          <ScrollReveal>
            <div className="flex items-end justify-between mb-8">
              <div>
                <span className="eyebrow-mono mb-3">{isAr ? "التصنيفات" : "CATEGORIES"}</span>
                <h2 className="text-display-serif mt-3">{isAr ? "تصفح حسب التصنيف" : "Browse by category"}</h2>
                <p className="text-body-lg text-muted-foreground mt-2">{isAr ? "اختر المجال الذي يناسبك" : "Find roles in your preferred industry"}</p>
              </div>
              <Link to={jobsPath} className="text-body text-primary font-medium flex items-center gap-1 link-underline shrink-0">
                {isAr ? "عرض الكل" : "View all"} <Arrow className="h-3 w-3" />
              </Link>
            </div>
          </ScrollReveal>
          <StaggerContainer className="grid grid-cols-2 sm:grid-cols-4 gap-4" staggerDelay={0.06}>
            {categories.map((cat) => (
              <StaggerItem key={cat.value}>
                <AnimatedCard>
                  <Link
                    to={`${jobsPath}?industry=${cat.value}`}
                    className="card-premium flex items-center gap-3.5 p-4 group"
                  >
                    <div className="icon-tile p-2.5">
                      <cat.icon className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-body font-medium group-hover:text-primary transition-colors duration-fast">
                        {isAr ? cat.labelAr : cat.label}
                      </p>
                      <p className="text-caption text-muted-foreground">
                        {cat.count} {isAr ? "وظيفة" : "jobs"}
                      </p>
                    </div>
                  </Link>
                </AnimatedCard>
              </StaggerItem>
            ))}
          </StaggerContainer>
        </div>
      </section>

      {/* ═══ COMPANY SPOTLIGHT ═══ */}
      <CompanySpotlight />

      {/* ═══ SAVED JOBS + ALERTS TEASER ═══ */}
      <SavedJobsTeaser />

      {/* ═══ STATS ═══ */}
      <StatsStrip
        stats={[
          { n: landing?.totalJobs ?? 0, suffix: "+", label: isAr ? "وظيفة نشطة" : "Active Jobs" },
          { n: landing?.sourcesCount ?? 0, suffix: "", label: isAr ? "مصادر" : "Sources" },
          { n: Object.keys(industryCounts).length || 0, suffix: "", label: isAr ? "قطاعات" : "Industries" },
          { n: 10, suffix: "+", label: isAr ? "دول" : "Countries" },
        ]}
        reduced={reduced}
      />

      {/* ═══ WHY USAM ═══ */}
      <WhyUsamSection isAr={isAr} reduced={reduced} />

      {/* ═══ FAQ ═══ */}
      <FaqSection />

      {/* ═══ EMPLOYER CTA ═══ */}
      <section className="section-y">
        <div className="container">
          <div className="card-premium relative overflow-hidden mx-auto max-w-4xl text-center p-10 md:p-14">
            <div className="glow-blob" style={{ width: 300, height: 300, top: -100, insetInlineEnd: -60, background: "hsl(var(--primary) / 0.12)" }} />
            <div className="icon-tile relative mx-auto mb-5 h-14 w-14">
              <Building2 className="h-6 w-6 text-primary" />
            </div>
            <h2 className="text-display-serif mb-3 relative">
              {isAr ? "هل تبحث عن مواهب؟" : "Looking to hire?"}
            </h2>
            <p className="text-body-lg text-muted-foreground mb-7 max-w-lg mx-auto relative">
              {isAr
                ? "انضم كصاحب عمل وابدأ في نشر وظائفك والوصول إلى أفضل المرشحين"
                : "Join as an employer to post jobs and reach top talent across the region"}
            </p>
            <Button asChild size="lg" className="relative rounded-xl px-8 h-12 font-medium press-feedback">
              <Link to="/login" state={{ from: "/app/employer/register" }}>
                <Building2 className="h-4 w-4 me-2" />
                {isAr ? "ابدأ التوظيف" : "Start hiring"} <Arrow className="h-4 w-4 ms-1" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* ═══ FINAL CTA ═══ */}
      <section className="section-y">
        <div className="container">
          <motion.div
            className="hero-gradient relative overflow-hidden rounded-[2rem] px-8 py-12 md:px-14 md:py-16 text-primary-foreground"
            initial={reduced ? {} : { opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6 }}
          >
            <div className="glow-blob" style={{ width: 360, height: 360, top: -120, insetInlineEnd: -60, background: "hsl(var(--secondary) / 0.3)" }} />
            <div className="glow-blob" style={{ width: 260, height: 260, bottom: -100, insetInlineStart: "20%", background: "hsl(var(--primary-hover) / 0.5)" }} />

            <div className="relative z-10 grid items-center gap-8 md:grid-cols-[1fr_auto]">
              <div className="max-w-xl">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-primary-foreground/15 bg-primary-foreground/10 px-3 py-1 text-caption font-medium backdrop-blur-sm mb-4">
                  {isAr ? "ابدأ اليوم" : "Get started today"}
                </span>
                <h2 className="text-display-serif leading-tight mb-3">
                  {isAuthenticated
                    ? (isAr ? "لا تفوت أي فرصة" : "Never miss an opportunity")
                    : (isAr ? "رحلتك المهنية تبدأ الآن" : "Your career journey starts now")}
                </h2>
                <p className="text-body-lg opacity-80 mb-7">
                  {isAuthenticated
                    ? (isAr ? "أنشئ تنبيهاً واحصل على إشعار فوري عند توفر وظيفة مناسبة." : "Create an alert and get notified the moment a matching role appears.")
                    : (isAr ? "أنشئ حساباً مجانياً واحصل على وصول كامل للوظائف والتوصيات ومساعدك رشيد." : "Create a free account for full access to jobs, matches, and Rasheed — your AI coach.")}
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <Button asChild size="lg" className="bg-secondary text-secondary-foreground hover:bg-secondary/90 press-feedback rounded-xl px-8 h-12 font-medium cta-glow">
                    <Link to={isAuthenticated ? "/app/alerts" : "/login"}>
                      {isAuthenticated
                        ? (isAr ? "أنشئ تنبيهاً مجانياً" : "Create a free alert")
                        : (isAr ? "سجّل الآن" : "Sign up now")}
                      <Arrow className="h-4 w-4 ms-1" />
                    </Link>
                  </Button>
                  {!isAuthenticated && (
                    <Button asChild size="lg" variant="outline" className="rounded-xl px-6 h-12 font-medium border-primary-foreground/25 bg-primary-foreground/5 text-primary-foreground hover:bg-primary-foreground/10">
                      <Link to="/pricing">{isAr ? "شاهد الباقات" : "See plans"}</Link>
                    </Button>
                  )}
                </div>
              </div>

              <div className="hidden md:block shrink-0">
                <RasheedAvatar expression="greeting" size={132} />
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </Layout>
  );
}
