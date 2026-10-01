/**
 * Employer Talent Pools — management UI over the existing talent-pools API.
 * Uses services/employer.ts (listTalentPools, createTalentPool,
 * getTalentPoolDetail, removeCandidateFromPool, deleteTalentPool) — no
 * duplicated engine. Backend enforces IsVerifiedEmployer, tenant isolation,
 * candidate-consent (is_discoverable), and a talent_pool entitlement gate; a
 * 403 from that gate renders a locked state rather than crashing.
 */
import { useState } from "react";
import { Navigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Users, Loader2, AlertCircle, RotateCcw, Plus, Trash2, ChevronDown, ChevronRight,
  Lock, FolderOpen, X,
} from "lucide-react";
import {
  listTalentPools, createTalentPool, getTalentPoolDetail, removeCandidateFromPool,
  deleteTalentPool, getEmployerProfile, type TalentPool,
} from "@/services/employer";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useTheme } from "@/hooks/use-theme";

function PoolCandidates({ poolId, isAr }: { poolId: number; isAr: boolean }) {
  const qc = useQueryClient();
  const { toast } = useToast();
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["talent-pool", poolId],
    queryFn: () => getTalentPoolDetail(poolId),
  });
  const removeMut = useMutation({
    mutationFn: (userId: number) => removeCandidateFromPool(poolId, userId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["talent-pool", poolId] });
      qc.invalidateQueries({ queryKey: ["talent-pools"] });
      toast({ title: isAr ? "تمت الإزالة" : "Candidate removed" });
    },
    onError: () => toast({ title: isAr ? "تعذّر التنفيذ" : "Action failed", variant: "destructive" }),
  });

  if (isLoading) return <div className="p-5 text-center"><Loader2 className="h-5 w-5 animate-spin text-primary mx-auto" /></div>;
  if (isError) return (
    <div className="p-5 text-center text-caption text-muted-foreground">
      {isAr ? "تعذّر تحميل المرشحين." : "Couldn't load candidates."}{" "}
      <button className="text-primary link-underline" onClick={() => refetch()}>{isAr ? "إعادة" : "Retry"}</button>
    </div>
  );
  if (!data?.candidates?.length) return (
    <div className="p-5 text-center text-caption text-muted-foreground">
      {isAr ? "لا يوجد مرشحون في هذه المجموعة بعد." : "No candidates in this pool yet."}
    </div>
  );

  return (
    <div className="divide-y divide-border/70">
      {data.candidates.map((c) => (
        <div key={c.id} className="px-5 py-3 flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-body font-medium text-foreground truncate">{c.user_name || c.user_email}</p>
            <p className="text-caption text-muted-foreground truncate">
              {[c.source, ...(c.tags || [])].filter(Boolean).join(" · ")}
            </p>
          </div>
          <Button variant="ghost" size="sm" className="gap-1.5 text-destructive hover:text-destructive shrink-0"
            disabled={removeMut.isPending} onClick={() => removeMut.mutate(c.user_id)}>
            <X className="h-3.5 w-3.5" /> {isAr ? "إزالة" : "Remove"}
          </Button>
        </div>
      ))}
    </div>
  );
}

