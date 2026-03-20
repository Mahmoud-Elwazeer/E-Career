import { useState, useCallback, useEffect } from "react";
import { useAuth } from "@/hooks/use-auth";
import {
  fetchSavedJobs,
  saveJob,
  unsaveJob,
  type SavedJob,
} from "@/services/userdata";
import { fetchJobs } from "@/services/jobs";

export function useSavedJobs() {
  const { user } = useAuth();
  const [savedJobs, setSavedJobs] = useState<SavedJob[]>([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!user) { setSavedJobs([]); return; }
    setLoading(true);
    try {
      const data = await fetchSavedJobs();
      setSavedJobs(data);
    } catch { setSavedJobs([]); }
    finally { setLoading(false); }
  }, [user]);

  useEffect(() => { load(); }, [load]);

  const isSaved = useCallback(
    (jobId: number | string) => savedJobs.some((s) => s.job.id === Number(jobId) || s.job.slug === String(jobId)),
    [savedJobs]
  );

  const getSavedId = useCallback(
    (jobId: number | string) => savedJobs.find((s) => s.job.id === Number(jobId) || s.job.slug === String(jobId))?.id,
    [savedJobs]
  );

  const save = useCallback(async (jobId: number) => {
    if (!user) return;
    try {
      const saved = await saveJob(jobId);
      setSavedJobs((prev) => [saved, ...prev]);
    } catch {}
  }, [user]);

  const remove = useCallback(async (jobId: number | string) => {
    if (!user) return;
    const savedId = getSavedId(jobId);
    if (!savedId) return;
    try {
      await unsaveJob(savedId);
      setSavedJobs((prev) => prev.filter((s) => s.id !== savedId));
    } catch {}
  }, [user, getSavedId]);

  return { savedJobs, save, remove, isSaved, loading, reload: load };
}
