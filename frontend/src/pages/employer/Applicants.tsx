/**
 * Employer Applicants — real applications experience on the existing
 * /employer/applications/ API (list + ?job_id + ?status filters) and the
 * shortlist/reject/status actions. No duplicate logic: everything goes through
 * services/employer.ts which wraps the audited backend endpoints.
 *
 * Backend authorization is authoritative (IsVerifiedEmployer + queryset scoped
 * to the employer's own jobs); this page only renders what the API returns.
 */
import { useMemo, useState } from "react";
import { useSearchParams, Navigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Users, Loader2, AlertCircle, RotateCcw, FileText, Star, X, CheckCircle2, Filter,
} from "lucide-react";
import {
  getApplications, getJobPostings, shortlistApplication, rejectApplication,
  updateApplicationStatus, getEmployerProfile, type JobApplication,
} from "@/services/employer";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useTheme } from "@/hooks/use-theme";

const STATUS_STYLES: Record<string, string> = {
  applied: "bg-info/15 text-info border-info/30",
  viewed: "bg-muted text-muted-foreground border-border",
  reviewing: "bg-warning/15 text-warning-foreground border-warning/30",
  shortlisted: "bg-success/15 text-success border-success/30",
  interview: "bg-primary/15 text-primary border-primary/30",
  rejected: "bg-destructive/15 text-destructive border-destructive/30",
};

const STATUS_FILTERS = [
  { value: "", en: "All", ar: "الكل" },
  { value: "applied", en: "New", ar: "جديد" },
  { value: "viewed", en: "Viewed", ar: "تمت المشاهدة" },
  { value: "shortlisted", en: "Shortlisted", ar: "القائمة المختصرة" },
  { value: "rejected", en: "Rejected", ar: "مرفوض" },
];

