import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Loader2, AlertTriangle, Languages } from "lucide-react";
import { Layout } from "@/components/Layout";
import { PolicyMarkdown } from "@/components/legal/PolicyMarkdown";
import { Badge } from "@/components/ui/badge";
import { useTheme } from "@/hooks/use-theme";
import { usePageMeta } from "@/hooks/use-seo";
import { getPolicy, type PolicyVersion } from "@/services/legal";
import { ApiError } from "@/services/client";

const TITLES: Record<string, { en: string; ar: string }> = {
  terms: { en: "Terms of Service", ar: "شروط الخدمة" },
  privacy: { en: "Privacy Policy", ar: "سياسة الخصوصية" },
  cookies: { en: "Cookie Policy", ar: "سياسة ملفات تعريف الارتباط" },
  refunds: { en: "Refund & Cancellation Policy", ar: "سياسة الاسترداد والإلغاء" },
  "payment-security": { en: "Payment & Card Security Policy", ar: "سياسة أمان الدفع والبطاقات" },
  security: { en: "Security Overview", ar: "نظرة عامة على الأمان" },
  "ai-disclosure": { en: "AI Use & Rasheed Disclosure", ar: "استخدام الذكاء الاصطناعي وإفصاح رشيد" },
};

/**
 * Generic public policy page, routed at /legal/:slug. Fetches the ACTIVE
 * PolicyVersion for the current locale and renders it. If no active version
 * exists yet for this locale, that's shown honestly rather than silently
 * falling back to invented text.
 */
export default function PolicyPage() {
  const { slug = "" } = useParams<{ slug: string }>();
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const titleInfo = TITLES[slug];

  const [version, setVersion] = useState<PolicyVersion | null>(null);
  const [loading, setLoading] = useState(true);
  // Fail-closed (directive item 24): ANY failure to load a policy — no
  // active version yet (404) OR a network/server error — must render an
  // honest "unavailable" state, never a blank page. `unavailable` covers
  // both cases; `reason` only changes the copy, not whether something
  // visible is shown.
  const [unavailable, setUnavailable] = useState<"not_found" | "error" | null>(null);

  usePageMeta(
    titleInfo ? (isAr ? titleInfo.ar : titleInfo.en) : "Legal",
    isAr ? "وثيقة قانونية من USAM." : "A legal document from USAM.",
  );

  useEffect(() => {
    let active = true;
    setLoading(true);
    setUnavailable(null);
    setVersion(null);
    getPolicy(slug, isAr ? "ar" : "en")
      .then((v) => { if (active) setVersion(v); })
      .catch((e) => {
        if (!active) return;
        setVersion(null);
        setUnavailable(e instanceof ApiError && e.status === 404 ? "not_found" : "error");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [slug, isAr]);

  return (
    <Layout>
      <section className="section-y">
        <div className="container max-w-3xl">
          <nav className="mb-6 flex items-center gap-1.5 text-caption text-muted-foreground">
            <Link to="/legal" className="hover:text-foreground link-underline">
              {isAr ? "المركز القانوني" : "Legal Center"}
            </Link>
            <Arrow className="h-3 w-3 rtl:rotate-180" />
            <span className="text-foreground">{titleInfo ? (isAr ? titleInfo.ar : titleInfo.en) : slug}</span>
          </nav>

          {loading && (
            <div className="flex items-center justify-center py-24" role="status" aria-live="polite">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          )}

          {!loading && unavailable === "not_found" && (
            <div className="card-premium flex items-start gap-3 p-6">
              <AlertTriangle className="h-5 w-5 shrink-0 text-warning" />
              <div>
                <h2 className="text-heading-3 font-semibold mb-1">
                  {isAr ? "لا توجد نسخة فعّالة بعد" : "No active version yet"}
                </h2>
                <p className="text-body text-muted-foreground">
                  {isAr
                    ? "هذه الوثيقة قيد الإعداد ولم تُنشر نسخة فعّالة منها بعد."
                    : "This document is being prepared and no active version has been published yet."}
                </p>
              </div>
            </div>
          )}

          {!loading && unavailable === "error" && (
            <div className="card-premium flex items-start gap-3 p-6" role="alert">
              <AlertTriangle className="h-5 w-5 shrink-0 text-destructive" />
              <div>
                <h2 className="text-heading-3 font-semibold mb-1">
                  {isAr ? "تعذّر تحميل هذه الوثيقة" : "This document couldn't be loaded"}
                </h2>
                <p className="text-body text-muted-foreground">
                  {isAr
                    ? "حدث خطأ أثناء تحميل هذه الوثيقة القانونية. حاول تحديث الصفحة أو العودة لاحقاً."
                    : "Something went wrong loading this legal document. Try refreshing the page or come back shortly."}
                </p>
              </div>
            </div>
          )}

          {!loading && version && (
            <article>
              <header className="mb-6">
                <h1 className="text-heading-1 font-display font-semibold mb-3">
                  {titleInfo ? (isAr ? titleInfo.ar : titleInfo.en) : version.document_title}
                </h1>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="soft">v{version.version_label}</Badge>
                  {version.effective_at && (
                    <span className="text-caption text-muted-foreground">
                      {isAr ? "ساري من: " : "Effective: "}
                      {new Date(version.effective_at).toLocaleDateString(isAr ? "ar-EG" : "en-US")}
                    </span>
                  )}
                  {version.is_machine_translated && (
                    <Badge variant="warning" className="gap-1">
                      <Languages className="h-3 w-3" />
                      {isAr ? "ترجمة آلية غير مراجعة" : "Unreviewed machine translation"}
                    </Badge>
                  )}
                </div>
                {version.summary_of_changes && (
                  <p className="mt-3 text-caption text-muted-foreground border-s-2 border-border ps-3">
                    {isAr ? "ملخص التغييرات: " : "Summary of changes: "}
                    {version.summary_of_changes}
                  </p>
                )}
              </header>
              <PolicyMarkdown content={version.content_markdown} />
            </article>
          )}
        </div>
      </section>
    </Layout>
  );
}
