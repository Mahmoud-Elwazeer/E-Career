import { useState, useMemo, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { SlidersHorizontal, X, ArrowUpDown, SearchX, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet";
import { Layout } from "@/components/Layout";
import { JobCard } from "@/components/JobCard";
import { EmptyState } from "@/components/EmptyState";
import { AnimatedFilterChipList, SearchBarMotion, JobCardMotion } from "@/components/motion";
import { fetchJobs } from "@/services/jobs";
import { logSearch } from "@/lib/api";
import { useSavedJobs } from "@/hooks/use-saved-jobs";
import { useTheme } from "@/hooks/use-theme";
import { usePageMeta } from "@/hooks/use-seo";
import type { Job } from "@/services/jobs";

const ITEMS_PER_PAGE = 8;
type SortOption = "latest" | "salary-high" | "salary-low";

function FilterControls({
  locationType, industry, experienceLevel, setParam
}: {
  locationType: string; industry: string; experienceLevel: string;
  setParam: (k: string, v: string) => void;
}) {
  const { lang } = useTheme();
  const isAr = lang === "ar";

  return (
    <div className="space-y-4">
      <h3 className="text-body font-medium">{isAr ? "عوامل التصفية" : "Filters"}</h3>
      <div>
        <label className="text-caption text-muted-foreground mb-1.5 block">{isAr ? "نوع الموقع" : "Location Type"}</label>
        <Select value={locationType || "all"} onValueChange={(v) => setParam("locationType", v === "all" ? "" : v)}>
          <SelectTrigger className="text-body"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{isAr ? "الكل" : "All Types"}</SelectItem>
            <SelectItem value="remote">{isAr ? "عن بعد" : "Remote"}</SelectItem>
            <SelectItem value="hybrid">{isAr ? "هجين" : "Hybrid"}</SelectItem>
            <SelectItem value="onsite">{isAr ? "في المقر" : "On-site"}</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <label className="text-caption text-muted-foreground mb-1.5 block">{isAr ? "القطاع" : "Industry"}</label>
        <Select value={industry || "all"} onValueChange={(v) => setParam("industry", v === "all" ? "" : v)}>
          <SelectTrigger className="text-body"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{isAr ? "كل القطاعات" : "All Industries"}</SelectItem>
            <SelectItem value="technology">{isAr ? "التكنولوجيا" : "Technology"}</SelectItem>
            <SelectItem value="finance">{isAr ? "المالية" : "Finance"}</SelectItem>
            <SelectItem value="healthcare">{isAr ? "الرعاية الصحية" : "Healthcare"}</SelectItem>
            <SelectItem value="education">{isAr ? "التعليم" : "Education"}</SelectItem>
            <SelectItem value="marketing">{isAr ? "التسويق" : "Marketing"}</SelectItem>
            <SelectItem value="engineering">{isAr ? "الهندسة" : "Engineering"}</SelectItem>
            <SelectItem value="design">{isAr ? "التصميم" : "Design"}</SelectItem>
            <SelectItem value="sales">{isAr ? "المبيعات" : "Sales"}</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <label className="text-caption text-muted-foreground mb-1.5 block">{isAr ? "مستوى الخبرة" : "Experience"}</label>
        <Select value={experienceLevel || "all"} onValueChange={(v) => setParam("experienceLevel", v === "all" ? "" : v)}>
          <SelectTrigger className="text-body"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{isAr ? "كل المستويات" : "All Levels"}</SelectItem>
            <SelectItem value="entry">{isAr ? "مبتدئ" : "Entry Level"}</SelectItem>
            <SelectItem value="mid">{isAr ? "متوسط" : "Mid Level"}</SelectItem>
            <SelectItem value="senior">{isAr ? "خبير" : "Senior"}</SelectItem>
            <SelectItem value="lead">{isAr ? "قائد" : "Lead"}</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}

export default function Jobs() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [sort, setSort] = useState<SortOption>("latest");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const searchTimeout = useRef<ReturnType<typeof setTimeout>>();

  usePageMeta(
    isAr ? "تصفح الوظائف" : "Browse Jobs",
    isAr ? "اكتشف فرص العمل من مصادر متعددة" : "Discover job opportunities from multiple sources across MENA"
  );

  const q = searchParams.get("q") || "";
  const locationType = searchParams.get("locationType") || "";
  const industry = searchParams.get("industry") || "";
  const experienceLevel = searchParams.get("experienceLevel") || "";
  const page = parseInt(searchParams.get("page") || "1", 10);

  const { isSaved, save, remove } = useSavedJobs();

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    next.set("page", "1");
    setSearchParams(next);
  };

  const clearFilters = () => setSearchParams({});

  // Fetch jobs from DB
  useEffect(() => {
    setLoading(true);
    fetchJobs({
      q: q || undefined,
      work_mode: locationType || undefined,
      industry: industry || undefined,
      seniority: experienceLevel || undefined,
      page,
      page_size: ITEMS_PER_PAGE,
      ordering: sort === 'latest' ? '-posted_at' : sort === 'salary-high' ? '-salary_max' : 'salary_min',
    }).then((res) => {
      const data = res.results ?? [];
      const count = res.count ?? 0;
      setJobs(data);
      setTotal(count);
      setLoading(false);
    }).catch(() => setLoading(false));

    return () => clearTimeout(searchTimeout.current);
  }, [q, locationType, industry, experienceLevel, page, sort]);

  const activeFilters = [
    locationType && { key: "locationType", label: locationType },
    industry && { key: "industry", label: industry },
    experienceLevel && { key: "experienceLevel", label: experienceLevel },
  ].filter(Boolean) as { key: string; label: string }[];

  const totalPages = Math.ceil(total / ITEMS_PER_PAGE);
  const hasFilters = !!(q || locationType || industry || experienceLevel);

  return (
    <Layout>
      <div className="container py-8">
        <div className="flex gap-2 mb-4">
          <SearchBarMotion>
            <Input
              value={q}
              onChange={(e) => setParam("q", e.target.value)}
              placeholder={isAr ? "ابحث عن وظائف..." : "Search jobs..."}
              className="ps-11 h-11 rounded-xl border-border/60 focus-visible:ring-0 focus-visible:ring-offset-0"
            />
          </SearchBarMotion>
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" className="md:hidden h-11 w-11 rounded-xl shrink-0">
                <SlidersHorizontal className="h-4 w-4" />
              </Button>
            </SheetTrigger>
            <SheetContent side="bottom" className="rounded-t-2xl max-h-[70vh]">
              <SheetTitle>{isAr ? "عوامل التصفية" : "Filters"}</SheetTitle>
              <div className="mt-4">
                <FilterControls locationType={locationType} industry={industry} experienceLevel={experienceLevel} setParam={setParam} />
                {hasFilters && (
                  <Button variant="outline" onClick={clearFilters} className="w-full mt-4">
                    <X className="h-3 w-3 me-1" /> {isAr ? "مسح الكل" : "Clear all"}
                  </Button>
                )}
              </div>
            </SheetContent>
          </Sheet>
        </div>

        {activeFilters.length > 0 && (
          <div className="mb-4">
            <AnimatedFilterChipList
              filters={activeFilters}
              onRemove={(key) => setParam(key, "")}
              onClearAll={clearFilters}
              clearLabel={isAr ? "مسح الكل" : "Clear all"}
            />
          </div>
        )}

        <div className="flex gap-6">
          <aside className="hidden md:block w-56 shrink-0 space-y-4">
            <FilterControls locationType={locationType} industry={industry} experienceLevel={experienceLevel} setParam={setParam} />
            {hasFilters && (
              <button onClick={clearFilters} className="text-caption text-primary hover:underline flex items-center gap-1">
                <X className="h-3 w-3" /> {isAr ? "مسح الكل" : "Clear all"}
              </button>
            )}
          </aside>

          <div className="flex-1">
            <div className="flex items-center justify-between mb-4">
              <p className="text-body text-muted-foreground">
                {loading ? "..." : `${total} ${isAr ? "وظيفة" : `job${total !== 1 ? "s" : ""} found`}`}
              </p>
              <Select value={sort} onValueChange={(v) => setSort(v as SortOption)}>
                <SelectTrigger className="w-auto gap-1 text-caption border-0 bg-transparent">
                  <ArrowUpDown className="h-3 w-3" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="latest">{isAr ? "الأحدث" : "Latest"}</SelectItem>
                  <SelectItem value="salary-high">{isAr ? "الراتب (الأعلى)" : "Salary (High)"}</SelectItem>
                  <SelectItem value="salary-low">{isAr ? "الراتب (الأقل)" : "Salary (Low)"}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            ) : jobs.length > 0 ? (
              <div className="space-y-3">
                {jobs.map((job, index) => (
                  <JobCardMotion key={job.id} index={index} staggerLimit={ITEMS_PER_PAGE}>
                    <JobCard
                      job={job}
                      isSaved={isSaved(job.id)}
                      onToggleSave={(id) => (isSaved(id) ? remove(id) : save(id))}
                    />
                  </JobCardMotion>
                ))}
              </div>
            ) : (
              <EmptyState
                icon={SearchX}
                title={isAr ? "لا توجد وظائف تطابق عوامل التصفية" : "No jobs match your filters"}
                description={isAr ? "حاول تعديل بحثك أو عوامل التصفية" : "Try adjusting your search or filters"}
                actionLabel={isAr ? "مسح الفلاتر" : "Clear filters"}
                actionHref="/app/jobs"
              />
            )}

            {totalPages > 1 && (
              <div className="flex justify-center gap-2 mt-8">
                <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setParam("page", String(page - 1))} className="press-feedback">
                  {isAr ? "السابق" : "Prev"}
                </Button>
                {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => (
                  <Button key={i} variant={page === i + 1 ? "default" : "outline"} size="sm" onClick={() => setParam("page", String(i + 1))} className="press-feedback w-9">
                    {i + 1}
                  </Button>
                ))}
                <Button variant="outline" size="sm" disabled={page === totalPages} onClick={() => setParam("page", String(page + 1))} className="press-feedback">
                  {isAr ? "التالي" : "Next"}
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
