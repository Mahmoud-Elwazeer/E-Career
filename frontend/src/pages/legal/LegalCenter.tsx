import { Link } from "react-router-dom";
import {
  FileText, ShieldCheck, Cookie, RotateCcw, CreditCard, Lock, Sparkles,
  ArrowRight, ArrowLeft, Mail, Ban, UserCheck, Server, Globe2, Briefcase, UserCog,
} from "lucide-react";
import { Layout } from "@/components/Layout";
import { useTheme } from "@/hooks/use-theme";
import { usePageMeta } from "@/hooks/use-seo";
import { useEffect, useState } from "react";
import { getLegalEntityPublic, type LegalEntityPublic } from "@/services/legal";

/**
 * Legal Center hub — stable, SEO-indexable entry point for every public legal
 * document. Real links only (no `#` placeholders): every tile routes to a
 * document actually served by the backend's PolicyVersion API.
 *
 * Grouped into 4 categories (continuation pass) rather than one flat grid —
 * mirrors the supplemental legal specs' "grouped, not flat" requirement.
 * Every slug here must have a matching PolicyDocument row seeded by
 * `seed_legal` and a matching entry in PolicyPage.tsx's TITLES map.
 */
type DocEntry = { slug: string; icon: typeof FileText; en: string; ar: string };

const CATEGORIES: { key: string; en: string; ar: string; docs: DocEntry[] }[] = [
  {
    key: "platform",
    en: "Platform",
    ar: "المنصة",
    docs: [
      { slug: "terms", icon: FileText, en: "Terms of Service", ar: "شروط الخدمة" },
      { slug: "acceptable-use", icon: Ban, en: "Acceptable Use Policy", ar: "سياسة الاستخدام المقبول" },
      { slug: "security", icon: Lock, en: "Security Overview", ar: "نظرة عامة على الأمان" },
      { slug: "ai-disclosure", icon: Sparkles, en: "AI Use & Rasheed Disclosure", ar: "استخدام الذكاء الاصطناعي وإفصاح رشيد" },
    ],
  },
  {
    key: "payments",
    en: "Payments & Commercial",
    ar: "الدفع والتجارة",
    docs: [
      { slug: "refunds", icon: RotateCcw, en: "Refund & Cancellation Policy", ar: "سياسة الاسترداد والإلغاء" },
      { slug: "payment-security", icon: CreditCard, en: "Payment & Card Security Policy", ar: "سياسة أمان الدفع والبطاقات" },
    ],
  },
  {
    key: "roles",
    en: "Candidate & Employer",
    ar: "المتقدمون وأصحاب العمل",
    docs: [
      { slug: "candidate-privacy", icon: UserCheck, en: "Candidate Privacy Notice", ar: "إشعار خصوصية المتقدمين" },
      { slug: "business-terms", icon: Briefcase, en: "Employer & Business Terms", ar: "شروط أصحاب العمل والشركات" },
    ],
  },
  {
    key: "data",
    en: "Data & Governance",
    ar: "البيانات والحوكمة",
    docs: [
      { slug: "privacy", icon: ShieldCheck, en: "Privacy Policy", ar: "سياسة الخصوصية" },
      { slug: "cookies", icon: Cookie, en: "Cookie Policy", ar: "سياسة ملفات تعريف الارتباط" },
      { slug: "data-rights", icon: UserCog, en: "Your Data Rights", ar: "حقوقك في البيانات" },
      { slug: "subprocessors", icon: Server, en: "Sub-processor Disclosure", ar: "إفصاح معالجي البيانات الفرعيين" },
      { slug: "international-transfers", icon: Globe2, en: "International Data Transfers", ar: "النقل الدولي للبيانات" },
    ],
  },
];

export default function LegalCenter() {
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const [entity, setEntity] = useState<LegalEntityPublic | null>(null);

  usePageMeta(
    isAr ? "المركز القانوني" : "Legal Center",
    isAr
      ? "الشروط والخصوصية وملفات تعريف الارتباط وسياسات الدفع لمنصة USAM."
      : "Terms, privacy, cookies, and payment policies for the USAM platform.",
  );

  useEffect(() => {
    getLegalEntityPublic().then(setEntity).catch(() => setEntity(null));
  }, []);

  return (
    <Layout>
      <section className="chamber chamber-grid relative overflow-hidden text-primary-foreground">
        <div className="glow-blob" style={{ width: 340, height: 340, top: -120, insetInlineEnd: -80, background: "hsl(var(--secondary) / 0.28)" }} />
        <div className="container relative z-10 max-w-3xl py-16 text-center md:py-20">
          <span className="eyebrow-mono text-primary-foreground/70 mb-4 justify-center">
            <span className="signal-dot" /> {isAr ? "المركز القانوني" : "LEGAL CENTER"}
          </span>
          <h1 className="text-display-serif mt-3 mb-4">
            {isAr ? "الشروط والسياسات" : "Terms & policies"}
          </h1>
          <p className="text-body-lg opacity-80">
            {isAr
              ? "كل وثيقة هنا تعكس كيفية عمل المنصة فعلياً اليوم. أي حقيقة قانونية لم نؤكدها بعد توضع صراحةً بحاجة لمراجعة قانونية."
              : "Every document here reflects how the platform actually works today. Anything we haven't legally confirmed yet is marked explicitly, not guessed."}
          </p>
        </div>
      </section>

      <section className="section-y">
        <div className="container">
          {CATEGORIES.map((cat) => (
            <div key={cat.key} className="mb-10">
              <h2 className="text-heading-2 font-semibold mb-4">{isAr ? cat.ar : cat.en}</h2>
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {cat.docs.map((d) => (
                  <Link
                    key={d.slug}
                    to={`/legal/${d.slug}`}
                    className="card-premium group flex items-start gap-4 p-6 transition-transform hover:-translate-y-0.5"
                  >
                    <span className="icon-tile h-12 w-12 shrink-0"><d.icon className="h-6 w-6 text-primary" /></span>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-heading-3 font-semibold mb-1">{isAr ? d.ar : d.en}</h3>
                      <span className="inline-flex items-center gap-1 text-caption font-medium text-primary link-underline">
                        {isAr ? "اقرأ المزيد" : "Read more"} <Arrow className="h-3.5 w-3.5" />
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}

          <div className="card-premium mt-8 flex flex-col gap-3 p-6 md:flex-row md:items-center md:justify-between">
            <div>
              <h3 className="text-heading-3 font-semibold mb-1">
                {isAr ? "تواصل بشأن الخصوصية أو القانون" : "Privacy & legal contact"}
              </h3>
              {entity?.is_configured ? (
                <p className="text-body text-muted-foreground">
                  {entity.legal_entity_name}
                  {entity.privacy_contact_email ? ` — ${entity.privacy_contact_email}` : ""}
                </p>
              ) : (
                <p className="text-body text-muted-foreground">
                  {isAr
                    ? "جهة الاتصال القانونية الرسمية قيد المراجعة والتهيئة من قِبل الإدارة."
                    : "The formal legal contact is REQUIRES LEGAL REVIEW / CONFIGURATION — not yet set by admin."}
                </p>
              )}
            </div>
            <Link
              to="/app/privacy-center"
              className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-primary px-5 h-11 text-body font-medium text-primary-foreground press-feedback"
            >
              <Mail className="h-4 w-4" /> {isAr ? "مركز الخصوصية" : "Privacy Center"}
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
}
