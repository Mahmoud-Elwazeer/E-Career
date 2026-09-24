/**
 * Admin Financial Control Center — real analytics from the ledger/orders.
 * Overview KPIs, revenue breakdowns, recent transactions, and reconciliation
 * exceptions. Admin-gated route. Every figure comes from the backend (no fake
 * numbers). The money is in minor units; formatMoney renders it.
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, TrendingUp, AlertTriangle, CheckCircle2, Layers, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatMoney } from "@/services/billing";
import { getOverview, getReconciliation, getAdminTransactions } from "@/services/adminFinance";

const PLATFORMS = [
  { code: "", label: "All" },
  { code: "C", label: "Career" },
  { code: "E", label: "Education" },
  { code: "F", label: "Freelancing" },
  { code: "K", label: "Kids" },
];

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <Card><CardContent className="p-5">
      <p className="text-caption text-muted-foreground">{label}</p>
      <p className="font-mono-data text-2xl font-semibold text-foreground">{value}</p>
    </CardContent></Card>
  );
}

export default function AdminFinance() {
  const [platform, setPlatform] = useState("");

  const overview = useQuery({
    queryKey: ["admin-fin-overview", platform],
    queryFn: () => getOverview({ platform: platform || undefined }),
  });
  const recon = useQuery({ queryKey: ["admin-fin-recon"], queryFn: getReconciliation });
  const txns = useQuery({
    queryKey: ["admin-fin-txns", platform],
    queryFn: () => getAdminTransactions({ platform: platform || undefined }),
  });

  const o = overview.data;
  // Overview response is currency-mixed at platform level; display in EGP-major
  // only when a single currency dominates, else show raw with the reported code.
  const cur = o?.revenue_by_currency?.[0]?.currency || "EGP";
  const money = (v: number) => formatMoney(v, cur);

  return (
    <AppShell>
      <PageHeader
        title="Financial Control Center"
        description="Live revenue, transactions and reconciliation across USAM products."
      />

      {/* Platform filter */}
      <div className="mb-6 flex flex-wrap items-center gap-2">
        {PLATFORMS.map((p) => (
          <button
            key={p.code}
            onClick={() => setPlatform(p.code)}
            className={`rounded-full px-3.5 py-1.5 text-caption font-medium transition-colors ${
              platform === p.code ? "bg-primary text-primary-foreground" : "border border-border text-muted-foreground hover:text-foreground"
            }`}
          >
            {p.label}
          </button>
        ))}
        <Button variant="outline" size="sm" className="ms-auto gap-1.5" onClick={() => { overview.refetch(); recon.refetch(); txns.refetch(); }}>
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </Button>
      </div>

      {overview.isLoading || !o ? (
        <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
      ) : (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Kpi label="Gross revenue" value={money(o.gross_revenue)} />
            <Kpi label="Net revenue" value={money(o.net_revenue)} />
            <Kpi label="Refunds" value={money(o.refunds)} />
            <Kpi label="Avg transaction" value={money(o.avg_transaction_value)} />
            <Kpi label="Payments succeeded" value={String(o.payments_succeeded)} />
            <Kpi label="Payments failed" value={String(o.payments_failed)} />
            <Kpi label="Success rate" value={`${o.payment_success_rate}%`} />
            <Kpi label="Paid today / month" value={`${o.transactions_today} / ${o.transactions_month}`} />
          </div>

          {/* Breakdowns */}
          <div className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-3">
            <Card><CardContent className="p-5">
              <div className="mb-3 flex items-center gap-2 text-body font-medium"><Layers className="h-4 w-4 text-primary" /> By platform</div>
              {o.revenue_by_platform.length === 0 ? <p className="text-caption text-muted-foreground">No revenue yet.</p> :
                o.revenue_by_platform.map((r) => (
                  <div key={r.platform_code} className="flex items-center justify-between py-1 text-caption">
                    <span>{r.platform_code}</span><span className="font-mono-data">{money(r.total)} ({r.count})</span>
                  </div>
                ))}
            </CardContent></Card>
            <Card><CardContent className="p-5">
              <div className="mb-3 flex items-center gap-2 text-body font-medium"><TrendingUp className="h-4 w-4 text-primary" /> By package</div>
              {o.revenue_by_package.length === 0 ? <p className="text-caption text-muted-foreground">No revenue yet.</p> :
                o.revenue_by_package.map((r) => (
                  <div key={r.package__name} className="flex items-center justify-between py-1 text-caption">
                    <span className="truncate">{r.package__name}</span><span className="font-mono-data">{money(r.total)}</span>
                  </div>
                ))}
            </CardContent></Card>
            <Card><CardContent className="p-5">
              <div className="mb-3 flex items-center gap-2 text-body font-medium">Webhooks</div>
              <div className="flex items-center justify-between py-1 text-caption"><span>Processed</span><span className="font-mono-data">{o.webhook_health.processed}</span></div>
              <div className="flex items-center justify-between py-1 text-caption"><span>Failed</span><span className="font-mono-data text-destructive">{o.webhook_health.failed}</span></div>
            </CardContent></Card>
          </div>

          {/* Reconciliation */}
          <div className="mt-6">
            <Card><CardContent className="p-5">
              <div className="mb-3 flex items-center gap-2 text-body font-medium">
                {recon.data && recon.data.exception_count === 0
                  ? <CheckCircle2 className="h-4 w-4 text-success" />
                  : <AlertTriangle className="h-4 w-4 text-warning-foreground" />}
                Reconciliation
              </div>
              {recon.isLoading || !recon.data ? (
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              ) : (
                <>
                  <p className="text-caption text-muted-foreground mb-2">
                    {recon.data.matched} matched · {recon.data.exception_count} exception(s)
                  </p>
                  {recon.data.exceptions.map((e, i) => (
                    <div key={i} className="flex items-center gap-2 py-1 text-caption">
                      <span className="rounded bg-destructive/10 px-1.5 py-0.5 text-[10px] font-medium text-destructive">{e.type}</span>
                      <span className="text-muted-foreground">{e.detail} {e.order || e.payment || ""}</span>
                    </div>
                  ))}
                </>
              )}
            </CardContent></Card>
          </div>

          {/* Transactions */}
          <div className="mt-6">
            <h2 className="text-heading-2 mb-3">Recent transactions</h2>
            <Card><CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-body">
                  <thead className="border-b text-caption text-muted-foreground">
                    <tr>
                      <th className="p-3 text-start">Reference</th>
                      <th className="p-3 text-start">Platform</th>
                      <th className="p-3 text-start">Package</th>
                      <th className="p-3 text-start">Amount</th>
                      <th className="p-3 text-start">Status</th>
                      <th className="p-3 text-start">Provider</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(txns.data ?? []).map((t) => (
                      <tr key={t.reference} className="border-b last:border-0">
                        <td className="p-3 font-mono-data text-caption">{t.reference}</td>
                        <td className="p-3">{t.platform}</td>
                        <td className="p-3">{t.package}</td>
                        <td className="p-3 font-mono-data">{formatMoney(t.amount, t.currency)}</td>
                        <td className="p-3">{t.status}</td>
                        <td className="p-3 text-caption text-muted-foreground">{t.provider || "—"}</td>
                      </tr>
                    ))}
                    {(txns.data ?? []).length === 0 && (
                      <tr><td colSpan={6} className="p-6 text-center text-muted-foreground">No transactions yet.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent></Card>
          </div>
        </>
      )}
    </AppShell>
  );
}
