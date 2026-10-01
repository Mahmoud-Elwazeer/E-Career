/**
 * Employer Dashboard Page
 * Phase 3A: Employer Portal — token-based, shell-consistent, bilingual.
 */
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, Navigate } from "react-router-dom";
import {
  Plus, Briefcase, Users, Eye, Clock, AlertCircle, Search, Loader2, RotateCcw, CheckCircle2,
} from "lucide-react";
import { getEmployerProfile, getEmployerStats, getJobPostings, requestVerification } from "@/services/employer";
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
  const queryClient = useQueryClient();
  const [verifyNote, setVerifyNote] = useState("");

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

  const verifyMutation = useMutation({
    mutationFn: (note?: string) => requestVerification(note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["employer-profile"] });
    },
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

  // Pending verification — actionable: the employer can submit a real
  // verification request (persisted + emits an admin event), and the screen
  // reflects whether a request is already on record.
  if (!profile?.is_verified) {
    const alreadyRequested = Boolean(profile?.verification_requested_at) || verifyMutation.isSuccess;
    return (
      <AppShell>
        <div className="page-shell flex items-center justify-center py-20">
          <div className="surface-card max-w-md text-center p-8">
            <div className="w-16 h-16 bg-warning/15 rounded-full flex items-center justify-center mx-auto mb-4">
              {alreadyRequested ? (
                <CheckCircle2 className="w-8 h-8 text-success" />
              ) : (
                <Clock className="w-8 h-8 text-warning-foreground" />
              )}
            </div>
            <h2 className="text-heading-2 mb-3">
              {alreadyRequested
                ? (isAr ? "تم استلام طلبك" : "Verification requested")
                : (isAr ? "التحقق مطلوب" : "Verify your company")}
            </h2>
            <p className="text-body text-muted-foreground mb-4">
              {alreadyRequested
                ? (isAr
                    ? "طلب التحقق قيد المراجعة من قبل الإدارة. سنُعلمك فور الموافقة."
                    : "Your verification request is being reviewed. We'll notify you once approved.")
                : (isAr
                    ? "قبل نشر الوظائف، اطلب التحقق من شركتك. يمكنك إضافة أي معلومات تساعد المراجعة."
                    : "Before posting jobs, request verification for your company. Add any context that helps the review.")}
            </p>
            <p className="text-caption text-muted-foreground mb-5">
              {isAr ? "الشركة: " : "Company: "}
              <span className="font-medium text-foreground">{profile?.company?.name}</span>
            </p>

            {!alreadyRequested && (
              <div className="text-start">
                <textarea
                  value={verifyNote}
                  onChange={(e) => setVerifyNote(e.target.value)}
                  rows={3}
                  placeholder={isAr
                    ? "اختياري: نطاق الشركة، موقعها، أو أي دليل يدعم التحقق"
                    : "Optional: company domain, website, or any evidence to support verification"}
                  className="w-full px-4 py-3 border border-input rounded-lg focus:ring-2 focus:ring-ring mb-3 text-body"
                />
                {verifyMutation.isError && (
                  <p className="text-caption text-destructive mb-3">
                    {(verifyMutation.error as { message?: string } | null)?.message
                      ?? (isAr ? "تعذّر إرسال الطلب." : "Could not submit the request.")}
                  </p>
                )}
                <Button
                  className="w-full gap-2"
                  disabled={verifyMutation.isPending}
                  onClick={() => verifyMutation.mutate(verifyNote.trim() || undefined)}
                >
                  {verifyMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  {isAr ? "طلب التحقق" : "Request verification"}
                </Button>
              </div>
            )}
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
              <Link
                key={job.id}
                to={`/app/employer/jobs/${job.id}/edit`}
                className="block p-5 hover:bg-accent/40 transition-colors"
              >
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
              </Link>
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
                <Link to="/app/employer/applicants?status=applied">
                  <Users className="h-4 w-4" />
                  {isAr ? "استعرض المتقدمين" : "Review applicants"}
                </Link>
              </Button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
