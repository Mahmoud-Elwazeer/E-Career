/**
 * Employer Dashboard Page
 * Phase 3A: Employer Portal — token-based, shell-consistent, bilingual.
 */
import { useQuery } from "@tanstack/react-query";
import { Link, Navigate } from "react-router-dom";
import {
  Plus, Briefcase, Users, Eye, Clock, AlertCircle, Search, Loader2, RotateCcw,
} from "lucide-react";
import { getEmployerProfile, getEmployerStats, getJobPostings } from "@/services/employer";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useTheme } from "@/hooks/use-theme";

const statusBadgeClass: Record<string, string> = {
  published: "bg-success/15 text-success border-success/30",
  pending_review: "bg-warning/15 text-warning-foreground border-warning/30",
  draft: "bg-muted text-muted-foreground border-border",
  closed: "bg-destructive/15 text-destructive border-destructive/30",
  rejected: "bg-destructive/15 text-destructive border-destructive/30",
};

export default function EmployerDashboard() {
  const { lang } = useTheme();
  const isAr = lang === "ar";

  const {
    data: profile,
    isLoading: profileLoading,
    isError: profileIsError,
    error: profileError,
    refetch: refetchProfile,
  } = useQuery({
    queryKey: ["employer-profile"],
    queryFn: getEmployerProfile,
    retry: false,
  });

  const { data: stats } = useQuery({
    queryKey: ["employer-stats"],
    queryFn: getEmployerStats,
    enabled: !!profile?.is_verified,
  });

  const { data: jobs } = useQuery({
    queryKey: ["employer-jobs"],
    queryFn: getJobPostings,
    enabled: !!profile?.is_verified,
  });

  // Loading
  if (profileLoading) {
    return (
      <AppShell>
        <div className="page-shell flex items-center justify-center py-24" role="status" aria-live="polite">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="sr-only">{isAr ? "جاري التحميل" : "Loading"}</span>
        </div>
      </AppShell>
    );
  }

  // Distinguish "no employer profile yet" (404) from a transient/API error.
  if (profileIsError) {
    const status = (profileError as { status?: number } | null)?.status;
    if (status === 404) {
      return <Navigate to="/app/employer/register" replace />;
    }
    return (
      <AppShell>
        <div className="page-shell flex flex-col items-center justify-center py-24 text-center">
          <div className="rounded-full bg-destructive/10 p-3 mb-4">
            <AlertCircle className="h-6 w-6 text-destructive" />
          </div>
          <h2 className="text-heading-2 mb-1">
            {isAr ? "تعذّر تحميل لوحة التحكم" : "Couldn't load your dashboard"}
          </h2>
          <p className="text-body text-muted-foreground mb-4 max-w-sm">
            {isAr
              ? "حدثت مشكلة أثناء جلب بيانات صاحب العمل. حاول مرة أخرى."
              : "Something went wrong loading your employer data. Please try again."}
          </p>
          <Button onClick={() => refetchProfile()} className="gap-2">
            <RotateCcw className="h-4 w-4" />
            {isAr ? "إعادة المحاولة" : "Try again"}
          </Button>
        </div>
      </AppShell>
    );
  }

  // Pending verification
  if (!profile?.is_verified) {
    return (
      <AppShell>
        <div className="page-shell flex items-center justify-center py-20">
          <div className="surface-card max-w-md text-center p-8">
            <div className="w-16 h-16 bg-warning/15 rounded-full flex items-center justify-center mx-auto mb-4">
              <Clock className="w-8 h-8 text-warning-foreground" />
            </div>
            <h2 className="text-heading-2 mb-3">
              {isAr ? "قيد المراجعة" : "Verification pending"}
            </h2>
            <p className="text-body text-muted-foreground mb-6">
              {isAr
                ? "حساب صاحب العمل الخاص بك قيد المراجعة. سنُعلمك فور الموافقة."
                : "Your employer account is pending verification. We'll notify you once approved."}
            </p>
            <p className="text-caption text-muted-foreground">
              {isAr ? "الشركة: " : "Company: "}
              <span className="font-medium text-foreground">{profile?.company?.name}</span>
            </p>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="page-shell">
        <PageHeader
          title={isAr ? "لوحة تحكم صاحب العمل" : "Employer Dashboard"}
          subtitle={profile?.company?.name}
          actions={
            <>
              <Button asChild variant="outline" className="gap-2">
                <Link to="/app/employer/talent-search">
                  <Search className="h-4 w-4" />
                  {isAr ? "بحث المواهب" : "Talent Search"}
                </Link>
              </Button>
              <Button asChild className="gap-2">
                <Link to="/app/employer/post-job">
                  <Plus className="h-4 w-4" />
                  {isAr ? "نشر وظيفة" : "Post New Job"}
                </Link>
              </Button>
            </>
          }
        />

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard icon={Briefcase} value={stats?.jobs?.active_jobs ?? 0} label={isAr ? "وظائف نشطة" : "Active Jobs"} />
          <StatCard icon={Users} value={stats?.applications?.total_applications ?? 0} label={isAr ? "إجمالي المتقدمين" : "Total Applicants"} accent="text-success" />
          <StatCard icon={Eye} value={stats?.engagement?.total_views ?? 0} label={isAr ? "إجمالي المشاهدات" : "Total Views"} accent="text-info" />
          <StatCard icon={AlertCircle} value={stats?.applications?.new_applications ?? 0} label={isAr ? "طلبات جديدة" : "New Applications"} accent="text-warning-foreground" />
        </div>

        {/* Jobs List */}
        <div className="surface-card">
          <div className="p-6 border-b flex items-center justify-between">
            <h2 className="section-heading mb-0">{isAr ? "إعلانات وظائفك" : "Your Job Postings"}</h2>
          </div>

          <div className="divide-y divide-border">
            {jobs?.slice(0, 6).map((job) => (
              <div key={job.id} className="p-5 hover:bg-accent/40 transition-colors">
                <div className="flex items-center justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <h3 className="text-body-lg font-medium text-foreground truncate">{job.title}</h3>
                    <p className="text-body text-muted-foreground mt-0.5">
                      {job.location} • {job.remote_type_display}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-caption text-muted-foreground">
                      <span>{job.applications_count} {isAr ? "متقدم" : "applicants"}</span>
                      <span>{job.views_count} {isAr ? "مشاهدة" : "views"}</span>
                    </div>
                  </div>
                  <Badge variant="outline" className={statusBadgeClass[job.status] ?? "bg-muted text-muted-foreground"}>
                    {job.status_display}
                  </Badge>
                </div>
              </div>
            ))}

            {(!jobs || jobs.length === 0) && (
              <div className="p-12 text-center">
                <Briefcase className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-body text-muted-foreground mb-4">
                  {isAr ? "لم تنشر أي وظائف بعد" : "No jobs posted yet"}
                </p>
                <Button asChild className="gap-2">
                  <Link to="/app/employer/post-job">
                    <Plus className="h-4 w-4" />
                    {isAr ? "أنشئ أول إعلان وظيفة" : "Create Your First Job Posting"}
                  </Link>
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Recent Applications summary */}
        {(stats?.applications?.new_applications ?? 0) > 0 && (
          <div className="surface-card mt-8">
            <div className="p-6 border-b">
              <h2 className="section-heading mb-0">{isAr ? "طلبات حديثة" : "Recent Applications"}</h2>
            </div>
            <div className="p-6">
              <p className="text-body text-muted-foreground">
                {isAr ? "لديك " : "You have "}
                <span className="font-semibold text-warning-foreground">
                  {stats?.applications?.new_applications} {isAr ? "طلب جديد" : "new applications"}
                </span>
                {isAr ? " بانتظار المراجعة." : " waiting for review."}
              </p>
              <Button asChild className="mt-4 gap-2">
                <Link to="/app/employer/talent-search">
                  <Users className="h-4 w-4" />
                  {isAr ? "استعرض المرشحين" : "Review candidates"}
                </Link>
              </Button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
