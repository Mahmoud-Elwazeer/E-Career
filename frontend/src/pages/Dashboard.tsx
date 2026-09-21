/**
 * Dashboard — the individual user's home after login.
 *
 * Previously the app had no home screen and dropped users straight onto the
 * jobs list. This aggregates the real, existing signals — profile completeness,
 * top recommendations, application status — from endpoints that already exist,
 * plus quick actions into the core journey. No new backend, no fabricated data:
 * every number here comes from a real API and every empty state is honest.
 */
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Briefcase, FileText, Sparkles, Target, ArrowRight, ArrowLeft,
  ClipboardList, TrendingUp, Loader2, AlertCircle, CheckCircle2, Clock,
} from "lucide-react";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { MOTION } from "@/lib/motion-tokens";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";
import { apiRequest } from "@/services/client";
import { profileApi, type ProfileCompletion } from "@/services/profile";
import { getRecommendations, type RecommendedJob } from "@/services/recommendations";

interface DashboardApplication {
  id: string;
  status: "pending" | "reviewing" | "interview" | "rejected" | "accepted";
  job?: { id?: string; title?: string; company?: { name?: string } };
}

const STATUS_META: Record<
  DashboardApplication["status"],
  { en: string; ar: string; className: string }
> = {
  pending: { en: "Pending", ar: "قيد الانتظار", className: "bg-warning/10 text-warning-foreground border-warning/30" },
  reviewing: { en: "Reviewing", ar: "قيد المراجعة", className: "bg-info/10 text-info border-info/30" },
  interview: { en: "Interview", ar: "مقابلة", className: "bg-primary/10 text-primary border-primary/30" },
  rejected: { en: "Closed", ar: "مغلق", className: "bg-destructive/10 text-destructive border-destructive/30" },
  accepted: { en: "Accepted", ar: "مقبول", className: "bg-success/10 text-success border-success/30" },
};

