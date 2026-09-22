/**
 * Talent Score — career intelligence dashboard.
 *
 * Surfaces the full intelligence the backend computes: overall grade + AI
 * confidence, per-dimension score with grade/trend/evidence/explanation
 * (drill-down), a strengths-vs-gaps framing, historical trend, and prioritized,
 * DEEP-LINKED recommended actions. Theme-aware (no hardcoded hex), shelled
 * loading/error/empty states, React Query, and bilingual.
 */
import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Trophy, TrendingUp, TrendingDown, Target, Code, Briefcase, GraduationCap,
  MessageSquare, Activity, CheckCircle2, AlertCircle, ArrowRight, ArrowLeft,
  RefreshCw, Loader2, Sparkles, ChevronDown, Info,
} from "lucide-react";
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import scoresApi, {
  calculateGrade, gradeToken, trendTokenText, priorityToken,
  type ScoreBreakdown,
} from "@/services/scores";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useTheme } from "@/hooks/use-theme";
import { useToast } from "@/hooks/use-toast";
import { MOTION } from "@/lib/motion-tokens";
import { cn } from "@/lib/utils";

type DimKey =
  | "skill_score" | "experience_score" | "education_score" | "portfolio_score"
  | "growth_score" | "communication_score" | "interview_score";

/** Dimension metadata — label + icon + a token color CLASS (no hex) + the page
 *  a related action should deep-link to. */
const DIMENSIONS: Record<DimKey, { en: string; ar: string; icon: typeof Code; link: string }> = {
  skill_score:         { en: "Skills",        ar: "المهارات",   icon: Code,          link: "/app/skills" },
  experience_score:    { en: "Experience",    ar: "الخبرة",     icon: Briefcase,     link: "/app/profile" },
  education_score:     { en: "Education",      ar: "التعليم",    icon: GraduationCap, link: "/app/profile" },
  portfolio_score:     { en: "Portfolio",     ar: "الأعمال",    icon: Target,        link: "/app/profile" },
  growth_score:        { en: "Growth",        ar: "النمو",      icon: TrendingUp,    link: "/app/recommendations" },
  communication_score: { en: "Communication", ar: "التواصل",    icon: MessageSquare, link: "/app/resume" },
  interview_score:     { en: "Interview",     ar: "المقابلات",  icon: Activity,      link: "/app/interviews" },
};

/** Deep-link target for a recommended action, by the dimension it targets. */
function actionLink(dimension: string): string {
  return (DIMENSIONS as Record<string, { link: string }>)[dimension]?.link ?? "/app/profile";
}

/** Read a theme CSS variable as an hsl() string so recharts adapts to the theme. */
function cssVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v ? `hsl(${v})` : fallback;
}

