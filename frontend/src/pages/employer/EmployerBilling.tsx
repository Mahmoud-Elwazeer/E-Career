/**
 * Employer Billing & Plans — the company's plan, real seat/job usage, and the
 * employer-audience packages available to purchase.
 *
 * All numbers are live: seat usage is a count of active team members, job
 * usage a count of active postings (from /employer/profile/billing/). Packages
 * and checkout reuse the existing /payments flow (no second billing system).
 */
import { useQuery, useMutation } from "@tanstack/react-query";
import { Navigate } from "react-router-dom";
import {
  Loader2, AlertCircle, RotateCcw, Users, Briefcase, Sparkles, CheckCircle2, CreditCard,
} from "lucide-react";
import { getEmployerBilling } from "@/services/employer";
import { listPackages, checkout, formatMoney, type Package } from "@/services/billing";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useTheme } from "@/hooks/use-theme";

function UsageBar({ used, limit, label, isAr }: { used: number; limit: number; label: string; isAr: boolean }) {
  const unlimited = !limit;
  const pct = unlimited ? 0 : Math.min(100, Math.round((used / limit) * 100));
  const near = !unlimited && pct >= 80;
  return (
    <div className="surface-card p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-caption text-muted-foreground">{label}</span>
        <span className="text-body font-medium text-foreground">
          {used}
          {unlimited ? ` ${isAr ? "(غير محدود)" : "(unlimited)"}` : ` / ${limit}`}
        </span>
      </div>
      {!unlimited && (
        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
          <div
            className={`h-full rounded-full ${near ? "bg-warning" : "bg-primary"}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
    </div>
  );
}

export default function EmployerBilling() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const { toast } = useToast();

  const billingQ = useQuery({
    queryKey: ["employer-billing"],
    queryFn: getEmployerBilling,
    retry: false,
  });

  const packagesQ = useQuery({
    queryKey: ["employer-packages"],
    queryFn: () => listPackages("employer"),
  });

  const checkoutMut = useMutation({
    mutationFn: (slug: string) => checkout(slug, "stripe"),
    onSuccess: (res) => {
      if (res.checkout_url) {
        window.location.href = res.checkout_url;
      } else {
        toast({ title: isAr ? "تم إنشاء الطلب" : "Order created" });
      }
    },
    onError: () => toast({ title: isAr ? "تعذّر بدء الدفع" : "Could not start checkout", variant: "destructive" }),
  });

  if (billingQ.isError && (billingQ.error as { status?: number } | null)?.status === 404) {
    return <Navigate to="/app/employer/register" replace />;
  }

  if (billingQ.isLoading) {
    return (
      <AppShell>
        <div className="page-shell flex items-center justify-center py-24" role="status" aria-live="polite">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="sr-only">{isAr ? "جاري التحميل" : "Loading"}</span>
        </div>
      </AppShell>
    );
  }

  if (billingQ.isError) {
    return (
      <AppShell>
        <div className="page-shell flex flex-col items-center justify-center py-24 text-center">
          <div className="rounded-full bg-destructive/10 p-3 mb-4">
            <AlertCircle className="h-6 w-6 text-destructive" />
          </div>
          <h2 className="text-heading-2 mb-1">{isAr ? "تعذّر تحميل الفوترة" : "Couldn't load billing"}</h2>
          <Button onClick={() => billingQ.refetch()} className="gap-2 mt-2">
            <RotateCcw className="h-4 w-4" />
            {isAr ? "إعادة المحاولة" : "Try again"}
          </Button>
        </div>
      </AppShell>
    );
  }

  const b = billingQ.data!;
  const packages = packagesQ.data ?? [];

  return (
    <AppShell>
      <div className="page-shell max-w-4xl">
        <PageHeader
          title={isAr ? "الفوترة والباقات" : "Billing & Plans"}
          subtitle={b.company.name}
        />

        {/* Current plan */}
        <div className="surface-card p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-heading mb-0">{isAr ? "باقتك الحالية" : "Current plan"}</h2>
            {b.plan ? (
              <Badge variant="outline" className="gap-1 bg-primary/10 text-primary border-primary/30">
                <CheckCircle2 className="h-3.5 w-3.5" /> {b.plan.name} · {b.plan.status}
              </Badge>
            ) : (
              <Badge variant="secondary">{isAr ? "لا توجد باقة" : "No active plan"}</Badge>
            )}
          </div>

          {!b.plan && (
            <p className="text-body text-muted-foreground mb-2">
              {isAr
                ? "لا توجد باقة فعّالة — كل الحدود مفتوحة حتى يتم تعيين باقة من قبل الإدارة أو الشراء أدناه."
                : "No active plan — limits are open until a plan is assigned by an admin or purchased below."}
            </p>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <UsageBar used={b.usage.seats_used} limit={b.usage.seats_limit}
              label={isAr ? "مقاعد الفريق" : "Team seats"} isAr={isAr} />
            <UsageBar used={b.usage.active_jobs} limit={b.usage.jobs_limit}
              label={isAr ? "الوظائف النشطة" : "Active jobs"} isAr={isAr} />
          </div>

          {b.plan && (
            <div className="flex flex-wrap gap-3 mt-4 text-caption text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <Users className="h-3.5 w-3.5" />
                {isAr ? "حد المقاعد:" : "Seat limit:"} {b.plan.seat_limit || (isAr ? "غير محدود" : "unlimited")}
              </span>
              <span className="inline-flex items-center gap-1">
                <Briefcase className="h-3.5 w-3.5" />
                {isAr ? "حد الوظائف:" : "Job limit:"} {b.plan.job_posting_limit || (isAr ? "غير محدود" : "unlimited")}
              </span>
              {b.plan.ai_features_enabled && (
                <span className="inline-flex items-center gap-1 text-primary">
                  <Sparkles className="h-3.5 w-3.5" /> {isAr ? "ميزات الذكاء مفعّلة" : "AI features enabled"}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Available employer packages */}
        <div className="surface-card">
          <div className="p-6 border-b">
            <h2 className="section-heading mb-0">{isAr ? "الباقات المتاحة" : "Available plans"}</h2>
          </div>
          <div className="p-6">
            {packagesQ.isLoading ? (
              <div className="flex justify-center py-6"><Loader2 className="h-5 w-5 animate-spin text-primary" /></div>
            ) : packages.length === 0 ? (
              <p className="text-body text-muted-foreground text-center py-6">
                {isAr ? "لا توجد باقات متاحة حالياً." : "No plans are available right now."}
              </p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {packages.map((p: Package) => (
                  <div key={p.id} className="rounded-xl border border-border p-5 flex flex-col">
                    <h3 className="text-body-lg font-medium text-foreground">{p.name}</h3>
                    <p className="text-caption text-muted-foreground mt-1 flex-1">{p.description}</p>
                    <div className="mt-4">
                      <span className="text-heading-3">{formatMoney(p.price_amount, p.currency)}</span>
                      {p.interval !== "one_time" && (
                        <span className="text-caption text-muted-foreground">
                          {" / "}{p.interval === "month" ? (isAr ? "شهر" : "mo") : (isAr ? "سنة" : "yr")}
                        </span>
                      )}
                    </div>
                    <Button
                      className="mt-4 gap-2"
                      disabled={checkoutMut.isPending}
                      onClick={() => checkoutMut.mutate(p.slug)}
                    >
                      {checkoutMut.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CreditCard className="h-4 w-4" />}
                      {isAr ? "اشترك" : "Choose plan"}
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
