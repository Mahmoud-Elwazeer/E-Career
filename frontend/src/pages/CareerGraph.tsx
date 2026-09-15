import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Network, Search, Loader2, Target, Route as RouteIcon, Sparkles, AlertTriangle } from "lucide-react";
import { Layout } from "@/components/Layout";
import { PageHeader } from "@/components/PageHeader";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { intelligenceApi } from "@/services/intelligence";
import { ScrollReveal } from "@/components/motion";
import { useTheme } from "@/hooks/use-theme";
import { usePageMeta } from "@/hooks/use-seo";

/** Best-effort extraction of a string list from a loosely-typed API payload. */
function toList(v: unknown): string[] {
  if (Array.isArray(v)) {
    return v
      .map((x) => (typeof x === "string" ? x : x?.name || x?.skill || x?.title || x?.label))
      .filter(Boolean) as string[];
  }
  if (v && typeof v === "object") {
    return Object.keys(v as Record<string, unknown>);
  }
  return [];
}

export default function CareerGraph() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const [role, setRole] = useState("");
  const [submitted, setSubmitted] = useState("");

  usePageMeta(
    isAr ? "خريطة المسار المهني" : "Career Graph",
    isAr ? "اكتشف المهارات المطلوبة والفجوات ومسارات النمو" : "Explore required skills, gaps and growth paths for any role"
  );

  const gaps = useMutation({ mutationFn: (r: string) => intelligenceApi.getSkillGaps(r) });
  const roleSkills = useMutation({ mutationFn: (r: string) => intelligenceApi.getRoleSkillsGraph(r) });
  const paths = useMutation({ mutationFn: (r: string) => intelligenceApi.getCareerPathGraph(r) });

  const analyze = (e: React.FormEvent) => {
    e.preventDefault();
    const r = role.trim();
    if (!r) return;
    setSubmitted(r);
    gaps.mutate(r);
    roleSkills.mutate(r);
    paths.mutate(r);
  };

  const busy = gaps.isPending || roleSkills.isPending || paths.isPending;
  const gapList = toList((gaps.data as any)?.missing_skills ?? (gaps.data as any)?.gaps ?? gaps.data);
  const skillList = toList((roleSkills.data as any)?.skills ?? roleSkills.data);
  const pathList = toList((paths.data as any)?.paths ?? (paths.data as any)?.next_roles ?? paths.data);

  return (
    <Layout>
      <div className="page-shell">
        <PageHeader
          title={isAr ? "خريطة المسار المهني" : "Career Graph"}
          subtitle={isAr ? "اكتب دوراً وظيفياً لاكتشاف مهاراته وفجواتك ومسارات نموه." : "Enter a target role to reveal its skills, your gaps, and growth paths."}
        />

        <form onSubmit={analyze} className="mb-8 flex gap-2 max-w-xl">
          <div className="relative flex-1">
            <Search className="absolute start-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder={isAr ? "مثال: مهندس برمجيات أول" : "e.g. Senior Software Engineer"}
              className="ps-11 h-12 rounded-xl"
            />
          </div>
          <Button type="submit" size="lg" disabled={busy || !role.trim()} className="h-12 rounded-xl press-feedback gap-2">
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Network className="h-4 w-4" />}
            {isAr ? "تحليل" : "Analyze"}
          </Button>
        </form>

        {!submitted ? (
          <div className="card-premium flex flex-col items-center justify-center py-16 text-center">
            <div className="icon-tile h-14 w-14 mb-4"><Network className="h-7 w-7 text-primary" /></div>
            <h3 className="text-heading-3 mb-1">{isAr ? "ابدأ بكتابة دور وظيفي" : "Start with a target role"}</h3>
            <p className="text-body text-muted-foreground max-w-sm">
              {isAr ? "سنعرض المهارات المطلوبة، والفجوات لديك، ومسارات التقدّم الممكنة." : "We'll show required skills, your gaps, and possible advancement paths."}
            </p>
          </div>
        ) : (
          <div className="grid gap-5 lg:grid-cols-3">
            <GraphCard
              icon={Target}
              title={isAr ? "المهارات المطلوبة" : "Required skills"}
              loading={roleSkills.isPending}
              error={roleSkills.isError}
              items={skillList}
              empty={isAr ? "لا توجد بيانات مهارات لهذا الدور بعد." : "No skill data for this role yet."}
              tone="primary"
            />
            <GraphCard
              icon={Sparkles}
              title={isAr ? "فجوات مهاراتك" : "Your skill gaps"}
              loading={gaps.isPending}
              error={gaps.isError}
              items={gapList}
              empty={isAr ? "لا توجد فجوات محسوبة (أكمل ملفك لنتائج أدق)." : "No computed gaps yet (complete your profile for sharper results)."}
              tone="warning"
            />
            <GraphCard
              icon={RouteIcon}
              title={isAr ? "مسارات النمو" : "Growth paths"}
              loading={paths.isPending}
              error={paths.isError}
              items={pathList}
              empty={isAr ? "لا توجد مسارات مقترحة بعد." : "No suggested paths yet."}
              tone="neutral"
            />
          </div>
        )}
      </div>
    </Layout>
  );
}

function GraphCard({
  icon: Icon, title, loading, error, items, empty, tone,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string; loading: boolean; error: boolean; items: string[]; empty: string;
  tone: "primary" | "warning" | "neutral";
}) {
  const chip =
    tone === "warning"
      ? "bg-warning/10 text-warning border-warning/20"
      : tone === "primary"
      ? "bg-primary/10 text-primary border-primary/20"
      : "bg-secondary/40 text-secondary-foreground border-border";

  return (
    <ScrollReveal>
      <div className="card-premium p-6 h-full">
        <div className="flex items-center gap-2.5 mb-4">
          <span className="icon-tile h-9 w-9"><Icon className="h-4 w-4 text-primary" /></span>
          <h3 className="text-heading-3 font-semibold">{title}</h3>
        </div>
        {loading ? (
          <div className="flex items-center gap-2 text-muted-foreground py-6"><Loader2 className="h-4 w-4 animate-spin" /> …</div>
        ) : error ? (
          <div className="flex items-center gap-2 text-muted-foreground py-6"><AlertTriangle className="h-4 w-4" /> —</div>
        ) : items.length === 0 ? (
          <p className="text-body text-muted-foreground py-2">{empty}</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {items.slice(0, 24).map((s, i) => (
              <span key={`${s}-${i}`} className={`rounded-full border px-3 py-1 text-caption font-medium ${chip}`}>{s}</span>
            ))}
          </div>
        )}
      </div>
    </ScrollReveal>
  );
}
