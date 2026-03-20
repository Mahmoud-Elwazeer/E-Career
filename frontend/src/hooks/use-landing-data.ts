import { useQuery } from "@tanstack/react-query";
import { fetchJobs, fetchCompanies, fetchSources } from "@/services/jobs";
import type { Job, Company } from "@/services/jobs";

interface LandingData {
  featuredJobs: Job[];
  totalJobs: number;
  companiesWithCounts: { company: Company; count: number }[];
  industryCounts: Record<string, number>;
  sourcesCount: number;
}

async function loadLandingData(): Promise<LandingData> {
  const [jobsRes, companies, sources] = await Promise.all([
    fetchJobs({ page_size: 8 }),
    fetchCompanies(),
    fetchSources(),
  ]);

  const jobs = jobsRes.results ?? [];
  const totalJobs = jobsRes.count ?? jobs.length;

  const industryCounts: Record<string, number> = {};
  for (const job of jobs) {
    industryCounts[job.industry] = (industryCounts[job.industry] || 0) + 1;
  }

  const companyJobCounts = new Map<string, number>();
  for (const job of jobs) {
    const key = job.company_slug;
    companyJobCounts.set(key, (companyJobCounts.get(key) || 0) + 1);
  }

  const companiesWithCounts = companies
    .map((c) => ({ company: c, count: companyJobCounts.get(c.slug) || 0 }))
    .sort((a, b) => b.count - a.count);

  return { featuredJobs: jobs, totalJobs, companiesWithCounts, industryCounts, sourcesCount: sources.length };
}

export function useLandingData() {
  return useQuery({
    queryKey: ["landing-data"],
    queryFn: loadLandingData,
    staleTime: 5 * 60 * 1000,
  });
}
