import { useParams, Link } from "react-router-dom";
import { useState, useEffect } from "react";
import { ArrowLeft, ArrowRight, Globe, MapPin, Building2, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/motion";
import { Layout } from "@/components/Layout";
import { JobCard } from "@/components/JobCard";
import { EmptyState } from "@/components/EmptyState";
import { useSavedJobs } from "@/hooks/use-saved-jobs";
import { useTheme } from "@/hooks/use-theme";
import { usePageMeta } from "@/hooks/use-seo";
import { fetchCompanyBySlug, fetchJobs } from "@/services/jobs";
import type { Company, Job } from "@/services/jobs";

export default function CompanyProfile() {
  const { id } = useParams();
  const [company, setCompany] = useState<Company | null>(null);
  const [companyJobs, setCompanyJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const { isSaved, save, remove } = useSavedJobs();
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const BackArrow = dir === "rtl" ? ArrowRight : ArrowLeft;

  usePageMeta(
    company ? `${company.name} — Jobs & Company Profile` : "Company",
    company?.snippet?.substring(0, 155)
  );

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetchCompanyBySlug(id).then((comp) => {
      setCompany(comp);
      if (comp) {
        return fetchJobs({ company: comp.slug, page_size: 100 }).then((jobsRes) => {
          setCompanyJobs(jobsRes.results ?? []);
        });
      }
    }).catch(() => null).finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      </Layout>
    );
  }

  if (!company) {
    return (
      <Layout>
        <div className="container py-8">
          <EmptyState
            icon={Building2}
            title={isAr ? "الشركة غير موجودة" : "Company not found"}
            description={isAr ? "لم نتمكن من العثور على هذه الشركة" : "We couldn't find this company"}
            actionLabel={isAr ? "تصفح الوظائف" : "Browse jobs"}
            actionHref="/app/jobs"
          />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="border-b bg-surface-1">
        <div className="container py-3 max-w-4xl">
          <Link to="/app/jobs" className="inline-flex items-center gap-1 text-body text-muted-foreground hover:text-foreground">
            <BackArrow className="h-3.5 w-3.5" /> {isAr ? "العودة" : "Back"}
          </Link>
        </div>
      </div>

      <div className="container py-8 max-w-4xl">
        <ScrollReveal>
          <div className="flex items-start gap-5 mb-8">
            {company.logo_url && (
              <img src={company.logo_url} alt={company.name}
                className="h-20 w-20 rounded-2xl shadow-sm object-cover shrink-0" />
            )}
            <div className="flex-1">
              <h1 className="text-heading-1">{company.name}</h1>
              <p className="text-body text-muted-foreground mt-1">{company.snippet}</p>
              <div className="flex items-center gap-3 mt-3 flex-wrap">
                <Badge variant="secondary" className="capitalize">{company.industry}</Badge>
                {company.website && (
                  <a href={company.website} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-caption text-primary hover:underline">
                    <Globe className="h-3 w-3" /> {company.website.replace(/^https?:\/\//, "")}
                  </a>
                )}
              </div>
            </div>
          </div>
        </ScrollReveal>

        <Tabs defaultValue="jobs">
          <TabsList className="mb-6">
            <TabsTrigger value="jobs">
              {isAr ? "الوظائف" : "Jobs"} ({companyJobs.length})
            </TabsTrigger>
            <TabsTrigger value="about">{isAr ? "عن الشركة" : "About"}</TabsTrigger>
          </TabsList>

          <TabsContent value="jobs">
            {companyJobs.length === 0 ? (
              <EmptyState
                icon={Building2}
                title={isAr ? "لا توجد وظائف حالية" : "No open positions"}
                description={isAr ? "لا توجد وظائف متاحة لهذه الشركة حالياً" : "Check back later for new openings"}
              />
            ) : (
              <StaggerContainer className="space-y-3">
                {companyJobs.map((job, i) => (
                  <StaggerItem key={job.id}>
                    <JobCard job={job} isSaved={isSaved(job.id)}
                      onToggleSave={(jid) => (isSaved(jid) ? remove(jid) : save(Number(jid)))} />
                  </StaggerItem>
                ))}
              </StaggerContainer>
            )}
          </TabsContent>

          <TabsContent value="about">
            <Card>
              <CardContent className="p-6">
                {company.about ? (
                  <p className="text-body leading-relaxed text-foreground/80 whitespace-pre-line">{company.about}</p>
                ) : (
                  <p className="text-body text-muted-foreground">{company.snippet || (isAr ? "لا يوجد وصف متاح" : "No description available.")}</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
