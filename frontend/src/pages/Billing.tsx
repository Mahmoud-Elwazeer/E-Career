/**
 * Billing — real checkout wired to /api/v1/payments/.
 * Lists packages for the user's audience, starts a provider checkout (redirects
 * to the hosted checkout URL) or fulfills a free plan immediately, shows the
 * result state from ?status=, and lists the user's transaction history.
 * No mock payments — every action hits the backend service layer.
 */
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { CheckCircle2, XCircle, Clock, Loader2, CreditCard, ArrowRight } from "lucide-react";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";
import {
  listPackages, checkout, listTransactions, formatMoney,
  type Package, type TransactionRow,
} from "@/services/billing";

const STATUS_BANNER: Record<string, { icon: typeof CheckCircle2; cls: string; en: string; ar: string }> = {
  success: { icon: CheckCircle2, cls: "text-success border-success/30 bg-success/10", en: "Payment successful — your plan is active.", ar: "تم الدفع بنجاح — باقتك مفعّلة." },
  cancelled: { icon: XCircle, cls: "text-muted-foreground border-border bg-muted/40", en: "Checkout cancelled. No charge was made.", ar: "تم إلغاء الدفع. لم يتم أي خصم." },
  pending: { icon: Clock, cls: "text-warning-foreground border-warning/30 bg-warning/10", en: "Payment pending confirmation.", ar: "بانتظار تأكيد الدفع." },
};

const STATUS_BADGE: Record<string, string> = {
  paid: "bg-success/15 text-success",
  pending: "bg-warning/15 text-warning-foreground",
  created: "bg-muted text-muted-foreground",
  failed: "bg-destructive/15 text-destructive",
  cancelled: "bg-muted text-muted-foreground",
  refunded: "bg-primary/15 text-primary",
};

export default function Billing() {
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const { user } = useAuth();
  const { toast } = useToast();
  const [params] = useSearchParams();
  const bannerKey = params.get("status") || "";
  const [buying, setBuying] = useState<string | null>(null);

  const audience = user?.role === "employer" ? "employer" : "individual";

  const pkgQuery = useQuery({
    queryKey: ["packages", audience],
    queryFn: () => listPackages(audience),
  });
  const txQuery = useQuery({
    queryKey: ["transactions"],
    queryFn: listTransactions,
  });

  const buy = useMutation({
    mutationFn: (slug: string) => checkout(slug),
    onMutate: (slug) => setBuying(slug),
    onSuccess: (res) => {
      if (res.checkout_url) {
        window.location.href = res.checkout_url; // hosted provider checkout
      } else {
        toast({ title: isAr ? "تم التفعيل" : "Activated", description: isAr ? "باقتك مفعّلة الآن." : "Your plan is now active." });
        txQuery.refetch();
      }
    },
    onError: (e: any) => toast({
      title: isAr ? "تعذّر بدء الدفع" : "Checkout failed",
      description: e?.message ?? (isAr ? "حاول مرة أخرى." : "Please try again."),
      variant: "destructive",
    }),
    onSettled: () => setBuying(null),
  });

  const banner = STATUS_BANNER[bannerKey];
  const packages = pkgQuery.data ?? [];
  const transactions = txQuery.data ?? [];

  return (
    <AppShell>
      <PageHeader
        title={isAr ? "الفوترة والباقات" : "Billing & Plans"}
        description={isAr ? "اختر باقة وادفع بأمان. سجل معاملاتك بالأسفل." : "Choose a plan and pay securely. Your transaction history is below."}
      />

      {banner && (
        <div className={`mb-6 flex items-center gap-2 rounded-xl border px-4 py-3 text-body ${banner.cls}`}>
          <banner.icon className="h-5 w-5 shrink-0" />
          {isAr ? banner.ar : banner.en}
        </div>
      )}

      {/* Packages */}
      {pkgQuery.isLoading ? (
        <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
      ) : packages.length === 0 ? (
        <Card><CardContent className="p-8 text-center text-muted-foreground">
          {isAr ? "لا توجد باقات متاحة حالياً." : "No packages available yet."}
        </CardContent></Card>
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
          {packages.map((p: Package) => (
            <Card key={p.id} className="flex flex-col">
              <CardContent className="flex flex-1 flex-col p-6">
                <div className="mb-1 flex items-center justify-between">
                  <h3 className="text-heading-3 font-semibold">{p.name}</h3>
                  <Badge variant="outline" className="text-[10px] uppercase">{p.interval === "one_time" ? (isAr ? "مرة واحدة" : "one-time") : p.interval}</Badge>
                </div>
                <p className="mb-4 text-body text-muted-foreground">{p.description}</p>
                <div className="mb-6 mt-auto">
                  <span className="font-mono-data text-3xl font-semibold text-foreground">{formatMoney(p.price_amount, p.currency)}</span>
                  {p.interval !== "one_time" && <span className="text-caption text-muted-foreground">/{p.interval === "month" ? (isAr ? "شهر" : "mo") : (isAr ? "سنة" : "yr")}</span>}
                </div>
                <Button
                  className="w-full gap-2 rounded-xl"
                  loading={buying === p.slug}
                  onClick={() => buy.mutate(p.slug)}
                >
                  <CreditCard className="h-4 w-4" />
                  {p.price_amount === 0 ? (isAr ? "تفعيل مجاني" : "Activate free") : (isAr ? "اشترِ الآن" : "Buy now")}
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Transaction history */}
      <div className="mt-10">
        <h2 className="text-heading-2 mb-4">{isAr ? "سجل المعاملات" : "Transaction history"}</h2>
        {txQuery.isLoading ? (
          <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
        ) : transactions.length === 0 ? (
          <Card><CardContent className="p-6 text-center text-muted-foreground">
            {isAr ? "لا توجد معاملات بعد." : "No transactions yet."}
          </CardContent></Card>
        ) : (
          <Card><CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-body">
                <thead className="border-b text-caption text-muted-foreground">
                  <tr>
                    <th className="p-3 text-start">{isAr ? "المرجع" : "Reference"}</th>
                    <th className="p-3 text-start">{isAr ? "الوصف" : "Description"}</th>
                    <th className="p-3 text-start">{isAr ? "المبلغ" : "Amount"}</th>
                    <th className="p-3 text-start">{isAr ? "الحالة" : "Status"}</th>
                    <th className="p-3 text-start">{isAr ? "التاريخ" : "Date"}</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((t: TransactionRow) => (
                    <tr key={t.reference} className="border-b last:border-0">
                      <td className="p-3 font-mono-data text-caption">{t.reference}</td>
                      <td className="p-3">{t.description}</td>
                      <td className="p-3 font-mono-data">{formatMoney(t.amount, t.currency)}</td>
                      <td className="p-3">
                        <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${STATUS_BADGE[t.status] || "bg-muted text-muted-foreground"}`}>
                          {t.status}
                        </span>
                      </td>
                      <td className="p-3 text-caption text-muted-foreground">{new Date(t.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent></Card>
        )}
      </div>
    </AppShell>
  );
}
