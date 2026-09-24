import { apiRequest } from "@/services/client";

export interface FinancialOverview {
  gross_revenue: number;
  net_revenue: number;
  refunds: number;
  orders_total: number;
  orders_paid: number;
  payments_total: number;
  payments_succeeded: number;
  payments_failed: number;
  payment_success_rate: number;
  avg_transaction_value: number;
  transactions_today: number;
  transactions_month: number;
  revenue_by_platform: { platform_code: string; total: number; count: number }[];
  revenue_by_currency: { currency: string; total: number; count: number }[];
  revenue_by_package: { package__name: string; total: number; count: number }[];
  webhook_health: { processed: number; failed: number };
}

export interface ReconResult {
  matched: number;
  exception_count: number;
  exceptions: { type: string; detail: string; order?: string; payment?: string; ledger?: string }[];
  provider_verified: boolean;
}

export interface AdminTxn {
  reference: string; platform: string; order: string; package: string;
  amount: number; currency: string; status: string; provider: string;
  provider_reference: string; created_at: string;
}

export async function getOverview(params: { platform?: string; currency?: string; days?: number } = {}): Promise<FinancialOverview> {
  const q = new URLSearchParams();
  if (params.platform) q.set("platform", params.platform);
  if (params.currency) q.set("currency", params.currency);
  if (params.days) q.set("days", String(params.days));
  return apiRequest<FinancialOverview>(`/payments/admin/overview/?${q.toString()}`);
}

export async function getReconciliation(): Promise<ReconResult> {
  return apiRequest<ReconResult>(`/payments/admin/reconciliation/`);
}

export async function getAdminTransactions(params: { platform?: string; currency?: string } = {}): Promise<AdminTxn[]> {
  const q = new URLSearchParams();
  if (params.platform) q.set("platform", params.platform);
  if (params.currency) q.set("currency", params.currency);
  const res = await apiRequest<AdminTxn[]>(`/payments/admin/transactions/?${q.toString()}`);
  return Array.isArray(res) ? res : [];
}
