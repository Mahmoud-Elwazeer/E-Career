import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Building2, Search, Globe, Loader2, RotateCcw, SearchX, ArrowRight, ArrowLeft } from "lucide-react";
import { Layout } from "@/components/Layout";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { fetchCompanies, type Company } from "@/services/jobs";
import { StaggerContainer, StaggerItem, AnimatedCard } from "@/components/motion";
import { useTheme } from "@/hooks/use-theme";
import { usePageMeta } from "@/hooks/use-seo";

export default function Companies() {
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const [q, setQ] = useState("");

  usePageMeta(
    isAr ? "الشركات" : "Companies",
    isAr ? "تصفّح الشركات التي تُوظّف عبر المنطقة" : "Browse companies hiring across MENA"
  );

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["companies"],
    queryFn: fetchCompanies,
  });

  const companies = useMemo(() => {
    const list: Company[] = data ?? [];
    const term = q.trim().toLowerCase();
    if (!term) return list;
    return list.filter(
      (c) =>
        c.name?.toLowerCase().includes(term) ||
        c.industry?.toLowerCase().includes(term) ||
        c.snippet?.toLowerCase().includes(term)
    );
  }, [data, q]);

  return (
    <Layout>
      {/* Header band */}
      <div className="chamber chamber-grid relative overflow-hidden text-primary-foreground">
        <div className="glow-blob" style={{ width: 320, height: 320, top: -120, insetInlineEnd: "12%", background: "hsl(var(--secondary) / 0.25)" }} />
        <div className="container relative z-10 py-12 md:py-14">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-primary-foreground/15 bg-primary-foreground/10 px-3 py-1 text-caption font-medium backdrop-blur-sm mb-3">
            {isAr ? "الشركات" : "Companies"}
          </span>
          <h1 className="text-display-serif mt-3">{isAr ? "الشركات التي تُوظّف" : "Companies hiring now"}</h1>
          <p className="text-body-lg opacity-80 mt-2">
            {isAr ? "اكتشف الشركات وتعرّف على وظائفها المفتوحة" : "Discover employers and explore their open roles"}
          </p>
        </div>
      </div>

      <div className="container py-8">
        {/* Search */}
        <div className="relative -mt-14 z-20 mb-8 max-w-xl">
          <Search className="absolute start-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={isAr ? "ابحث عن شركة أو قطاع..." : "Search company or industry..."}
            className="ps-11 h-12 rounded-xl border-border/60 bg-card shadow-lg focus-visible:ring-0 focus-visible:ring-offset-0"
          />
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-20" role="status" aria-live="polite">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span className="sr-only">{isAr ? "جاري التحميل" : "Loading"}</span>
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="icon-tile h-12 w-12 mb-4"><Building2 className="h-6 w-6 text-primary" /></div>
            <h3 className="text-heading-3 mb-1">{isAr ? "تعذّر تحميل الشركات" : "Couldn't load companies"}</h3>
            <Button onClick={() => refetch()} className="mt-3 gap-2 press-feedback">
              <RotateCcw className="h-4 w-4" /> {isAr ? "إعادة المحاولة" : "Try again"}
            </Button>
          </div>
        ) : companies.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="icon-tile h-12 w-12 mb-4"><SearchX className="h-6 w-6 text-primary" /></div>
            <h3 className="text-heading-3 mb-1">{isAr ? "لا توجد شركات مطابقة" : "No companies match"}</h3>
            <p className="text-body text-muted-foreground">{isAr ? "جرّب بحثاً مختلفاً" : "Try a different search"}</p>
          </div>
        ) : (
          <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" staggerDelay={0.05}>
            {companies.map((c) => (
              <StaggerItem key={c.id}>
                <AnimatedCard>
                  <Link to={`/app/companies/${c.slug}`} className="card-premium card-accent-top group flex h-full flex-col p-5">
                    <div className="flex items-center gap-3 mb-3">
                      {c.logo_url ? (
                        <img src={c.logo_url} alt="" className="h-12 w-12 rounded-xl object-cover border border-border/60" loading="lazy" />
                      ) : (
                        <span className="icon-tile h-12 w-12 text-body font-semibold text-primary">
                          {c.name?.slice(0, 2).toUpperCase()}
                        </span>
                      )}
                      <div className="min-w-0">
                        <h3 className="text-body font-semibold truncate group-hover:text-primary transition-colors">{c.name}</h3>
                        {c.industry && <p className="text-caption text-muted-foreground truncate">{c.industry}</p>}
                      </div>
                    </div>
                    {c.snippet && <p className="text-body text-muted-foreground line-clamp-2 mb-4">{c.snippet}</p>}
                    <div className="mt-auto flex items-center justify-between">
                      {c.website ? (
                        <span className="inline-flex items-center gap-1 text-caption text-muted-foreground">
                          <Globe className="h-3.5 w-3.5" /> {isAr ? "الموقع" : "Website"}
                        </span>
                      ) : <span />}
                      <span className="inline-flex items-center gap-1 text-caption font-medium text-primary">
                        {isAr ? "عرض" : "View"} <Arrow className="h-3.5 w-3.5 group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5 transition-transform" />
                      </span>
                    </div>
                  </Link>
                </AnimatedCard>
              </StaggerItem>
            ))}
          </StaggerContainer>
        )}
      </div>
    </Layout>
  );
}
