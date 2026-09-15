import { useState, useRef, useCallback } from "react";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";
import { useNavigate, Link } from "react-router-dom";
import { Search, ArrowRight, ArrowLeft, Briefcase, Laptop, Stethoscope, PenTool, DollarSign, GraduationCap, Wrench, Users, TrendingUp, Shield, Zap, Globe, Bell, MousePointerClick, Filter, Send, LogIn, Building2, Sparkles, CheckCircle2 } from "lucide-react";
import { StatsStrip, WhyUsamSection } from "@/components/landing/ScrollSections";
import { HeroAssistant } from "@/components/landing/HeroAssistant";
import { FeatureShowcase } from "@/components/landing/FeatureShowcase";
import { Button } from "@/components/ui/button";
import { Layout } from "@/components/Layout";
import { WatermarkBackground } from "@/components/WatermarkBackground";
import { HowItWorks } from "@/components/HowItWorks";
import { SmartSearch } from "@/components/landing/SmartSearch";
import { OnboardingFlow } from "@/components/landing/OnboardingFlow";
import { QuickFilters } from "@/components/landing/QuickFilters";
import { FeaturedCarousel } from "@/components/landing/FeaturedCarousel";
import { CareerTracks } from "@/components/landing/CareerTracks";
import { CompanySpotlight } from "@/components/landing/CompanySpotlight";
import { SavedJobsTeaser } from "@/components/landing/SavedJobsTeaser";
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

  // Hero parallax scroll
  const heroRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
  const heroY = useTransform(scrollYProgress, [0, 1], [0, 80]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

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

  const isTyping = query.length > 0;

  return (
    <Layout>
      {/* ═══ ONBOARDING FLOW ═══
          Only for anonymous visitors on the landing page. Authenticated
          onboarding is owned exclusively by <OnboardingWrapper> in App.tsx,
          so the two never render simultaneously. */}
      {!isAuthenticated && <OnboardingFlow onComplete={handleOnboardingComplete} />}
      {/* ═══ HERO — Cinematic Entrance ═══ */}
      <section ref={heroRef} className="hero-gradient hero-grid relative overflow-hidden text-primary-foreground">
        <WatermarkBackground variant="shimmer" opacity={0.04} inheritColor paused={isTyping} />

        {/* Ambient glow blobs for depth */}
        <div className="glow-blob" style={{ width: 480, height: 480, top: -140, insetInlineEnd: -120, background: "hsl(var(--secondary) / 0.35)" }} />
        <div className="glow-blob" style={{ width: 360, height: 360, bottom: -120, insetInlineStart: -80, background: "hsl(var(--primary-hover) / 0.6)" }} />

        {/* Gradient breathing overlay */}
        <div
          className="absolute inset-0 pointer-events-none z-[1]"
          style={{
            background: "radial-gradient(ellipse at 30% 50%, hsl(var(--primary-hover) / 0.08), transparent 70%)",
            animation: isTyping || reduced ? "none" : "gradient-breathe 6s ease-in-out infinite",
          }}
        />

        <motion.div
          className="container relative z-10 py-20 md:py-32"
          style={reduced ? {} : { y: heroY, opacity: heroOpacity }}
        >
          <div className="max-w-2xl">
            {/* Eyebrow chip */}
            <motion.div
              className="mb-5"
              initial={reduced ? {} : { opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1, ease: [0, 0, 0.2, 1] }}
            >
              <span className="inline-flex items-center gap-2 rounded-full border border-primary-foreground/15 bg-primary-foreground/10 px-3.5 py-1.5 text-caption font-medium backdrop-blur-sm">
                <Sparkles className="h-3.5 w-3.5 text-secondary" />
                {isAr ? "منصة تجميع الوظائف الذكية" : "AI-powered jobs aggregator"}
              </span>
            </motion.div>

            {/* H1 */}
            <motion.h1
              className="text-display leading-[1.08] mb-5"
              initial={reduced ? {} : { opacity: 0, y: 60, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{
                type: "spring",
                stiffness: 80,
                damping: 18,
                mass: 1.2,
                delay: 0.2,
              }}
            >
              {isAr ? "بحث واحد." : "One search."}
            </motion.h1>

            {/* Subtitle */}
            <motion.p
              className="text-display leading-[1.08] mb-5 font-light text-secondary"
              initial={reduced ? {} : { opacity: 0, y: 50, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{
                type: "spring",
                stiffness: 80,
                damping: 18,
                mass: 1.2,
                delay: 0.35,
              }}
            >
              {isAr ? "كل الفرص." : "Every opportunity."}
            </motion.p>

            {/* Body text */}
            <motion.p
              className="text-body-lg opacity-75 mb-10 max-w-lg"
              initial={reduced ? {} : { opacity: 0, y: 20 }}
              animate={{ opacity: 0.75, y: 0 }}
              transition={{ duration: 0.6, delay: 0.5, ease: [0, 0, 0.2, 1] }}
            >
              {isAr
                ? "اكتشف آلاف الوظائف المجمعة من أفضل المنصات في منطقة الشرق الأوسط وشمال أفريقيا."
                : "Discover thousands of jobs aggregated from top platforms across MENA. No more tab overload."}
            </motion.p>

            {/* Search bar */}
            <motion.div
              initial={reduced ? {} : { opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.6, ease: [0, 0, 0.2, 1] }}
            >
              <SmartSearch
                query={query}
                setQuery={setQuery}
                onSubmit={handleSearch}
              />
            </motion.div>

            {/* Trust micro-row */}
            <motion.div
              className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2 text-caption text-primary-foreground/70"
              initial={reduced ? {} : { opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.75, ease: [0, 0, 0.2, 1] }}
            >
              {[
                isAr ? "تقديم مباشر للمصدر" : "Direct-to-source apply",
                isAr ? "بدون وسطاء" : "No middleman",
                isAr ? "تحديث مستمر" : "Continuously verified",
              ].map((t) => (
                <span key={t} className="inline-flex items-center gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-secondary" />
                  {t}
                </span>
              ))}
            </motion.div>
          </div>

          {/* AI career-coach persona */}
          <div className="hidden lg:flex absolute end-4 xl:end-10 top-1/2 -translate-y-1/2 w-[400px] xl:w-[440px] items-center justify-center">
            <HeroAssistant />
          </div>
        </motion.div>
      </section>

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
                <span className="eyebrow mb-3">{isAr ? "التصنيفات" : "Categories"}</span>
                <h2 className="text-heading-2 mt-3">{isAr ? "تصفح حسب التصنيف" : "Browse by Category"}</h2>
                <p className="text-body text-muted-foreground mt-1">{isAr ? "اختر المجال الذي يناسبك" : "Find roles in your preferred industry"}</p>
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

      {/* ═══ EMPLOYER CTA ═══ */}
      <section className="section-y">
        <div className="container">
          <div className="card-premium relative overflow-hidden mx-auto max-w-4xl text-center p-10 md:p-14">
            <div className="glow-blob" style={{ width: 300, height: 300, top: -100, insetInlineEnd: -60, background: "hsl(var(--primary) / 0.12)" }} />
            <div className="icon-tile relative mx-auto mb-5 h-14 w-14">
              <Building2 className="h-6 w-6 text-primary" />
            </div>
            <h2 className="text-heading-2 mb-3 relative">
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

      {/* ═══ CTA BANNER ═══ */}
      <motion.section
        className="hero-gradient hero-grid relative overflow-hidden text-primary-foreground"
        initial={reduced ? {} : { opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
      >
        <div className="glow-blob" style={{ width: 380, height: 380, top: -120, insetInlineStart: "40%", background: "hsl(var(--secondary) / 0.25)" }} />
        <WatermarkBackground variant="drift" opacity={0.04} inheritColor />
        <div className="container relative z-10 py-16 text-center">
          {isAuthenticated ? (
            <>
              <motion.div
                initial={reduced ? {} : { scale: 0.8, opacity: 0 }}
                whileInView={{ scale: 1, opacity: 0.6 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 200, damping: 20, delay: 0.1 }}
              >
                <Bell className="h-10 w-10 mx-auto mb-4" />
              </motion.div>
              <motion.h2
                className="text-heading-1 mb-3"
                initial={reduced ? {} : { opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                {isAr ? "لا تفوت أي فرصة" : "Never miss an opportunity"}
              </motion.h2>
              <motion.p
                className="text-body-lg opacity-75 mb-8 max-w-md mx-auto"
                initial={reduced ? {} : { opacity: 0, y: 16 }}
                whileInView={{ opacity: 0.75, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.3 }}
              >
                {isAr ? "أنشئ تنبيهاً واحصل على إشعار فوري عند توفر وظيفة مناسبة" : "Create an alert and get instantly notified when a matching job appears"}
              </motion.p>
              <motion.div
                initial={reduced ? {} : { opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: 0.45 }}
              >
                <Button asChild size="lg" className="bg-secondary text-secondary-foreground hover:bg-secondary/90 press-feedback rounded-xl px-8 h-12 font-medium cta-glow">
                  <Link to="/app/alerts">
                    {isAr ? "أنشئ تنبيهاً مجانياً" : "Create a free alert"} <Arrow className="h-4 w-4 ms-1" />
                  </Link>
                </Button>
              </motion.div>
            </>
          ) : (
            <>
              <motion.div
                initial={reduced ? {} : { scale: 0.8, opacity: 0 }}
                whileInView={{ scale: 1, opacity: 0.6 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 200, damping: 20, delay: 0.1 }}
              >
                <LogIn className="h-10 w-10 mx-auto mb-4" />
              </motion.div>
              <motion.h2
                className="text-heading-1 mb-3"
                initial={reduced ? {} : { opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                {isAr ? "ابدأ رحلتك المهنية" : "Start your career journey"}
              </motion.h2>
              <motion.p
                className="text-body-lg opacity-75 mb-8 max-w-md mx-auto"
                initial={reduced ? {} : { opacity: 0, y: 16 }}
                whileInView={{ opacity: 0.75, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.3 }}
              >
                {isAr
                  ? "أنشئ حساباً مجانياً واحصل على وصول كامل لجميع الوظائف والتنبيهات"
                  : "Create a free account and get full access to all jobs and alerts"}
              </motion.p>
              <motion.div
                initial={reduced ? {} : { opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: 0.45 }}
              >
                <Button asChild size="lg" className="bg-secondary text-secondary-foreground hover:bg-secondary/90 press-feedback rounded-xl px-8 h-12 font-medium cta-glow">
                  <Link to="/login">
                    {isAr ? "سجّل الآن" : "Sign up now"} <Arrow className="h-4 w-4 ms-1" />
                  </Link>
                </Button>
              </motion.div>
            </>
          )}
        </div>
      </motion.section>
    </Layout>
  );
}
