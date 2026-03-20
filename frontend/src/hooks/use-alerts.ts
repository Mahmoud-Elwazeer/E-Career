import { useState, useCallback, useEffect } from "react";
import { useAuth } from "@/hooks/use-auth";
import {
  fetchAlerts,
  createAlert,
  updateAlert,
  deleteAlert,
  type Alert,
} from "@/services/userdata";

export type { Alert as DbAlert };

export function useAlerts() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    if (!user) { setAlerts([]); return; }
    setIsLoading(true);
    try { setAlerts(await fetchAlerts()); }
    catch { setAlerts([]); }
    finally { setIsLoading(false); }
  }, [user]);

  useEffect(() => { load(); }, [load]);

  const addAlert = useCallback(async (
    keyword: string,
    work_mode?: string,
    industry?: string,
    frequency: "daily" | "weekly" | "instant" = "daily"
  ) => {
    if (!user) return;
    try {
      const a = await createAlert({ keyword, work_mode, industry, frequency });
      setAlerts((prev) => [a, ...prev]);
      return { error: null };
    } catch (e) {
      return { error: e };
    }
  }, [user]);

  const updateAlertHook = useCallback(async (
    uuid: string,
    updates: { frequency?: "daily" | "weekly" | "instant"; is_active?: boolean }
  ) => {
    try {
      const updated = await updateAlert(uuid, updates);
      setAlerts((prev) => prev.map((a) => (a.uuid === uuid ? updated : a)));
      return { error: null };
    } catch (e) { return { error: e }; }
  }, []);

  const removeAlert = useCallback(async (uuid: string) => {
    try {
      await deleteAlert(uuid);
      setAlerts((prev) => prev.filter((a) => a.uuid !== uuid));
      return { error: null };
    } catch (e) { return { error: e }; }
  }, []);

  return { alerts, isLoading, addAlert, updateAlert: updateAlertHook, removeAlert, reload: load };
}
