import {
  MessageCircle, FileText, Mic, Sparkles, Target, ShieldCheck,
  Briefcase, Users2, ListChecks, GraduationCap, LineChart, BellRing,
  type LucideIcon,
} from "lucide-react";

/**
 * audience-content — the single source of truth for what each audience
 * (Individuals / Businesses) gets. The landing switcher, the dedicated
 * /for-individuals and /for-businesses pages, and the feature showcase all
 * draw from here so the messaging never drifts apart.
 *
 * Every `to` points at a REAL existing route/feature. Gated app routes are
 * sent through /login (carrying `from`) by the consuming component.
 */

export interface AudienceFeature {
  icon: LucideIcon;
  en: string; ar: string;
  descEn: string; descAr: string;
  to: string;
}

export interface AudienceStep {
  en: string; ar: string;
  descEn: string; descAr: string;
}

export interface AudienceContent {
  key: "individuals" | "businesses";
  eyebrowEn: string; eyebrowAr: string;
  titleEn: string; titleAr: string;
  leadEn: string; leadAr: string;
  primaryCta: { en: string; ar: string; to: string };
  features: AudienceFeature[];
  steps: AudienceStep[];
}

export const INDIVIDUALS: AudienceContent = {
  key: "individuals",
  eyebrowEn: "FOR INDIVIDUALS", eyebrowAr: "للأفراد",
  titleEn: "Your career, guided end to end", titleAr: "مسارك المهني، بمرافقة من البداية للنهاية",
  leadEn: "From discovering verified roles to landing the offer and growing after — Rasheed and the platform guide every step, grounded in your real profile.",
  leadAr: "من اكتشاف وظائف موثقة إلى الحصول على العرض والنمو بعده — يرافقك رشيد والمنصة في كل خطوة بناءً على ملفك الحقيقي.",
  primaryCta: { en: "Get started free", ar: "ابدأ مجاناً", to: "/app/jobs" },
  features: [
    { icon: MessageCircle, en: "Rasheed — your AI career coach", ar: "رشيد — مساعدك المهني", descEn: "Chat 24/7 for CV feedback, job matches, cover letters and interview prep — grounded in your real profile.", descAr: "دردش على مدار الساعة لمراجعة سيرتك ووظائف مطابقة ورسائل تقديم وتحضير للمقابلات.", to: "/app/rashid" },
    { icon: FileText, en: "Resume Builder", ar: "منشئ السيرة الذاتية", descEn: "Craft and export an ATS-ready CV that passes the screeners.", descAr: "أنشئ وصدّر سيرة متوافقة مع أنظمة التوظيف.", to: "/app/resume" },
    { icon: Mic, en: "Interview Practice", ar: "تدريب المقابلات", descEn: "Rehearse real questions with an AI voice coach and get feedback.", descAr: "تدرّب على أسئلة حقيقية مع مدرب صوتي ذكي واحصل على ملاحظات.", to: "/app/interviews" },
    { icon: Sparkles, en: "Personalized matches", ar: "توصيات مخصصة", descEn: "See jobs picked for your skills — with the reasons behind each match.", descAr: "وظائف مختارة لمهاراتك مع أسباب كل مطابقة.", to: "/app/recommendations" },
    { icon: Target, en: "Talent Score", ar: "نقاط الموهبة", descEn: "Measure your employability and see exactly how to grow it.", descAr: "قِس جاهزيتك المهنية واعرف كيف تطوّرها.", to: "/app/talent-score" },
    { icon: ShieldCheck, en: "Verified direct-apply", ar: "تقديم مباشر موثّق", descEn: "Every job links to the real employer source — no aggregator middlemen.", descAr: "كل وظيفة مرتبطة بالمصدر الأصلي — بدون وسطاء.", to: "/app/jobs" },
    { icon: LineChart, en: "Salary insights", ar: "رؤى الرواتب", descEn: "Know the real range before you apply or negotiate.", descAr: "اعرف النطاق الحقيقي قبل التقديم أو التفاوض.", to: "/app/salary" },
    { icon: BellRing, en: "Smart job alerts", ar: "تنبيهات ذكية", descEn: "Get notified the moment a matching verified role is posted.", descAr: "احصل على تنبيه فور نشر وظيفة موثقة مطابقة.", to: "/app/alerts" },
  ],
  steps: [
    { en: "Build your profile", ar: "ابنِ ملفك", descEn: "Import or write your CV; the platform maps your skills into a live career graph.", descAr: "استورد أو اكتب سيرتك؛ تحوّل المنصة مهاراتك إلى رسم بياني حي." },
    { en: "Match with verified roles", ar: "طابق مع وظائف موثقة", descEn: "See scored matches from direct-employer sources, with the reasons.", descAr: "شاهد مطابقات مقيّمة من مصادر أصحاب العمل مباشرة مع الأسباب." },
    { en: "Prepare with Rasheed", ar: "استعد مع رشيد", descEn: "Sharpen your CV, cover letter and interview answers with your AI coach.", descAr: "طوّر سيرتك ورسالتك وإجاباتك مع مساعدك الذكي." },
    { en: "Apply & grow", ar: "قدّم وتطوّر", descEn: "Apply directly to the employer and track every application in one place.", descAr: "قدّم مباشرة لصاحب العمل وتابع كل طلباتك في مكان واحد." },
  ],
};

