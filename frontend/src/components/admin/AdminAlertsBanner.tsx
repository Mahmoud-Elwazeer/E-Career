/**
 * AdminAlertsBanner — surfaces live decision-support alerts from
 * GET /admin-api/alerts/ (DecisionSupportAlertsView). This endpoint was fully
 * built on the backend but had no frontend consumer: it aggregates AI cost
 * spikes, stale scraper sources, cache failures, missing Celery workers, and
 * overdue GDPR deletions. Shown globally at the top of the admin console so an
 * operator sees platform health at a glance on every tab.
 */
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, AlertCircle, Info, X } from "lucide-react";
import { useState } from "react";
import { fetchAdminAlerts, type AdminAlert } from "@/services/admin";
import { cn } from "@/lib/utils";

function severityStyle(sev: string): { row: string; icon: typeof AlertTriangle; iconCls: string } {
  switch (sev) {
    case "critical":
      return { row: "border-destructive/30 bg-destructive/5", icon: AlertCircle, iconCls: "text-destructive" };
    case "warning":
      return { row: "border-warning/30 bg-warning/5", icon: AlertTriangle, iconCls: "text-warning-foreground" };
    default:
      return { row: "border-info/30 bg-info/5", icon: Info, iconCls: "text-info" };
  }
}

export function AdminAlertsBanner() {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const { data: alerts = [] } = useQuery({
    queryKey: ["admin-alerts"],
    queryFn: fetchAdminAlerts,
    // Ops health should stay fresh without hammering the endpoint.
    refetchInterval: 60_000,
    retry: false,
  });

  const visible = (alerts as AdminAlert[]).filter(
    (a, i) => !dismissed.has(a.id ?? String(i)),
  );

  if (visible.length === 0) return null;

  return (
    <div className="mb-6 space-y-2" role="status" aria-live="polite">
      {visible.slice(0, 5).map((a, i) => {
        const key = a.id ?? String(i);
        const s = severityStyle(a.severity);
        const Icon = s.icon;
        return (
          <div key={key} className={cn("flex items-start gap-3 rounded-xl border p-3", s.row)}>
            <Icon className={cn("h-5 w-5 shrink-0 mt-0.5", s.iconCls)} />
            <div className="flex-1 min-w-0">
              {a.title && <p className="text-body font-medium text-foreground">{a.title}</p>}
              <p className="text-caption text-muted-foreground">{a.message || a.detail}</p>
            </div>
            <button
              onClick={() => setDismissed((prev) => new Set(prev).add(key))}
              className="shrink-0 rounded-md p-1 text-muted-foreground hover:bg-foreground/10 hover:text-foreground transition-colors"
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