export default function TalentScore() {
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [openDim, setOpenDim] = useState<string | null>(null);

  const scoresQuery = useQuery({ queryKey: ["talent-scores"], queryFn: scoresApi.getScores, retry: false });
  const trendsQuery = useQuery({ queryKey: ["talent-trends"], queryFn: scoresApi.getScoreTrends, retry: false });
  const actionsQuery = useQuery({ queryKey: ["talent-actions"], queryFn: scoresApi.getAllScoresWithActions, retry: false });

  const recalc = useMutation({
    mutationFn: scoresApi.recalculateScores,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["talent-scores"] });
      queryClient.invalidateQueries({ queryKey: ["talent-trends"] });
      queryClient.invalidateQueries({ queryKey: ["talent-actions"] });
      toast({ title: isAr ? "تم التحديث" : "Recalculated", description: isAr ? "تم تحديث نقاطك." : "Your scores were refreshed." });
    },
    onError: () =>
      toast({ title: isAr ? "خطأ" : "Error", description: isAr ? "تعذّر إعادة الحساب." : "Couldn't recalculate.", variant: "destructive" }),
  });

  const scores = scoresQuery.data;
  const trends = trendsQuery.data;
  const dimensions = actionsQuery.data?.dimensions ?? {};
  const actions = actionsQuery.data?.actions ?? [];

  const isLoading = scoresQuery.isLoading || actionsQuery.isLoading;
  const isError = scoresQuery.isError && actionsQuery.isError;

  const overallPct = scores ? Math.round(scores.overall_score * 100) : 0;
  const overallGrade = scores ? calculateGrade(scores.overall_score) : "F";
  const gradeCls = gradeToken(overallGrade);
  const trendDir = trends?.trend_direction ?? "insufficient_data";
  const aiConfidence = scores ? Math.round((scores.ai_confidence ?? 0) * 100) : 0;

  // Dimension rows sorted high→low for a strengths/gaps framing.
  const dimRows = useMemo(() => {
    const bd = scores?.dimension_breakdown;
    if (!bd) return [];
    return (Object.keys(DIMENSIONS) as DimKey[])
      .filter((k) => bd[k] !== undefined)
      .map((k) => ({ key: k, value: bd[k], meta: DIMENSIONS[k], detail: dimensions[k] as ScoreBreakdown | undefined }))
      .sort((a, b) => b.value - a.value);
  }, [scores, dimensions]);

  const strengths = dimRows.slice(0, 2);
  const gaps = [...dimRows].reverse().slice(0, 2);

  const radarData = dimRows.map((d) => ({ subject: isAr ? d.meta.ar : d.meta.en, A: Math.round(d.value * 100), fullMark: 100 }));

  const history = scores?.score_history ?? [];
  const historyData = history.map((h) => ({
    date: new Date(h.date).toLocaleDateString(isAr ? "ar" : "en", { month: "short", day: "numeric" }),
    score: Math.round(h.overall_score * 100),
  }));

  // Theme-aware chart colors (read once per render).
  const cPrimary = cssVar("--primary", "#0A3836");
  const cGrid = cssVar("--border", "#e5e7eb");
  const cMuted = cssVar("--muted-foreground", "#6b7280");

  // ── Loading ──────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <AppShell>
        <div className="page-shell">
          <PageHeader title={isAr ? "نقاط الموهبة" : "Talent Score"} subtitle={isAr ? "ملف ذكائك المهني" : "Your career intelligence profile"} />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="skeleton h-56 lg:col-span-1 rounded-2xl" />
            <div className="skeleton h-56 lg:col-span-2 rounded-2xl" />
          </div>
          <div className="mt-6 flex items-center justify-center py-8" role="status" aria-live="polite">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span className="sr-only">{isAr ? "جاري التحميل" : "Loading"}</span>
          </div>
        </div>
      </AppShell>
    );
  }

  // ── Error ────────────────────────────────────────────────────────────────
  if (isError) {
    return (
      <AppShell>
        <div className="page-shell">
          <PageHeader title={isAr ? "نقاط الموهبة" : "Talent Score"} />
          <div className="surface-card flex flex-col items-center justify-center py-20 text-center">
            <AlertCircle className="h-10 w-10 text-destructive mb-3" />
            <h2 className="text-heading-3 mb-1">{isAr ? "تعذّر تحميل النقاط" : "Couldn't load your scores"}</h2>
            <p className="text-body text-muted-foreground mb-4 max-w-sm">
              {isAr ? "أكمل ملفك أو حاول مرة أخرى." : "Complete your profile or try again."}
            </p>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => { scoresQuery.refetch(); actionsQuery.refetch(); }}>
                {isAr ? "إعادة المحاولة" : "Retry"}
              </Button>
              <Button asChild>
                <Link to="/app/profile">{isAr ? "أكمل ملفك" : "Complete profile"}</Link>
              </Button>
            </div>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="page-shell">
        <PageHeader
          title={isAr ? "نقاط الموهبة" : "Talent Score"}
          subtitle={isAr ? "ملف ذكائك المهني — نقاط قوتك وفجواتك وخطواتك التالية" : "Your career intelligence — strengths, gaps, and next steps"}
          actions={
            <Button variant="outline" className="gap-2" onClick={() => recalc.mutate()} disabled={recalc.isPending}>
              <RefreshCw className={cn("h-4 w-4", recalc.isPending && "animate-spin")} />
              {isAr ? "إعادة الحساب" : "Recalculate"}
            </Button>
          }
        />

        {/* Overall + strengths/gaps */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Overall score */}
          <motion.div {...MOTION.presets.fadeUp} className={cn("chamber chamber-grid relative overflow-hidden rounded-2xl p-6 flex flex-col items-center justify-center text-center", "lg:col-span-1")}>
            <div className="relative z-10">
              <div className="inline-flex items-center gap-1.5 text-caption font-medium text-primary-foreground/80 mb-3">
                <Trophy className="h-4 w-4" />
                {isAr ? "النتيجة الإجمالية" : "Overall Career Score"}
              </div>
              <div className="font-mono-data text-6xl font-bold text-primary-foreground leading-none">
                {overallPct}<span className="text-2xl align-top">%</span>
              </div>
              <div className="mt-3 flex items-center justify-center gap-2">
                <span className={cn("inline-flex h-8 min-w-8 items-center justify-center rounded-full px-2.5 text-lg font-bold", gradeCls.bg, gradeCls.text)}>
                  {overallGrade}
                </span>
                <span className={cn("inline-flex items-center gap-1 text-caption font-medium",
                  trendDir === "improving" ? "text-success" : trendDir === "declining" ? "text-destructive" : "text-primary-foreground/70")}>
                  {trendDir === "improving" && <TrendingUp className="h-3.5 w-3.5" />}
                  {trendDir === "declining" && <TrendingDown className="h-3.5 w-3.5" />}
                  {trendDir === "stable" && <Activity className="h-3.5 w-3.5" />}
                  {isAr ? "" : trendDir.replace(/_/g, " ")}
                </span>
              </div>
              {aiConfidence > 0 && (
                <p className="mt-3 inline-flex items-center gap-1.5 text-caption text-primary-foreground/70">
                  <Sparkles className="h-3.5 w-3.5" />
                  {isAr ? `ثقة الذكاء الاصطناعي ${aiConfidence}%` : `AI confidence ${aiConfidence}%`}
                </p>
              )}
              {scores?.last_calculated_at && (
                <p className="mt-1 text-[11px] text-primary-foreground/50">
                  {isAr ? "آخر تحديث " : "Updated "}
                  {new Date(scores.last_calculated_at).toLocaleDateString(isAr ? "ar" : "en")}
                </p>
              )}
            </div>
          </motion.div>

          {/* Radar */}
          <motion.div
            initial={MOTION.presets.fadeUp.initial}
            animate={MOTION.presets.fadeUp.animate}
            transition={{ ...MOTION.presets.fadeUp.transition, delay: 0.05 }}
            className="surface-card p-5 lg:col-span-2"
          >
            <h2 className="text-heading-3 mb-2">{isAr ? "توزّع النقاط" : "Score breakdown"}</h2>
            <div className="h-[300px]">
              {radarData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="72%" data={radarData}>
                    <PolarGrid stroke={cGrid} />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: cMuted, fontSize: 12 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                    <Radar name={isAr ? "نقاطك" : "Your score"} dataKey="A" stroke={cPrimary} fill={cPrimary} fillOpacity={0.35} />
                    <Tooltip
                      contentStyle={{ background: cssVar("--card", "#fff"), border: `1px solid ${cGrid}`, borderRadius: 12, color: cssVar("--foreground", "#111") }}
                      formatter={(v) => [`${v}%`, isAr ? "النتيجة" : "Score"]}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground text-body">
                  {isAr ? "لا توجد بيانات كافية بعد." : "Not enough data yet."}
                </div>
              )}
            </div>
          </motion.div>
        </div>

        {/* Strengths vs gaps */}
        {dimRows.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="surface-card p-5">
              <h3 className="text-body font-semibold text-success mb-3 flex items-center gap-2">
                <TrendingUp className="h-4 w-4" /> {isAr ? "أقوى نقاطك" : "Your strengths"}
              </h3>
              <ul className="space-y-2">
                {strengths.map((d) => (
                  <li key={d.key} className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-body"><d.meta.icon className="h-4 w-4 text-success" />{isAr ? d.meta.ar : d.meta.en}</span>
                    <span className="font-mono-data text-body font-semibold">{Math.round(d.value * 100)}%</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="surface-card p-5">
              <h3 className="text-body font-semibold text-warning-foreground mb-3 flex items-center gap-2">
                <Target className="h-4 w-4" /> {isAr ? "فرص التحسين" : "Biggest opportunities"}
              </h3>
              <ul className="space-y-2">
                {gaps.map((d) => (
                  <li key={d.key} className="flex items-center justify-between">
                    <Link to={d.meta.link} className="flex items-center gap-2 text-body hover:text-primary transition-colors">
                      <d.meta.icon className="h-4 w-4 text-warning-foreground" />{isAr ? d.meta.ar : d.meta.en}
                    </Link>
                    <span className="font-mono-data text-body font-semibold">{Math.round(d.value * 100)}%</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Per-dimension detail (drill-down: grade/trend/evidence/explanation) */}
        <motion.div {...MOTION.presets.fadeUp} className="surface-card mb-6">
          <div className="p-5 border-b border-border">
            <h2 className="text-heading-3">{isAr ? "تفاصيل الأبعاد" : "Dimension detail"}</h2>
          </div>
          <div className="divide-y divide-border">
            {dimRows.map((d) => {
              const detail = d.detail;
              const grade = detail?.grade ?? calculateGrade(d.value);
              const gc = gradeToken(grade);
              const isOpen = openDim === d.key;
              return (
                <div key={d.key}>
                  <button
                    onClick={() => setOpenDim(isOpen ? null : d.key)}
                    className="w-full flex items-center gap-4 p-4 text-start hover:bg-accent/40 transition-colors"
                    aria-expanded={isOpen}
                  >
                    <span className="icon-tile p-2 shrink-0"><d.meta.icon className="h-4 w-4 text-primary" /></span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-3 mb-1.5">
                        <span className="text-body font-medium">{isAr ? d.meta.ar : d.meta.en}</span>
                        <span className="flex items-center gap-2 shrink-0">
                          {detail?.trend && (
                            <span className={cn("text-caption", trendTokenText(detail.trend))}>
                              {detail.trend === "improving" ? "↑" : detail.trend === "declining" ? "↓" : "→"}
                            </span>
                          )}
                          <span className={cn("inline-flex h-6 min-w-6 items-center justify-center rounded-full px-2 text-caption font-bold", gc.bg, gc.text)}>{grade}</span>
                          <span className="font-mono-data text-body font-semibold w-10 text-end">{Math.round(d.value * 100)}%</span>
                        </span>
                      </div>
                      <Progress value={Math.round(d.value * 100)} className="h-1.5" />
                    </div>
                    <ChevronDown className={cn("h-4 w-4 text-muted-foreground transition-transform shrink-0", isOpen && "rotate-180")} />
                  </button>

                  {isOpen && (
                    <div className="px-4 pb-4 ps-16 space-y-3">
                      {detail?.explanation ? (
                        <p className="text-body text-muted-foreground">{detail.explanation}</p>
                      ) : (
                        <p className="text-body text-muted-foreground flex items-center gap-1.5">
                          <Info className="h-3.5 w-3.5" />
                          {isAr ? "أكمل ملفك للحصول على تحليل مفصّل." : "Complete your profile for a detailed breakdown."}
                        </p>
                      )}
                      {detail?.evidence && detail.evidence.length > 0 && (
                        <ul className="flex flex-wrap gap-2">
                          {detail.evidence.slice(0, 6).map((e, i) => (
                            <li key={i} className="pill-tag text-[11px]">
                              {e.description}{typeof e.count === "number" ? ` · ${e.count}` : ""}
                            </li>
                          ))}
                        </ul>
                      )}
                      {detail?.confidence !== undefined && (
                        <p className="text-caption text-muted-foreground inline-flex items-center gap-1.5">
                          <Sparkles className="h-3 w-3" />
                          {isAr ? `الثقة ${Math.round(detail.confidence * 100)}%` : `Confidence ${Math.round(detail.confidence * 100)}%`}
                        </p>
                      )}
                      <Button asChild variant="outline" size="sm" className="gap-1">
                        <Link to={d.meta.link}>
                          {isAr ? "تحسين هذا البعد" : "Improve this"}
                          <Arrow className="h-3.5 w-3.5" />
                        </Link>
                      </Button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* History trend (only real historical data) */}
        {historyData.length > 1 && (
          <motion.div {...MOTION.presets.fadeUp} className="surface-card p-5 mb-6">
            <h2 className="text-heading-3 mb-2">{isAr ? "تطوّر نتيجتك" : "Your score over time"}</h2>
            <div className="h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={cGrid} vertical={false} />
                  <XAxis dataKey="date" tick={{ fill: cMuted, fontSize: 12 }} axisLine={{ stroke: cGrid }} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: cMuted, fontSize: 12 }} axisLine={false} tickLine={false} width={32} />
                  <Tooltip
                    contentStyle={{ background: cssVar("--card", "#fff"), border: `1px solid ${cGrid}`, borderRadius: 12, color: cssVar("--foreground", "#111") }}
                    formatter={(v) => [`${v}%`, isAr ? "النتيجة" : "Score"]}
                  />
                  <Line type="monotone" dataKey="score" stroke={cPrimary} strokeWidth={2.5} dot={{ r: 3, fill: cPrimary }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}

        {/* Recommended actions — deep-linked */}
        {actions.length > 0 && (
          <motion.div {...MOTION.presets.fadeUp} className="surface-card">
            <div className="p-5 border-b border-border">
              <h2 className="text-heading-3">{isAr ? "خطوات موصى بها" : "Recommended next steps"}</h2>
            </div>
            <div className="divide-y divide-border">
              {actions.slice(0, 6).map((action, i) => {
                const pc = priorityToken(action.priority);
                const to = actionLink(action.dimension);
                return (
                  <Link key={i} to={to} className="flex items-start gap-3 p-4 hover:bg-accent/40 transition-colors group">
                    <span className={cn("flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center", pc.bg, pc.text)}>
                      {action.priority === "high" ? <AlertCircle className="w-4 h-4" /> : action.priority === "medium" ? <Target className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-0.5">
                        <h4 className="text-body font-medium">{action.title}</h4>
                        <Badge variant="outline" className={cn("shrink-0", pc.text)}>{action.priority}</Badge>
                      </div>
                      <p className="text-caption text-muted-foreground">{action.description}</p>
                    </div>
                    <Arrow className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors shrink-0 mt-1" />
                  </Link>
                );
              })}
            </div>
          </motion.div>
        )}
      </div>
    </AppShell>
  );
}
