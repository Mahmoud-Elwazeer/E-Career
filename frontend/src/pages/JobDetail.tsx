import { useParams, Link } from "react-router-dom";
import { useRef, useEffect, useState } from "react";
import {
  ArrowLeft, ArrowRight, MapPin, Clock, Bookmark, BookmarkCheck,
  Building2, Globe, DollarSign, Briefcase, Calendar, Share2, Loader2,
} from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Layout } from "@/components/Layout";
import { JobCard } from "@/components/JobCard";
import { EmptyState } from "@/components/EmptyState";
import { ApplyNowButton } from "@/components/ApplyNowButton";
import { ReadingProgress, SectionReveal, JobCardMotion } from "@/components/motion";
import { fetchJobBySlug, fetchSimilarJobs, logApplyClick } from "@/services/jobs";
import { useSavedJobs } from "@/hooks/use-saved-jobs";
import { useTheme } from "@/hooks/use-theme";
import { useJobStructuredData, usePageMeta, useBreadcrumbStructuredData } from "@/hooks/use-seo";
import { formatDistanceToNow } from "date-fns";
import type { Job } from "@/services/jobs";

function JobHeader({ job, isAr, reduced, expired }: any) {
  const company = job.company;
  const locationClass = `location-${job.location_type}`;
  return (
    <div>
      <div className="flex items-start gap-4">
        {(company?.logo_url || job.company_logo) && (
          <motion.img
            layoutId={reduced ? undefined : `job-${job.id}-logo`}
            src={company?.logo_url || job.company_logo}
            alt={company?.name || job.company_name}
            className="h-16 w-16 rounded-xl shadow-sm"
            loading="lazy"
            transition={{ type: "spring", stiffness: 300, damping: 26 }}
          />
        )}
        <div className="flex-1">
          <h1 className="text-heading-1">
            <motion.span
              layoutId={reduced ? undefined : `job-${job.id}-title`}
              transition={{ type: "spring", stiffness: 300, damping: 26 }}
            >
              {job.title}
            </motion.span>
          </h1>
          <Link
            to={`/app/companies/${company?.slug || job.company_slug}`}
            className="text-body-lg text-muted-foreground hover:text-primary transition-colors link-underline"
          >
            {company?.name || job.company_name}
          </Link>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 mt-5">
        <Badge variant="secondary" className="gap-1 rounded-lg px-3 py-1">
          <MapPin className="h-3 w-3" />{job.location}
        </Badge>
        <span className={`px-3 py-1 rounded-lg text-caption font-medium border ${locationClass}`}>
          {job.location_type}
        </span>
        <Badge variant="outline" className="rounded-lg px-3 py-1">{job.experience_level} level</Badge>
        <Badge variant="outline" className="rounded-lg px-3 py-1">{job.industry}</Badge>
        {expired && (
          <Badge variant="destructive" className="rounded-lg px-3 py-1">
            {isAr ? "ربما انتهت صلاحيته" : "May have expired"}
          </Badge>
        )}
      </div>
    </div>
  );
}

