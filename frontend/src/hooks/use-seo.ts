import { useEffect } from "react";
import type { Job } from "@/services/jobs";
// NOTE: getCompany is currently a no-op stub (always returns undefined,
// see former lib/api.ts) kept only for API-shape compatibility until this
// hook is wired to a real company cache.
function getCompany(_id: string): undefined { return undefined; }

export function useBreadcrumbStructuredData(items: { name: string; url: string }[]) {
  useEffect(() => {
    if (!items.length) return;
    const jsonLd = {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      itemListElement: items.map((item, i) => ({
        "@type": "ListItem",
        position: i + 1,
        name: item.name,
        item: item.url,
      })),
    };
    const script = document.createElement("script");
    script.type = "application/ld+json";
    script.text = JSON.stringify(jsonLd);
    script.id = "breadcrumb-jsonld";
    document.head.querySelector("#breadcrumb-jsonld")?.remove();
    document.head.appendChild(script);
    return () => { document.head.querySelector("#breadcrumb-jsonld")?.remove(); };
  }, [JSON.stringify(items)]);
}

export function useJobStructuredData(job: Job | null) {
  useEffect(() => {
    if (!job) return;
    const jsonLd = {
      "@context": "https://schema.org",
      "@type": "JobPosting",
      title: job.title,
      description: job.description ?? "",
      hiringOrganization: { "@type": "Organization", name: job.company_name },
      jobLocation: { "@type": "Place", address: job.location },
      employmentType: job.location_type?.toUpperCase(),
      datePosted: job.posted_at,
      validThrough: job.deadline ?? undefined,
      baseSalary: job.salary_min
        ? { "@type": "MonetaryAmount", currency: job.salary_currency ?? "USD", value: { "@type": "QuantitativeValue", minValue: job.salary_min, maxValue: job.salary_max } }
        : undefined,
    };
    const script = document.createElement("script");
    script.type = "application/ld+json";
    script.text = JSON.stringify(jsonLd);
    script.id = "job-jsonld";
    document.head.querySelector("#job-jsonld")?.remove();
    document.head.appendChild(script);
    return () => { document.head.querySelector("#job-jsonld")?.remove(); };
  }, [job?.id]);
}

export function usePageMeta(title: string, description?: string) {
  useEffect(() => {
    const prev = document.title;
    document.title = title ? `${title} | USAM Career Compass` : "USAM Career Compass";
    const metaDesc = document.querySelector('meta[name="description"]');
    const prevDesc = metaDesc?.getAttribute("content") ?? "";
    if (description && metaDesc) metaDesc.setAttribute("content", description);
    return () => {
      document.title = prev;
      if (metaDesc) metaDesc.setAttribute("content", prevDesc);
    };
  }, [title, description]);
}
