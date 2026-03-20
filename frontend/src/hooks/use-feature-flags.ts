import { useState, useCallback, useEffect } from "react";
import { fetchFeatureFlags, updateFeatureFlag } from "@/services/admin";

export interface FeatureFlag {
  id: number;
  uuid: string;
  key: string;
  label: string;
  description: string | null;
  is_enabled: boolean;
  metadata: Record<string, unknown>;
  updated_at: string;
}

export function useFeatureFlags() {
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    setIsLoading(true);
    try { setFlags(await fetchFeatureFlags()); }
    catch { setFlags([]); }
    finally { setIsLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggleFlag = useCallback(async (uuid: string, enabled: boolean) => {
    try {
      await updateFeatureFlag(uuid, { is_enabled: enabled });
      setFlags((prev) => prev.map((f) => (f.uuid === uuid ? { ...f, is_enabled: enabled } : f)));
      return { error: null };
    } catch (e) { return { error: e }; }
  }, []);

  const isEnabled = useCallback(
    (key: string) => flags.find((f) => f.key === key)?.is_enabled ?? false,
    [flags]
  );

  return { flags, isLoading, toggleFlag, isEnabled, reload: load };
}
