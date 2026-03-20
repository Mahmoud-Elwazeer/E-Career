import { Link } from "react-router-dom";
import { ArrowRight, ArrowLeft, Briefcase, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollReveal, AnimatedCard } from "@/components/motion";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";
import { useLandingData } from "@/hooks/use-landing-data";
import { Skeleton } from "@/components/ui/skeleton";

export function CompanySpotlight() {
  const { lang, dir } = useTheme();
  const { isAuthenticated } = useAuth();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const { data: landing, isLoading } = useLandingData();

  const spotlight = landing?.companiesWithCounts?.[0];

  if (isLoading) {
    return (
      <section className="py-14 bg-surface-2">
        <div className="container">
          <Skeleton className="h-8 w-48 mb-6" />
          <Skeleton className="h-32 w-full rounded-2xl" />
        </div>
      </section>
    );
  }

  if (!spotlight || spotlight.count === 0) return null;

  const companyPath = isAuthenticated
    ? `/app/companies/${spotlight.company.slug}`
    : "/login";

  return (
    <section className="py-14 bg-surface-2">
      <div className="container">
        <ScrollReveal>
          <div className="mb-8">
            <h2 className="text-heading-2">{isAr ? "شركة مميزة" : "Company Spotlight"}</h2>
            <p className="text-body text-muted-foreground mt-1">
              {isAr ? "تعرّف على أبرز الشركات التي توظف الآن" : "Get to know top companies hiring now"}
            </p>
          </div>
        </ScrollReveal>
        <ScrollReveal delay={0.1}>
          <AnimatedCard>
            <div className="rounded-2xl border bg-card p-6 md:p-8 flex flex-col md:flex-row items-start gap-6">
              <img
                src={spotlight.company.logo_url}
                alt={spotlight.company.name}
                className="h-16 w-16 rounded-xl object-cover shrink-0"
              />
              <div className="flex-1 min-w-0">
                <h3 className="text-heading-3 mb-1">{spotlight.company.name}</h3>
                <p className="text-body text-muted-foreground mb-3 max-w-lg">
                  {spotlight.company.snippet}
                </p>
                <div className="flex items-center gap-4 flex-wrap">
                  <span className="flex items-center gap-1.5 text-body font-medium text-primary">
                    <Briefcase className="h-4 w-4" />
                    {spotlight.count} {isAr ? "وظيفة مفتوحة" : "open positions"}
                  </span>
                  {spotlight.company.website && (
                    <a
                      href={spotlight.company.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-caption text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <ExternalLink className="h-3 w-3" />
                      {isAr ? "الموقع" : "Website"}
                    </a>
                  )}
                </div>
              </div>
              <Button asChild className="shrink-0 rounded-xl press-feedback">
                <Link to={companyPath}>
                  {isAr ? "عرض الملف" : "View Profile"} <Arrow className="h-3.5 w-3.5 ms-1" />
                </Link>
              </Button>
            </div>
          </AnimatedCard>
        </ScrollReveal>
      </div>
    </section>
  );
}
