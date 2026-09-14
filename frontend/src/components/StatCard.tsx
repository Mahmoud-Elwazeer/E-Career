import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  icon: LucideIcon;
  value: ReactNodeLike;
  label: string;
  /** Tailwind text color token for the icon accent, e.g. "text-primary". */
  accent?: string;
  className?: string;
}

type ReactNodeLike = string | number | React.ReactNode;

/**
 * Token-based dashboard stat tile. Replaces the ad-hoc
 * bg-white/bg-blue-50/text-gray-900 tiles used in legacy dashboards.
 */
export function StatCard({ icon: Icon, value, label, accent = "text-primary", className }: StatCardProps) {
  return (
    <div className={cn("stat-tile", className)}>
      <div className="flex items-center gap-4">
        <div className="rounded-lg bg-primary-muted p-3">
          <Icon className={cn("h-6 w-6", accent)} />
        </div>
        <div className="min-w-0">
          <p className="stat-value">{value}</p>
          <p className="stat-label">{label}</p>
        </div>
      </div>
    </div>
  );
}
