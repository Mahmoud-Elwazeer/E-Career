/**
 * Employer Team — manage the company's hiring team (multi-seat).
 *
 * Wired to the real EmployerTeamViewSet (/employer/team/): list, invite
 * (existing user OR pending email invite), change role, remove. All management
 * is enforced OWNER/ADMIN server-side; a 403 is surfaced, never bypassed.
 */
import { useState } from "react";
import { Navigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Users, Loader2, AlertCircle, RotateCcw, UserPlus, Trash2, Mail, Clock, ShieldCheck,
} from "lucide-react";
import {
  listTeamMembers, inviteTeamMember, updateTeamMemberRole, removeTeamMember,
  type TeamMember, type TeamRole,
} from "@/services/employer";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useTheme } from "@/hooks/use-theme";

const ASSIGNABLE_ROLES: Array<{ value: Exclude<TeamRole, "owner">; en: string; ar: string }> = [
  { value: "admin", en: "Admin", ar: "مسؤول" },
  { value: "recruiter", en: "Recruiter", ar: "موظّف توظيف" },
  { value: "hiring_manager", en: "Hiring Manager", ar: "مدير توظيف" },
  { value: "viewer", en: "Viewer", ar: "مشاهد" },
];

export default function Team() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const { toast } = useToast();
  const qc = useQueryClient();

  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Exclude<TeamRole, "owner">>("recruiter");

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["employer-team"],
    queryFn: listTeamMembers,
    retry: false,
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ["employer-team"] });

  const permissionToast = (e: { status?: number }) => {
    if (e?.status === 403) {
      toast({
        title: isAr ? "صلاحيات غير كافية" : "Not allowed",
        description: isAr
          ? "فقط مالك الشركة أو المسؤول يمكنه إدارة الفريق."
          : "Only a company owner or admin can manage the team.",
        variant: "destructive",
      });
    } else {
      toast({ title: isAr ? "تعذّر التنفيذ" : "Action failed", variant: "destructive" });
    }
  };

  const inviteMut = useMutation({
    mutationFn: () => inviteTeamMember(email.trim(), role),
    onSuccess: (res) => {
      setEmail("");
      invalidate();
      toast({
        title: res.pending_registration
          ? (isAr ? "تمت دعوة عبر البريد" : "Email invite sent")
          : (isAr ? "تمت الدعوة" : "Member invited"),
        description: res.pending_registration
          ? (isAr ? "سينضم عند التسجيل بهذا البريد." : "They'll join once they register with that email.")
          : undefined,
      });
    },
    onError: permissionToast,
  });

  const roleMut = useMutation({
    mutationFn: ({ id, newRole }: { id: number; newRole: Exclude<TeamRole, "owner"> }) =>
      updateTeamMemberRole(id, newRole),
    onSuccess: () => { invalidate(); toast({ title: isAr ? "تم تحديث الدور" : "Role updated" }); },
    onError: permissionToast,
  });

  const removeMut = useMutation({
    mutationFn: (id: number) => removeTeamMember(id),
    onSuccess: () => { invalidate(); toast({ title: isAr ? "تمت الإزالة" : "Member removed" }); },
    onError: permissionToast,
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
          <h2 className="text-heading-2 mb-1">{isAr ? "تعذّر تحميل الفريق" : "Couldn't load the team"}</h2>
          <Button onClick={() => refetch()} className="gap-2 mt-2">
            <RotateCcw className="h-4 w-4" />
            {isAr ? "إعادة المحاولة" : "Try again"}
          </Button>
        </div>
      </AppShell>
    );
  }

  const members = (data ?? []).filter((m) => m.is_active);

  return (
    <AppShell>
      <div className="page-shell max-w-3xl">
        <PageHeader
          title={isAr ? "فريق العمل" : "Team"}
          subtitle={isAr ? "ادعُ زملاءك وأدِر أدوارهم" : "Invite colleagues and manage their roles"}
        />

        {/* Invite form */}
        <form
          onSubmit={(e) => { e.preventDefault(); if (email.trim()) inviteMut.mutate(); }}
          className="surface-card p-5 mb-6"
        >
          <h2 className="section-heading mb-3">{isAr ? "دعوة عضو" : "Invite a member"}</h2>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={isAr ? "البريد الإلكتروني" : "Email address"}
              className="flex-1 px-3 py-2 border border-input rounded-lg focus:ring-2 focus:ring-ring text-body"
            />
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as Exclude<TeamRole, "owner">)}
              className="px-3 py-2 border border-input rounded-lg focus:ring-2 focus:ring-ring text-body bg-background"
            >
              {ASSIGNABLE_ROLES.map((r) => (
                <option key={r.value} value={r.value}>{isAr ? r.ar : r.en}</option>
              ))}
            </select>
            <Button type="submit" className="gap-2" disabled={inviteMut.isPending}>
              {inviteMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
              {isAr ? "دعوة" : "Invite"}
            </Button>
          </div>
          <p className="text-caption text-muted-foreground mt-2">
            {isAr
              ? "يمكنك دعوة شخص لم يسجّل بعد؛ سينضم تلقائياً عند التسجيل بنفس البريد."
              : "You can invite someone who hasn't registered yet — they'll join automatically when they sign up with that email."}
          </p>
        </form>

        {/* Members list */}
        <div className="surface-card">
          <div className="p-5 border-b flex items-center justify-between">
            <h2 className="section-heading mb-0">{isAr ? "الأعضاء" : "Members"}</h2>
            <Badge variant="secondary">{members.length}</Badge>
          </div>
          <div className="divide-y divide-border">
            {members.map((m: TeamMember) => {
              const isOwner = m.role === "owner";
              return (
                <div key={m.id} className="p-5 flex items-center justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-body font-medium text-foreground truncate">
                        {m.user_name || m.user_email || m.invite_email}
                      </p>
                      {isOwner && (
                        <Badge variant="outline" className="gap-1 bg-primary/10 text-primary border-primary/30">
                          <ShieldCheck className="h-3 w-3" /> {isAr ? "المالك" : "Owner"}
                        </Badge>
                      )}
                      {m.is_pending && (
                        <Badge variant="outline" className="gap-1 bg-warning/15 text-warning-foreground border-warning/30">
                          {m.user_email ? <Clock className="h-3 w-3" /> : <Mail className="h-3 w-3" />}
                          {m.user_email
                            ? (isAr ? "بانتظار القبول" : "Pending")
                            : (isAr ? "دعوة بريد" : "Email invite")}
                        </Badge>
                      )}
                    </div>
                    {m.user_email && m.user_name && (
                      <p className="text-caption text-muted-foreground truncate">{m.user_email}</p>
                    )}
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {isOwner ? (
                      <span className="text-caption text-muted-foreground">{m.role_display}</span>
                    ) : (
                      <select
                        value={m.role}
                        onChange={(e) =>
                          roleMut.mutate({ id: m.id, newRole: e.target.value as Exclude<TeamRole, "owner"> })
                        }
                        disabled={roleMut.isPending}
                        className="px-2 py-1.5 border border-input rounded-lg text-caption bg-background"
                      >
                        {ASSIGNABLE_ROLES.map((r) => (
                          <option key={r.value} value={r.value}>{isAr ? r.ar : r.en}</option>
                        ))}
                      </select>
                    )}
                    {!isOwner && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        disabled={removeMut.isPending}
                        onClick={() => removeMut.mutate(m.id)}
                        aria-label={isAr ? "إزالة" : "Remove"}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}

            {members.length === 0 && (
              <div className="p-12 text-center">
                <Users className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-body text-muted-foreground">
                  {isAr ? "لا يوجد أعضاء بعد. ابدأ بدعوة زميل." : "No members yet. Invite a colleague to get started."}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