export default function Dashboard() {
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const { user } = useAuth();
  const firstName = (user?.name || "").split(" ")[0];

  const completionQuery = useQuery({
    queryKey: ["profile-completion"],
    queryFn: () => profileApi.getCompletion(),
    retry: false,
  });

  const recsQuery = useQuery({
    queryKey: ["dashboard-recommendations"],
    queryFn: () => getRecommendations(4, 60),
    retry: false,
  });

  const appsQuery = useQuery({
    queryKey: ["dashboard-applications"],
    queryFn: async () => {
      const res = await apiRequest<DashboardApplication[] | { results: DashboardApplication[] }>(
        "/users/me/applications/"
      );
      return Array.isArray(res) ? res : res?.results ?? [];
    },
    retry: false,
  });

  const completion: ProfileCompletion | undefined = completionQuery.data;
  const recs: RecommendedJob[] = recsQuery.data?.recommendations ?? [];
  const apps: DashboardApplication[] = appsQuery.data ?? [];

  const activeApps = apps.filter((a) => a.status !== "rejected");
  const interviewCount = apps.filter((a) => a.status === "interview").length;
  const completionPct = Math.round(completion?.total_score ?? 0);

  const greeting = isAr
    ? firstName ? `أهلاً، ${firstName}` : "أهلاً بك"
    : firstName ? `Welcome back, ${firstName}` : "Welcome back";

  return (
    <AppShell>
      <div className="page-shell">
        <PageHeader
          title={greeting}
          subtitle={isAr ? "نظرة سريعة على رحلتك المهنية" : "A quick view of your career journey"}
          actions={
            <Button asChild className="gap-2">
              <Link to="/app/jobs">
                <Briefcase className="h-4 w-4" />
                {isAr ? "تصفح الوظائف" : "Browse jobs"}
              </Link>
            </Button>
          }
        />

        {/* Stat row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={Target}
            value={completionQuery.isLoading ? "…" : `${completionPct}%`}
            label={isAr ? "اكتمال الملف" : "Profile complete"}
          />
          <StatCard
            icon={Sparkles}
            value={recsQuery.isLoading ? "…" : recs.length}
            label={isAr ? "توصيات جديدة" : "New matches"}
            accent="text-signal"
          />
          <StatCard
            icon={ClipboardList}
            value={appsQuery.isLoading ? "…" : activeApps.length}
            label={isAr ? "طلبات نشطة" : "Active applications"}
            accent="text-info"
          />
          <StatCard
            icon={CheckCircle2}
            value={appsQuery.isLoading ? "…" : interviewCount}
            label={isAr ? "مقابلات" : "Interviews"}
            accent="text-success"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: recommendations */}
          <motion.section {...MOTION.presets.fadeUp} className="lg:col-span-2 space-y-6">
            <div className="surface-card">
              <div className="flex items-center justify-between p-5 border-b border-border">
                <h2 className="text-heading-3 flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-signal" />
                  {isAr ? "موصى بها لك" : "Recommended for you"}
                </h2>
                <Button asChild variant="ghost" size="sm" className="gap-1">
                  <Link to="/app/recommendations">
                    {isAr ? "الكل" : "See all"}
                    <Arrow className="h-3.5 w-3.5" />
                  </Link>
                </Button>
              </div>

              <div className="divide-y divide-border">
                {recsQuery.isLoading ? (
                  <div className="flex items-center justify-center py-12" role="status">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  </div>
                ) : recsQuery.isError ? (
                  <div className="p-8 text-center">
                    <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
                    <p className="text-body text-muted-foreground mb-3">
                      {isAr ? "تعذّر تحميل التوصيات." : "Couldn't load recommendations."}
                    </p>
                    <Button variant="outline" size="sm" onClick={() => recsQuery.refetch()}>
                      {isAr ? "إعادة المحاولة" : "Retry"}
                    </Button>
                  </div>
                ) : recs.length === 0 ? (
                  <div className="p-8 text-center">
                    <Target className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                    <p className="text-body text-muted-foreground mb-3">
                      {isAr
                        ? "أكمل ملفك للحصول على توصيات مخصصة."
                        : "Complete your profile to unlock personalized matches."}
                    </p>
                    <Button asChild variant="outline" size="sm">
                      <Link to="/app/profile">{isAr ? "أكمل ملفك" : "Complete profile"}</Link>
                    </Button>
                  </div>
                ) : (
                  recs.map((r) => (
                    <Link
                      key={r.job_id}
                      to={`/app/jobs/${r.job_id}`}
                      className="flex items-center justify-between gap-4 p-5 hover:bg-accent/40 transition-colors"
                    >
                      <div className="min-w-0">
                        <p className="text-body font-medium text-foreground truncate">{r.job_title}</p>
                        <p className="text-caption text-muted-foreground truncate">
                          {r.company_name}{r.location ? ` • ${r.location}` : ""}
                        </p>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="font-mono-data text-body font-semibold text-primary">
                          {Math.round(r.score)}%
                        </span>
                        <Arrow className="h-4 w-4 text-muted-foreground" />
                      </div>
                    </Link>
                  ))
                )}
              </div>
            </div>

            {/* Recent applications */}
            <div className="surface-card">
              <div className="flex items-center justify-between p-5 border-b border-border">
                <h2 className="text-heading-3 flex items-center gap-2">
                  <ClipboardList className="h-5 w-5 text-info" />
                  {isAr ? "طلباتك الأخيرة" : "Recent applications"}
                </h2>
                <Button asChild variant="ghost" size="sm" className="gap-1">
                  <Link to="/app/applications">
                    {isAr ? "الكل" : "See all"}
                    <Arrow className="h-3.5 w-3.5" />
                  </Link>
                </Button>
              </div>
              <div className="divide-y divide-border">
                {appsQuery.isLoading ? (
                  <div className="flex items-center justify-center py-10" role="status">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  </div>
                ) : apps.length === 0 ? (
                  <div className="p-8 text-center">
                    <Briefcase className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                    <p className="text-body text-muted-foreground mb-3">
                      {isAr ? "لم تتقدم لأي وظيفة بعد." : "You haven't applied to any jobs yet."}
                    </p>
                    <Button asChild variant="outline" size="sm">
                      <Link to="/app/jobs">{isAr ? "ابدأ التقديم" : "Find jobs to apply"}</Link>
                    </Button>
                  </div>
                ) : (
                  apps.slice(0, 5).map((a) => {
                    const meta = STATUS_META[a.status] ?? STATUS_META.pending;
                    return (
                      <Link
                        key={a.id}
                        to={a.job?.id ? `/app/jobs/${a.job.id}` : "/app/applications"}
                        className="flex items-center justify-between gap-4 p-5 hover:bg-accent/40 transition-colors"
                      >
                        <div className="min-w-0">
                          <p className="text-body font-medium text-foreground truncate">
                            {a.job?.title ?? (isAr ? "وظيفة" : "Job")}
                          </p>
                          <p className="text-caption text-muted-foreground truncate">
                            {a.job?.company?.name ?? ""}
                          </p>
                        </div>
                        <Badge variant="outline" className={meta.className}>
                          {isAr ? meta.ar : meta.en}
                        </Badge>
                      </Link>
                    );
                  })
                )}
              </div>
            </div>
          </motion.section>

          {/* Right: profile completeness + quick actions */}
          <motion.aside
            initial={MOTION.presets.fadeUp.initial}
            animate={MOTION.presets.fadeUp.animate}
            transition={{ ...MOTION.presets.fadeUp.transition, delay: 0.08 }}
            className="space-y-6"
          >
            <div className="surface-card p-5">
              <h2 className="text-heading-3 flex items-center gap-2 mb-4">
                <Target className="h-5 w-5 text-primary" />
                {isAr ? "اكتمال الملف" : "Profile strength"}
              </h2>
              {completionQuery.isLoading ? (
                <div className="flex items-center justify-center py-6" role="status">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                </div>
              ) : (
                <>
                  <div className="flex items-end justify-between mb-2">
                    <span className="font-mono-data text-display-serif text-primary leading-none">
                      {completionPct}%
                    </span>
                    {completion?.is_complete && (
                      <span className="pill-tag pill-tag-signal">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        {isAr ? "مكتمل" : "Complete"}
                      </span>
                    )}
                  </div>
                  <Progress value={completionPct} className="h-2 mb-4" />
                  {completion?.sections && (
                    <ul className="space-y-2">
                      {Object.entries(completion.sections)
                        .filter(([, s]) => !s.complete)
                        .slice(0, 4)
                        .map(([key, s]) => (
                          <li key={key} className="flex items-center gap-2 text-caption text-muted-foreground">
                            <Clock className="h-3.5 w-3.5 text-warning-foreground shrink-0" />
                            {s.label}
                          </li>
                        ))}
                    </ul>
                  )}
                  <Button asChild variant="outline" size="sm" className="w-full mt-4 gap-1">
                    <Link to="/app/profile">
                      {isAr ? "تحسين الملف" : "Improve profile"}
                      <Arrow className="h-3.5 w-3.5" />
                    </Link>
                  </Button>
                </>
              )}
            </div>

            {/* Quick actions */}
            <div className="surface-card p-5">
              <h2 className="text-heading-3 mb-4">{isAr ? "إجراءات سريعة" : "Quick actions"}</h2>
              <div className="grid grid-cols-1 gap-2">
                {[
                  { to: "/app/resume", icon: FileText, en: "Build your resume", ar: "أنشئ سيرتك الذاتية" },
                  { to: "/app/cover-letters", icon: FileText, en: "Write a cover letter", ar: "اكتب خطاب تغطية" },
                  { to: "/app/interviews", icon: TrendingUp, en: "Practice interviews", ar: "تدرّب على المقابلات" },
                  { to: "/app/rashid", icon: Sparkles, en: "Ask Rasheed", ar: "اسأل رشيد" },
                ].map((a) => (
                  <Link
                    key={a.to}
                    to={a.to}
                    className="surface-card-interactive flex items-center justify-between gap-3 p-3 group"
                  >
                    <span className="flex items-center gap-3 text-body">
                      <span className="icon-tile p-2">
                        <a.icon className="h-4 w-4 text-primary" />
                      </span>
                      {isAr ? a.ar : a.en}
                    </span>
                    <Arrow className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                  </Link>
                ))}
              </div>
            </div>
          </motion.aside>
        </div>
      </div>
    </AppShell>
  );
}
