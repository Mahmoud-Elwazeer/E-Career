import { useState, useCallback, useEffect } from "react";
import {
  fetchAdminStats,
  fetchAdminCharts,
  fetchActivityLogs as apiFetchActivityLogs,
  type AdminStats,
  type AdminCharts,
} from "@/services/admin";

export { fetchActivityLogs } from "@/services/admin";

export function useAdminStats() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [charts, setCharts] = useState<AdminCharts | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const [s, c] = await Promise.all([fetchAdminStats(), fetchAdminCharts()]);
      setStats(s);
      setCharts(c);
    } catch {}
    finally { setIsLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  return {
    stats: stats ?? {
      total_jobs: 0, pending_review: 0, active_sources: 0,
      total_saves: 0, total_clicks: 0, total_views: 0,
      total_users: 0, jobs_this_week: 0,
    },
    charts: charts ?? { jobs_by_industry: [], jobs_by_source: [] },
    isLoading,
    reload: load,
  };
}
