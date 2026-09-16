import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Sparkles, Search, Loader2, Layers, ChevronRight, X } from "lucide-react";
import { Layout } from "@/components/Layout";
import { Input } from "@/components/ui/input";
import { StaggerContainer, StaggerItem, AnimatedCard } from "@/components/motion";
import { skillsApi, type Skill } from "@/services/skills";
import { useTheme } from "@/hooks/use-theme";
import { usePageMeta } from "@/hooks/use-seo";

export default function SkillsExplorer() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const [q, setQ] = useState("");
  const [term, setTerm] = useState("");
  const [selected, setSelected] = useState<Skill | null>(null);

  usePageMeta(
    isAr ? "مستكشف المهارات" : "Skills Explorer",
    isAr ? "تصفّح تصنيف المهارات والمهن ذات الصلة" : "Browse the skills taxonomy and related occupations"
  );

  const listQ = useQuery({ queryKey: ["skills", "list"], queryFn: skillsApi.list, enabled: !term });
  const searchQ = useQuery({ queryKey: ["skills", "search", term], queryFn: () => skillsApi.search(term), enabled: !!term });
  const relatedQ = useQuery({
    queryKey: ["skills", "related", selected?.id],
    queryFn: () => skillsApi.related(selected!.id),
    enabled: !!selected,
  });

  const skills = term ? (searchQ.data ?? []) : (listQ.data ?? []);
  const loading = term ? searchQ.isLoading : listQ.isLoading;

  return (
    <Layout>
      {/* Header band */}
      <div className="hero-gradient hero-grid relative overflow-hidden text-primary-foreground">
        <div className="glow-blob" style={{ width: 300, height: 300, top: -110, insetInlineEnd: "12%", background: "hsl(var(--secondary) / 0.25)" }} />
        <div className="container relative z-10 py-10 md:py-12">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-primary-foreground/15 bg-primary-foreground/10 px-3 py-1 text-caption font-medium backdrop-blur-sm mb-3">
            <Sparkles className="h-3.5 w-3.5" /> {isAr ? "المهارات" : "Skills"}
          </span>
          <h1 className="text-heading-1">{isAr ? "مستكشف المهارات" : "Skills Explorer"}</h1>
          <p className="text-body-lg opacity-80 mt-1">
            {isAr ? "ابحث في تصنيف المهارات واكتشف المهارات المرتبطة" : "Search the skills taxonomy and discover related skills"}
          </p>
        </div>
      </div>

      <div className="container py-8">
        {/* Search */}
        <form
          onSubmit={(e) => { e.preventDefault(); setTerm(q.trim()); setSelected(null); }}
          className="relative -mt-14 z-20 mb-8 max-w-xl"
        >
          <Search className="absolute start-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={isAr ? "ابحث عن مهارة… (مثال: React)" : "Search a skill… (e.g. React)"}
            className="ps-11 h-12 rounded-xl border-border/60 bg-card shadow-lg focus-visible:ring-0 focus-visible:ring-offset-0"
          />
        </form>

        <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
          {/* Skill list */}
          <div>
            {loading ? (
              <div className="flex items-center justify-center py-20"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
            ) : skills.length === 0 ? (
              <div className="card-premium flex flex-col items-center py-16 text-center">
                <div className="icon-tile h-12 w-12 mb-4"><Layers className="h-6 w-6 text-primary" /></div>
                <h3 className="text-heading-3 mb-1">{isAr ? "لا توجد مهارات" : "No skills found"}</h3>
                <p className="text-body text-muted-foreground">{isAr ? "جرّب بحثاً مختلفاً" : "Try a different search"}</p>
              </div>
            ) : (
              <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 gap-3" staggerDelay={0.04}>
                {skills.map((s) => (
                  <StaggerItem key={s.id}>
                    <AnimatedCard>
                      <button
                        onClick={() => setSelected(s)}
                        className={`card-premium group flex w-full items-start gap-3 p-4 text-start ${selected?.id === s.id ? "border-primary/40" : ""}`}
                      >
                        <span className="icon-tile mt-0.5 h-9 w-9 shrink-0"><Sparkles className="h-4 w-4 text-primary" /></span>
                        <span className="min-w-0">
                          <span className="block text-body font-medium text-foreground group-hover:text-primary transition-colors truncate">
                            {isAr && s.name_ar ? s.name_ar : s.name}
                          </span>
                          {(s.category || s.type) && (
                            <span className="block text-caption text-muted-foreground truncate">{s.category || s.type}</span>
                          )}
                        </span>
                        <ChevronRight className="ms-auto mt-1 h-4 w-4 text-muted-foreground shrink-0 group-hover:text-primary" />
                      </button>
                    </AnimatedCard>
                  </StaggerItem>
                ))}
              </StaggerContainer>
            )}
          </div>

          {/* Detail / related panel */}
          <aside>
            <div className="card-premium p-5 sticky top-20">
              {!selected ? (
                <div className="py-8 text-center">
                  <div className="icon-tile mx-auto h-12 w-12 mb-3"><Layers className="h-6 w-6 text-primary" /></div>
                  <p className="text-body text-muted-foreground">
                    {isAr ? "اختر مهارة لعرض المهارات المرتبطة بها" : "Select a skill to see related skills"}
                  </p>
                </div>
              ) : (
                <>
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <h3 className="text-heading-3 font-semibold">{isAr && selected.name_ar ? selected.name_ar : selected.name}</h3>
                    <button onClick={() => setSelected(null)} aria-label="Close" className="rounded-full p-1 text-muted-foreground hover:bg-accent">
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                  {selected.description && <p className="text-body text-muted-foreground mb-4">{selected.description}</p>}
                  <p className="text-caption font-medium text-foreground mb-2">{isAr ? "مهارات مرتبطة" : "Related skills"}</p>
                  {relatedQ.isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  ) : (relatedQ.data ?? []).length === 0 ? (
                    <p className="text-body text-muted-foreground">{isAr ? "لا توجد مهارات مرتبطة." : "No related skills."}</p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {(relatedQ.data ?? []).slice(0, 24).map((r) => (
                        <button
                          key={r.id}
                          onClick={() => setSelected(r)}
                          className="rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-caption font-medium text-primary hover:bg-primary/10 transition-colors"
                        >
                          {isAr && r.name_ar ? r.name_ar : r.name}
                        </button>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </aside>
        </div>
      </div>
    </Layout>
  );
}