export default function TalentPools() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const { toast } = useToast();
  const qc = useQueryClient();
  const [expanded, setExpanded] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");

  const { data: profile, isLoading: profileLoading, isError: profileIsError, error: profileError } =
    useQuery({ queryKey: ["employer-profile"], queryFn: getEmployerProfile, retry: false });

  const { data: pools, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["talent-pools"],
    queryFn: listTalentPools,
    enabled: !!profile?.is_verified,
    retry: false,
  });

  const createMut = useMutation({
    mutationFn: () => createTalentPool({ name: newName.trim(), description: newDesc.trim() || undefined }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["talent-pools"] });
      setCreating(false); setNewName(""); setNewDesc("");
      toast({ title: isAr ? "تم إنشاء المجموعة" : "Talent pool created" });
    },
    onError: () => toast({ title: isAr ? "تعذّر الإنشاء" : "Couldn't create pool", variant: "destructive" }),
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteTalentPool(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["talent-pools"] });
      toast({ title: isAr ? "تم حذف المجموعة" : "Talent pool deleted" });
    },
    onError: () => toast({ title: isAr ? "تعذّر الحذف" : "Couldn't delete pool", variant: "destructive" }),
  });

  if (profileLoading) {
    return <AppShell><div className="page-shell flex items-center justify-center py-24"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div></AppShell>;
  }
  if (profileIsError && (profileError as { status?: number } | null)?.status === 404) {
    return <Navigate to="/app/employer/register" replace />;
  }
  if (!profile?.is_verified) {
    return (
      <AppShell><div className="page-shell flex items-center justify-center py-20">
        <div className="surface-card max-w-md text-center p-8">
          <div className="w-14 h-14 bg-warning/15 rounded-full flex items-center justify-center mx-auto mb-4"><AlertCircle className="w-7 h-7 text-warning-foreground" /></div>
          <h2 className="text-heading-2 mb-2">{isAr ? "قيد المراجعة" : "Verification pending"}</h2>
          <p className="text-body text-muted-foreground">{isAr ? "تتاح مجموعات المواهب بعد توثيق الحساب." : "Talent pools are available once your account is verified."}</p>
        </div>
      </div></AppShell>
    );
  }

  // Entitlement gate: backend returns 403 when the plan lacks talent_pool.
  const errStatus = (error as { status?: number } | null)?.status;
  if (isError && errStatus === 403) {
    return (
      <AppShell><div className="page-shell flex items-center justify-center py-20">
        <div className="surface-card max-w-md text-center p-8">
          <div className="w-14 h-14 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4"><Lock className="w-7 h-7 text-primary" /></div>
          <h2 className="text-heading-2 mb-2">{isAr ? "ميزة مدفوعة" : "Upgrade required"}</h2>
          <p className="text-body text-muted-foreground mb-5">{isAr ? "مجموعات المواهب متاحة في باقات أعلى." : "Talent Pools are available on a higher plan."}</p>
          <Button asChild><a href="/app/billing">{isAr ? "عرض الباقات" : "View plans"}</a></Button>
        </div>
      </div></AppShell>
    );
  }

  return (
    <AppShell>
      <div className="page-shell">
        <PageHeader
          title={isAr ? "مجموعات المواهب" : "Talent Pools"}
          subtitle={profile?.company?.name}
          actions={
            <Button className="gap-2" onClick={() => setCreating((v) => !v)}>
              <Plus className="h-4 w-4" /> {isAr ? "مجموعة جديدة" : "New Pool"}
            </Button>
          }
        />

        {creating && (
          <div className="surface-card p-5 mb-6">
            <form onSubmit={(e) => { e.preventDefault(); if (newName.trim()) createMut.mutate(); }} className="space-y-3">
              <input value={newName} onChange={(e) => setNewName(e.target.value)} required
                placeholder={isAr ? "اسم المجموعة *" : "Pool name *"}
                className="w-full h-11 rounded-lg border border-input bg-card px-4 text-body focus:outline-none focus:ring-2 focus:ring-ring" />
              <textarea value={newDesc} onChange={(e) => setNewDesc(e.target.value)} rows={2}
                placeholder={isAr ? "وصف (اختياري)" : "Description (optional)"}
                className="w-full rounded-lg border border-input bg-card px-4 py-3 text-body focus:outline-none focus:ring-2 focus:ring-ring" />
              <div className="flex gap-2">
                <Button type="submit" disabled={createMut.isPending || !newName.trim()} className="gap-2">
                  {createMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                  {isAr ? "إنشاء" : "Create"}
                </Button>
                <Button type="button" variant="outline" onClick={() => setCreating(false)}>{isAr ? "إلغاء" : "Cancel"}</Button>
              </div>
            </form>
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-20"><Loader2 className="h-7 w-7 animate-spin text-primary" /></div>
        ) : isError ? (
          <div className="surface-card flex flex-col items-center justify-center py-16 text-center">
            <AlertCircle className="h-6 w-6 text-destructive mb-3" />
            <p className="text-body text-muted-foreground mb-4">{isAr ? "تعذّر تحميل المجموعات." : "Couldn't load talent pools."}</p>
            <Button onClick={() => refetch()} variant="outline" className="gap-2"><RotateCcw className="h-4 w-4" /> {isAr ? "إعادة المحاولة" : "Try again"}</Button>
          </div>
        ) : (pools?.length ?? 0) === 0 ? (
          <div className="surface-card flex flex-col items-center justify-center py-16 text-center">
            <FolderOpen className="h-10 w-10 text-muted-foreground mb-4" />
            <p className="text-body text-muted-foreground mb-4">{isAr ? "لا توجد مجموعات بعد. أنشئ أول مجموعة مواهب." : "No pools yet. Create your first talent pool."}</p>
            <Button className="gap-2" onClick={() => setCreating(true)}><Plus className="h-4 w-4" /> {isAr ? "مجموعة جديدة" : "New Pool"}</Button>
          </div>
        ) : (
          <div className="space-y-3">
            {pools!.map((p: TalentPool) => (
              <div key={p.id} className="surface-card overflow-hidden">
                <div className="p-5 flex items-center justify-between gap-3">
                  <button className="flex items-center gap-3 min-w-0 text-left flex-1"
                    onClick={() => setExpanded(expanded === p.id ? null : p.id)}>
                    {expanded === p.id ? <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" /> : <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />}
                    <span className="min-w-0">
                      <span className="flex items-center gap-2">
                        <span className="text-body-lg font-medium text-foreground truncate">{p.name}</span>
                        <Badge variant="outline" className="bg-primary/10 text-primary border-primary/30">
                          <Users className="h-3 w-3 me-1" />{p.candidate_count}
                        </Badge>
                      </span>
                      {p.description && <span className="block text-caption text-muted-foreground truncate">{p.description}</span>}
                    </span>
                  </button>
                  <Button variant="ghost" size="sm" className="gap-1.5 text-destructive hover:text-destructive shrink-0"
                    disabled={deleteMut.isPending}
                    onClick={() => { if (confirm(isAr ? "حذف هذه المجموعة؟" : "Delete this pool?")) deleteMut.mutate(p.id); }}>
                    <Trash2 className="h-3.5 w-3.5" /> {isAr ? "حذف" : "Delete"}
                  </Button>
                </div>
                {expanded === p.id && (
                  <div className="border-t border-border bg-surface-2/30">
                    <PoolCandidates poolId={p.id} isAr={isAr} />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