export const BUSINESSES: AudienceContent = {
  key: "businesses",
  eyebrowEn: "FOR BUSINESSES", eyebrowAr: "للشركات",
  titleEn: "Hire faster with intelligence", titleAr: "وظّف أسرع بذكاء",
  leadEn: "Post domain-verified roles, let the platform rank applicants by real fit, and build reusable talent pools — every candidate arrives with evidence.",
  leadAr: "انشر وظائف موثقة بالنطاق، ودع المنصة ترتّب المتقدمين حسب الملاءمة الحقيقية، وابنِ قوائم مواهب قابلة لإعادة الاستخدام.",
  primaryCta: { en: "Create Employer Account", ar: "أنشئ حساب شركة", to: "/app/employer/register" },
  features: [
    { icon: Briefcase, en: "Post verified roles", ar: "انشر وظائف موثقة", descEn: "Publish jobs linked to your own domain — candidates apply directly, no middlemen.", descAr: "انشر وظائف مرتبطة بنطاقك الرسمي — تقديم مباشر بدون وسطاء.", to: "/app/employer/post-job" },
    { icon: ListChecks, en: "Auto candidate ranking", ar: "ترتيب تلقائي للمرشحين", descEn: "Rank applicants by skill, experience and fit — with knockout rules and evidence.", descAr: "رتّب المتقدمين بالمهارة والخبرة والملاءمة مع قواعد استبعاد وأدلة.", to: "/app/employer/talent-search" },
    { icon: Users2, en: "Talent pools", ar: "قوائم المواهب", descEn: "Build and search reusable candidate pools across all your roles.", descAr: "أنشئ وابحث في قوائم مرشحين قابلة لإعادة الاستخدام.", to: "/app/employer/talent-search" },
    { icon: Sparkles, en: "Match intelligence", ar: "ذكاء المطابقة", descEn: "See the strongest candidates for each role, ranked with reasons.", descAr: "شاهد أقوى المرشحين لكل وظيفة مرتبين مع الأسباب.", to: "/app/employer/talent-search" },
    { icon: Target, en: "Screening questions", ar: "أسئلة الفرز", descEn: "Add knockout questions that filter applicants automatically.", descAr: "أضف أسئلة استبعاد تصفّي المتقدمين تلقائياً.", to: "/app/employer/post-job" },
    { icon: ShieldCheck, en: "Domain-verified posting", ar: "نشر موثّق بالنطاق", descEn: "Your apply URL is verified against your company domain to build candidate trust.", descAr: "يتم التحقق من رابط التقديم مقابل نطاق شركتك لبناء الثقة.", to: "/app/employer/register" },
  ],
  steps: [
    { en: "Create your company", ar: "أنشئ شركتك", descEn: "Register your employer profile and verify your domain.", descAr: "سجّل ملف صاحب العمل ووثّق نطاقك." },
    { en: "Post a verified role", ar: "انشر وظيفة موثقة", descEn: "Publish a job with screening questions and a direct-apply URL.", descAr: "انشر وظيفة بأسئلة فرز ورابط تقديم مباشر." },
    { en: "Review ranked candidates", ar: "راجع المرشحين المرتبين", descEn: "The platform ranks applicants by fit with supporting evidence.", descAr: "ترتّب المنصة المتقدمين حسب الملاءمة مع الأدلة." },
    { en: "Hire & reuse the pool", ar: "وظّف وأعد استخدام القائمة", descEn: "Move candidates through hiring and keep strong ones in your talent pool.", descAr: "انقل المرشحين خلال التوظيف واحتفظ بالأقوياء في قائمتك." },
  ],
};

export const AUDIENCES: Record<"individuals" | "businesses", AudienceContent> = {
  individuals: INDIVIDUALS,
  businesses: BUSINESSES,
};
