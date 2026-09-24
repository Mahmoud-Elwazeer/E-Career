import { apiRequest } from "@/services/client";

/** Money is minor units (piastres/cents). Format for display. */
export function formatMoney(minor: number, currency: string): string {
  const major = (minor || 0) / 100;
  try {
    return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(major);
  } catch {
    return `${major.toFixed(2)} ${currency}`;
  }
}

export interface Package {
  id: string;
  name: string;
  slug: string;
  description: string;
  audience: "individual" | "employer";
  platform_code: string;
  price_amount: number;
  currency: string;
  interval: "one_time" | "month" | "year";
}

export interface OrderStatus {
  reference: string;
  platform_code: string;
  package_name: string;
  subtotal: number;
  discount: number;
  total: number;
  currency: string;
  status: string;
  created_at: string;
}

export interface TransactionRow {
  reference: string;
  platform: string;
  description: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
}

export async function listPackages(audience?: "individual" | "employer"): Promise<Package[]> {
  const q = audience ? `?audience=${audience}` : "";
  const res = await apiRequest<{ results?: Package[] } | Package[]>(`/payments/packages/${q}`);
  if (Array.isArray(res)) return res;
  return (res as { results?: Package[] })?.results ?? [];
}

export async function checkout(packageSlug: string, provider = "stripe"): Promise<{ order: string; checkout_url: string }> {
  return apiRequest(`/payments/checkout/`, {
    method: "POST",
    body: { package: packageSlug, provider },
  });
}

export async function getOrder(reference: string): Promise<OrderStatus> {
  return apiRequest(`/payments/orders/${reference}/`);
}

export async function listTransactions(): Promise<TransactionRow[]> {
  const res = await apiRequest<TransactionRow[]>(`/payments/transactions/`);
  return Array.isArray(res) ? res : [];
}