function OverviewGrid({ job, isAr }: any) {
  const items = [
    {
      icon: DollarSign,
      label: isAr ? "الراتب" : "Salary",
      value:
        job.salary_min && job.salary_max
          ? `${job.salary_min.toLocaleString()}–${job.salary_max.toLocaleString()} ${job.salary_currency ?? ""}`
          : isAr ? "غير معلن" : "Not disclosed",
    },
    { icon: Briefcase, label: isAr ? "الخبرة" : "Experience", value: job.experience_level },
    { icon: MapPin, label: isAr ? "النوع" : "Type", value: job.location_type },
    {
      icon: Calendar,
      label: isAr ? "تاريخ النشر" : "Posted",
      value: formatDistanceToNow(new Date(job.posted_at), { addSuffix: true }),
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      {items.map((item) => (
        <div key={item.label} className="bg-surface-2 rounded-xl p-4">
          <item.icon className="h-4 w-4 text-primary mb-2" />
          <p className="text-caption text-muted-foreground">{item.label}</p>
          <p className="text-body font-medium mt-0.5 capitalize">{item.value}</p>
        </div>
      ))}
    </div>
  );
}

function SidebarCard({ job, expired, saved, isAr, onToggleSave, onApplyClick }: any) {
  const company = job.company;
  const source = job.source;
  return (
    <div className="hidden lg:block sticky top-20">
      <Card className="shadow-lg border-primary/10">
        <CardContent className="p-6 space-y-4">
          <ApplyNowButton
            href={job.source_url}
            disabled={expired}
            disabledLabel={isAr ? "انتهت صلاحية الإعلان" : "Listing Expired"}
            className="w-full"
          />
          <div className="flex gap-2">
            <Button variant="outline" className="flex-1 rounded-xl press-feedback" onClick={onToggleSave}>
              {saved ? <BookmarkCheck className="h-4 w-4 me-1.5 text-primary" /> : <Bookmark className="h-4 w-4 me-1.5" />}
              {saved ? (isAr ? "تم الحفظ" : "Saved") : (isAr ? "حفظ" : "Save")}
            </Button>
            <Button variant="outline" size="icon" className="rounded-xl press-feedback shrink-0">
              <Share2 className="h-4 w-4" />
            </Button>
          </div>
          <Separator />
          <div className="text-caption text-muted-foreground space-y-2">
            <p className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" />
              {isAr ? "نُشرت" : "Posted"} {formatDistanceToNow(new Date(job.posted_at), { addSuffix: true })}
            </p>
            {job.deadline && (
              <p className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5" />
                {isAr ? "الموعد النهائي:" : "Deadline:"} {new Date(job.deadline).toLocaleDateString()}
              </p>
            )}
            {source && (
              <p className="flex items-center gap-1.5">
                <Globe className="h-3.5 w-3.5" />
                {isAr ? "المصدر:" : "Source:"} {source.name}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {company && (
        <Card className="mt-4">
          <CardContent className="p-5">
            <div className="flex items-center gap-3 mb-3">
              {company.logo_url && <img src={company.logo_url} alt={company.name} className="h-10 w-10 rounded-lg" />}
              <div>
                <h3 className="text-body font-medium">{company.name}</h3>
                <p className="text-caption text-muted-foreground">{company.industry}</p>
              </div>
            </div>
            <p className="text-caption text-muted-foreground leading-relaxed">{company.snippet}</p>
            <div className="flex gap-2 mt-3">
              <Button variant="outline" size="sm" className="flex-1 rounded-lg press-feedback text-caption" asChild>
                <Link to={`/app/companies/${company.slug}`}>
                  <Building2 className="h-3 w-3 me-1" /> {isAr ? "عرض الشركة" : "View Company"}
                </Link>
              </Button>
              {company.website && (
                <Button variant="outline" size="sm" className="rounded-lg press-feedback text-caption" asChild>
                  <a href={company.website} target="_blank" rel="noopener noreferrer">
                    <Globe className="h-3 w-3" />
                  </a>
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function JobDetail() {
  const { id } = useParams();
  const [job, setJob] = useState<Job | null>(null);
  const [similarJobs, setSimilarJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const { isSaved, save, remove } = useSavedJobs();
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const BackArrow = dir === "rtl" ? ArrowRight : ArrowLeft;
  const reduced = useReducedMotion();
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetchJobBySlug(id)
      .then((data) => {
        setJob(data);
        fetchSimilarJobs(id).then(setSimilarJobs).catch(() => {});
      })
      .catch(() => setJob(null))
      .finally(() => setLoading(false));
  }, [id]);

  useJobStructuredData(job);
  useBreadcrumbStructuredData(
    job
      ? [
          { name: "Home", url: "/" },
          { name: "Jobs", url: "/app/jobs" },
          { name: job.title, url: `/app/jobs/${job.slug}` },
        ]
      : []
  );
  usePageMeta(
    job ? `${job.title} at ${job.company_name}` : "Job not found",
    job?.description?.substring(0, 155)
  );

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      </Layout>
    );
  }

  if (!job) {
    return (
      <Layout>
        <div className="container py-8 max-w-4xl">
          <EmptyState
            icon={Briefcase}
            title={isAr ? "الوظيفة غير موجودة" : "Job not found"}
            description={isAr ? "ربما تم إزالة هذا الإعلان" : "This listing may have been removed"}
            actionLabel={isAr ? "تصفح الوظائف" : "Browse all jobs"}
            actionHref="/app/jobs"
          />
        </div>
      </Layout>
    );
  }

  const expired = job.deadline ? new Date(job.deadline) < new Date() : false;
  const saved = isSaved(job.id);
  const tags = job.tags ?? [];

  const handleApplyClick = async () => {
    try {
      const result = await logApplyClick(job.slug);
      if (result.source_url) window.open(result.source_url, "_blank", "noopener,noreferrer");
    } catch {
      window.open(job.source_url, "_blank", "noopener,noreferrer");
    }
  };

  return (
    <Layout>
      <ReadingProgress containerRef={contentRef} />
      <div className="border-b bg-surface-1">
        <div className="container py-3 max-w-5xl">
          <nav className="hidden md:flex items-center gap-1.5 text-caption text-muted-foreground">
            <Link to="/" className="hover:text-foreground transition-colors">{isAr ? "الرئيسية" : "Home"}</Link>
            <span className="opacity-40">/</span>
            <Link to="/app/jobs" className="hover:text-foreground transition-colors">{isAr ? "الوظائف" : "Jobs"}</Link>
            <span className="opacity-40">/</span>
            <span className="text-foreground truncate max-w-[300px]">{job.title}</span>
          </nav>
          <Link to="/app/jobs" className="md:hidden inline-flex items-center gap-1 text-body text-muted-foreground hover:text-foreground">
            <BackArrow className="h-3.5 w-3.5" /> {isAr ? "العودة للوظائف" : "Back to jobs"}
          </Link>
        </div>
      </div>

      <div ref={contentRef} className="container py-8 max-w-5xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            <JobHeader job={job} isAr={isAr} reduced={reduced} expired={expired} />
            <SectionReveal><OverviewGrid job={job} isAr={isAr} /></SectionReveal>
            <Separator />
            <SectionReveal delay={0.05}>
              <section>
                <h2 className="text-heading-3 mb-4">{isAr ? "الوصف" : "Description"}</h2>
                <p className="text-body leading-[1.8] text-foreground/80 whitespace-pre-line">{job.description}</p>
              </section>
            </SectionReveal>
            {tags.length > 0 && (
              <>
                <Separator />
                <SectionReveal delay={0.05}>
                  <section>
                    <h2 className="text-heading-3 mb-4">{isAr ? "المهارات" : "Skills"}</h2>
                    <div className="flex flex-wrap gap-2">
                      {tags.map((tag) => (
                        <Badge key={tag.id} variant="secondary" className="rounded-lg px-3 py-1.5 text-body font-normal">
                          {tag.name}
                        </Badge>
                      ))}
                    </div>
                  </section>
                </SectionReveal>
              </>
            )}
            {similarJobs.length > 0 && (
              <>
                <Separator />
                <SectionReveal delay={0.08}>
                  <section>
                    <h2 className="text-heading-3 mb-4">{isAr ? "وظائف مشابهة" : "Similar Jobs"}</h2>
                    <div className="space-y-3">
                      {similarJobs.map((sJob, i) => (
                        <JobCardMotion key={sJob.id} index={i} staggerLimit={3}>
                          <JobCard job={sJob} isSaved={isSaved(sJob.id)} onToggleSave={(jid) => (isSaved(jid) ? remove(jid) : save(Number(jid)))} />
                        </JobCardMotion>
                      ))}
                    </div>
                  </section>
                </SectionReveal>
              </>
            )}
          </div>
          <div className="space-y-4">
            <SidebarCard job={job} expired={expired} saved={saved} isAr={isAr}
              onToggleSave={() => (saved ? remove(job.id) : save(job.id))}
              onApplyClick={handleApplyClick}
            />
          </div>
        </div>
      </div>

      <div className="lg:hidden fixed bottom-0 inset-x-0 border-t bg-card/95 glass p-3 z-40">
        <div className="flex gap-2 max-w-lg mx-auto">
          <Button variant="outline" size="icon" className="shrink-0 h-11 w-11 rounded-xl press-feedback"
            onClick={() => (saved ? remove(job.id) : save(job.id))}>
            {saved ? <BookmarkCheck className="h-4 w-4 text-primary" /> : <Bookmark className="h-4 w-4" />}
          </Button>
          <div onClick={handleApplyClick} className="flex-1">
            <ApplyNowButton href={job.source_url} disabled={expired} disabledLabel={isAr ? "انتهت" : "Expired"} size="compact" className="w-full" />
          </div>
        </div>
      </div>
      <div className="lg:hidden h-16" />
    </Layout>
  );
}