export default function Applicants() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const { toast } = useToast();
  const qc = useQueryClient();
  const [params, setParams] = useSearchParams();

  const jobId = params.get("job_id") || "";
  const status = params.get("status") || "";

  // Gate on a verified employer profile; a 404 means onboarding isn't done.
  const { data: profile, isLoading: profileLoading, isError: profileIsError, error: profileError } =
    useQuery({ queryKey: ["employer-profile"], queryFn: getEmployerProfile, retry: false });

  const { data: jobs } = useQuery({
    queryKey: ["employer-jobs"],
    queryFn: getJobPostings,
    enabled: !!profile?.is_verified,
  });

  const {
    data: applicants, isLoading, isError, refetch,
  } = useQuery({
    queryKey: ["employer-applications", jobId, status],
    queryFn: () => getApplications({
      job_id: jobId ? Number(jobId) : undefined,
      status: status || undefined,
    }),
    enabled: !!profile?.is_verified,
  });

  const setFilter = (key: "job_id" | "status", value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value); else next.delete(key);
    setParams(next, { replace: true });
  };

  const shortlistMut = useMutation({
    mutationFn: (id: number) => shortlistApplication(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["employer-applications"] });
      toast({ title: isAr ? "تمت الإضافة للقائمة المختصرة" : "Candidate shortlisted" });
    },
    onError: () => toast({ title: isAr ? "تعذّر التنفيذ" : "Action failed", variant: "destructive" }),
  });
  const rejectMut = useMutation({
    mutationFn: (id: number) => rejectApplication(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["employer-applications"] });
      toast({ title: isAr ? "تم رفض المتقدم" : "Applicant rejected" });
    },
    onError: () => toast({ title: isAr ? "تعذّر التنفيذ" : "Action failed", variant: "destructive" }),
  });
  const viewMut = useMutation({
    mutationFn: (id: number) => updateApplicationStatus(id, "viewed"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["employer-applications"] }),
  });

  const jobOptions = useMemo(
    () => (jobs ?? []).map((j) => ({ id: j.id, title: j.title })),
    [jobs],
  );

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
  if (profileIsError) {
    const s = (profileError as { status?: number } | null)?.status;
    if (s === 404) return <Navigate to="/app/employer/register" replace />;
  }
  if (!profile?.is_verified) {
    return (
      <AppShell>
        <div className="page-shell flex items-center justify-center py-20">
          <div className="surface-card max-w-md text-center p-8">
            <div className="w-14 h-14 bg-warning/15 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-7 h-7 text-warning-foreground" />
            </div>
            <h2 className="text-heading-2 mb-2">{isAr ? "قيد المراجعة" : "Verification pending"}</h2>
            <p className="text-body text-muted-foreground">
              {isAr ? "سيتاح عرض المتقدمين بعد توثيق الحساب." : "Applicants are available once your account is verified."}
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
          title={isAr ? "المتقدمون" : "Applicants"}
          subtitle={profile?.company?.name}
        />

        {/* Filters */}
        <div className="surface-card p-4 mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <select
              value={jobId}
              onChange={(e) => setFilter("job_id", e.target.value)}
              className="h-9 rounded-lg border border-input bg-card px-3 text-body focus:outline-none focus:ring-2 focus:ring-ring"
              aria-label={isAr ? "تصفية حسب الوظيفة" : "Filter by job"}
            >
              <option value="">{isAr ? "كل الوظائف" : "All jobs"}</option>
              {jobOptions.map((j) => (
                <option key={j.id} value={j.id}>{j.title}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {STATUS_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setFilter("status", f.value)}
                className={`rounded-full px-3 py-1.5 text-caption font-medium transition-colors ${
                  status === f.value
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent"
                }`}
              >
                {isAr ? f.ar : f.en}
              </button>
            ))}
          </div>
        </div>

        {/* List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20" role="status" aria-live="polite">
            <Loader2 className="h-7 w-7 animate-spin text-primary" />
          </div>
        ) : isError ? (
          <div className="surface-card flex flex-col items-center justify-center py-16 text-center">
            <AlertCircle className="h-6 w-6 text-destructive mb-3" />
            <p className="text-body text-muted-foreground mb-4">
              {isAr ? "تعذّر تحميل المتقدمين." : "Couldn't load applicants."}
            </p>
            <Button onClick={() => refetch()} variant="outline" className="gap-2">
              <RotateCcw className="h-4 w-4" /> {isAr ? "إعادة المحاولة" : "Try again"}
            </Button>
          </div>
        ) : (applicants?.length ?? 0) === 0 ? (
          <div className="surface-card flex flex-col items-center justify-center py-16 text-center">
            <Users className="h-10 w-10 text-muted-foreground mb-4" />
            <p className="text-body text-muted-foreground">
              {isAr ? "لا يوجد متقدمون مطابقون." : "No applicants match these filters."}
            </p>
          </div>
        ) : (
          <div className="surface-card divide-y divide-border">
            {applicants!.map((a: JobApplication) => (
              <div key={a.id} className="p-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-body-lg font-medium text-foreground truncate">{a.user_name || a.user_email}</h3>
                    <Badge variant="outline" className={STATUS_STYLES[a.status] ?? "bg-muted text-muted-foreground"}>
                      {a.status_display}
                    </Badge>
                  </div>
                  <p className="text-caption text-muted-foreground mt-0.5 truncate">
                    {a.job_title} · {isAr ? "تقدّم في" : "applied"} {new Date(a.applied_at).toLocaleDateString()}
                  </p>
                  {a.user_profile && (
                    <p className="text-caption text-muted-foreground mt-1 truncate">
                      {[a.user_profile.current_position, a.user_profile.location,
                        a.user_profile.years_of_experience != null
                          ? `${a.user_profile.years_of_experience}${isAr ? " سنوات" : "y exp"}` : null]
                        .filter(Boolean).join(" · ")}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {a.cv_url && (
                    <Button asChild variant="outline" size="sm" className="gap-1.5">
                      <a href={a.cv_url} target="_blank" rel="noopener noreferrer" onClick={() => a.status === "applied" && viewMut.mutate(a.id)}>
                        <FileText className="h-3.5 w-3.5" /> {isAr ? "السيرة" : "CV"}
                      </a>
                    </Button>
                  )}
                  {a.status !== "shortlisted" && (
                    <Button size="sm" className="gap-1.5" disabled={shortlistMut.isPending}
                      onClick={() => shortlistMut.mutate(a.id)}>
                      <Star className="h-3.5 w-3.5" /> {isAr ? "قائمة مختصرة" : "Shortlist"}
                    </Button>
                  )}
                  {a.status !== "rejected" && (
                    <Button size="sm" variant="ghost" className="gap-1.5 text-destructive hover:text-destructive"
                      disabled={rejectMut.isPending} onClick={() => rejectMut.mutate(a.id)}>
                      <X className="h-3.5 w-3.5" /> {isAr ? "رفض" : "Reject"}
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
