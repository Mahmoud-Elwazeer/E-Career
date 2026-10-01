/**
 * Employer Analytics — real hiring metrics for the company.
 *
 * All data comes from /employer/profile/analytics/ which aggregates this
 * employer's real JobPosting / JobApplication rows. No fabricated series:
 * the time chart is zero-filled over the window (0 = no real applications that
 * day), the funnel is actual status counts, top jobs are live counts.
 */
import { useState } from "react";
import { Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import { Briefcase, Users, Eye, MousePointerClick, Loader2, AlertCircle, RotateCcw } from "lucide-react";
import { getEmployerAnalytics, type EmployerAnalytics as AnalyticsData } from "@/services/employer";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/use-theme";

const WINDOWS = [7, 30, 90];

const FUNNEL_STAGES: Array<{ key: keyof AnalyticsData["funnel"]; en: string; ar: string; cls: string }> = [
  { key: "applied", en: "Applied", ar: "تقدّم", cls: "bg-primary" },
  { key: "viewed", en: "Viewed", ar: "تمت المشاهدة", cls: "bg-info" },
  { key: "shortlisted", en: "Shortlisted", ar: "قائمة مختصرة", cls: "bg-success" },
  { key: "rejected", en: "Rejected", ar: "مرفوض", cls: "bg-destructive" },
];

export default function EmployerAnalytics() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const [days, setDays] = useState(30);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["employer-analytics", days],
    queryFn: () => getEmployerAnalytics(days),
    retry: false,
  });

  if (isError && (error as { status?: number } | null)?.status === 404) {
    return <Navigate to="/app/employer/register" replace />;
  }

  if (isLoading) {
    return (
      <AppShell>
        <div className="page-shell flex items-center justify-center py-24" role="status" aria-live="polite">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="sr-only">{isAr ? "جاري التحميل" : "Loading"}</span>
        </div>
      </AppShell>
    );
  }

  if (isError) {
    return (
      <AppShell>
        <div className="page-shell flex flex-col items-center justify-center py-24 text-center">
          <div className="rounded-full bg-destructive/10 p-3 mb-4">
            <AlertCircle className="h-6 w-6 text-destructive" />
          </div>
          <h2 className="text-heading-2 mb-1">{isAr ? "تعذّر تحميل التحليلات" : "Couldn't load analytics"}</h2>
          <Button onClick={() => refetch()} className="gap-2 mt-2">
            <RotateCcw className="h-4 w-4" />
            {isAr ? "إعادة المحاولة" : "Try again"}
          </Button>
        </div>
      </AppShell>
    );
  }

  const a = data!;
  const maxFunnel = Math.max(1, a.funnel.applied, a.funnel.viewed, a.funnel.shortlisted, a.funnel.rejected);

  // Chart theme colors from CSS tokens.
  const css = (v: string, fb: string) =>
    typeof window !== "undefined"
      ? getComputedStyle(document.documentElement).getPropertyValue(v).trim() || fb
      : fb;
  const cPrimary = `hsl(${css("--primary", "142 70% 35%")})`;
  const cGrid = `hsl(${css("--border", "214 15% 88%")})`;
  const cMuted = `hsl(${css("--muted-foreground", "215 16% 47%")})`;

  const chartData = a.applications_over_time.map((p) => ({
    date: p.date.slice(5), // MM-DD
    count: p.count,
  }));

  return (
    <AppShell>
      <div className="page-shell">
        <PageHeader
          title={isAr ? "تحليلات التوظيف" : "Hiring Analytics"}
          subtitle={isAr ? "بيانات حقيقية من وظائفك ومتقدميك" : "Real data from your jobs and applicants"}
          actions={
            <div className="flex items-center gap-1 rounded-lg border border-border p-1">
              {WINDOWS.map((w) => (
                <button
                  key={w}
                  onClick={() => setDays(w)}
                  className={`px-3 py-1.5 rounded-md text-caption font-medium transition-colors ${
                    days === w ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent"
                  }`}
                >
                  {w}{isAr ? "ي" : "d"}
                </button>
              ))}
            </div>
          }
        />

        {/* Totals */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard icon={Briefcase} value={a.totals.published_jobs} label={isAr ? "وظائف منشورة" : "Published Jobs"} />
          <StatCard icon={Users} value={a.totals.applications} label={isAr ? "إجمالي المتقدمين" : "Total Applicants"} accent="text-success" />
          <StatCard icon={Eye} value={a.totals.views} label={isAr ? "المشاهدات" : "Views"} accent="text-info" />
          <StatCard icon={MousePointerClick} value={a.totals.clicks} label={isAr ? "النقرات" : "Clicks"} accent="text-warning-foreground" />
        </div>

        {/* Applications over time */}
        <div className="surface-card p-6 mb-8">
          <h2 className="section-heading mb-4">
            {isAr ? `المتقدمون خلال ${a.window_days} يوماً` : `Applications — last ${a.window_days} days`}
          </h2>
          <div className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={cGrid} vertical={false} />
                <XAxis dataKey="date" tick={{ fill: cMuted, fontSize: 11 }} axisLine={{ stroke: cGrid }} tickLine={false} minTickGap={24} />
                <YAxis allowDecimals={false} tick={{ fill: cMuted, fontSize: 12 }} axisLine={false} tickLine={false} width={28} />
                <Tooltip formatter={(v) => [v, isAr ? "متقدمون" : "Applications"]} />
                <Line type="monotone" dataKey="count" stroke={cPrimary} strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Funnel */}
        <div className="surface-card p-6 mb-8">
          <h2 className="section-heading mb-4">{isAr ? "مسار المتقدمين" : "Applicant funnel"}</h2>
          <div className="space-y-3">
            {FUNNEL_STAGES.map((s) => {
              const val = a.funnel[s.key] as number;
              const pct = Math.round((val / maxFunnel) * 100);
              return (
                <div key={s.key}>
                  <div className="flex items-center justify-between text-caption mb-1">
                    <span className="text-muted-foreground">{isAr ? s.ar : s.en}</span>
                    <span className="font-medium text-foreground">{val}</span>
                  </div>
                  <div className="h-2.5 w-full rounded-full bg-muted overflow-hidden">
                    <div className={`h-full rounded-full ${s.cls}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top jobs */}
        <div className="surface-card">
          <div className="p-6 border-b">
            <h2 className="section-heading mb-0">{isAr ? "أفضل الوظائف أداءً" : "Top performing jobs"}</h2>
          </div>
          {a.top_jobs.length === 0 ? (
            <div className="p-10 text-center text-body text-muted-foreground">
              {isAr ? "لا توجد بيانات وظائف بعد." : "No job data yet."}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-body">
                <thead>
                  <tr className="border-b text-caption text-muted-foreground">
                    <th className="text-start p-4 font-medium">{isAr ? "الوظيفة" : "Job"}</th>
                    <th className="text-end p-4 font-medium">{isAr ? "مشاهدات" : "Views"}</th>
                    <th className="text-end p-4 font-medium">{isAr ? "نقرات" : "Clicks"}</th>
                    <th className="text-end p-4 font-medium">{isAr ? "متقدمون" : "Applicants"}</th>
                  </tr>
                </thead>
                <tbody>
                  {a.top_jobs.map((j) => (
                    <tr key={j.id} className="border-b last:border-0">
                      <td className="p-4 font-medium text-foreground">{j.title}</td>
                      <td className="p-4 text-end text-muted-foreground">{j.views}</td>
                      <td className="p-4 text-end text-muted-foreground">{j.clicks}</td>
                      <td className="p-4 text-end font-medium text-foreground">{j.applications}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
