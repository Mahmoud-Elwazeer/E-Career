import { ScrollReveal } from "@/components/motion";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useTheme } from "@/hooks/use-theme";

/**
 * FaqSection — answers the real questions a first-time USAM visitor asks.
 * Content maps to actual platform behavior (aggregation, direct-apply moat,
 * Rasheed, pricing, employers). No invented claims.
 */

interface Qa {
  qEn: string;
  qAr: string;
  aEn: string;
  aAr: string;
}

const FAQS: Qa[] = [
  {
    qEn: "What makes USAM different from other job boards?",
    qAr: "ما الذي يميّز USAM عن مواقع التوظيف الأخرى؟",
    aEn: "USAM aggregates verified jobs from top sources across MENA and links every listing directly to the original employer or ATS — never through third-party apply middlemen. It also layers an AI career coach, matching, and CV tools on top, so it works as a career operating system, not just a search box.",
    aAr: "يجمع USAM وظائف موثقة من أفضل المصادر في المنطقة ويربط كل وظيفة مباشرةً بصاحب العمل الأصلي — بدون وسطاء. كما يضيف مساعداً مهنياً ذكياً وأدوات مطابقة وسيرة ذاتية، ليعمل كنظام مهني متكامل وليس مجرد بحث.",
  },
  {
    qEn: "Who is Rasheed?",
    qAr: "من هو رشيد؟",
    aEn: "Rasheed is your AI career coach. He reviews your CV, explains why a job matches you, drafts cover letters, and runs interview practice — grounded in your real profile, available across the platform.",
    aAr: "رشيد هو مساعدك المهني الذكي. يراجع سيرتك، ويشرح سبب مطابقة كل وظيفة لك، ويكتب رسائل التقديم، ويجري تدريباً على المقابلات — بالاعتماد على ملفك الحقيقي.",
  },
  {
    qEn: "Is it free to get started?",
    qAr: "هل البدء مجاني؟",
    aEn: "Yes. You can create an account, search jobs, get matches, and use core tools for free. Paid plans unlock deeper coaching and advanced features — see the pricing page for details.",
    aAr: "نعم. يمكنك إنشاء حساب والبحث عن الوظائف والحصول على التوصيات واستخدام الأدوات الأساسية مجاناً. تفتح الباقات المدفوعة ميزات متقدمة — راجع صفحة الأسعار.",
  },
  {
    qEn: "Do you support employers and hiring teams?",
    qAr: "هل تدعمون أصحاب العمل وفرق التوظيف؟",
    aEn: "Yes. Employers can post jobs, search the talent pool, and manage candidates from a dedicated dashboard. Create a company account to start hiring.",
    aAr: "نعم. يمكن لأصحاب العمل نشر الوظائف والبحث في قاعدة المواهب وإدارة المرشحين من لوحة مخصصة. أنشئ حساب شركة لتبدأ التوظيف.",
  },
  {
    qEn: "Which regions and industries are covered?",
    qAr: "ما المناطق والقطاعات المشمولة؟",
    aEn: "USAM focuses on MENA markets across many industries — technology, finance, healthcare, design, marketing, engineering and more — with new roles added continuously.",
    aAr: "يركّز USAM على أسواق الشرق الأوسط وشمال أفريقيا عبر قطاعات متعددة — التقنية والمالية والرعاية الصحية والتصميم والتسويق والهندسة وغيرها — مع إضافة وظائف جديدة باستمرار.",
  },
];

export function FaqSection() {
  const { lang } = useTheme();
  const isAr = lang === "ar";

  return (
    <section className="section-band section-y">
      <div className="container">
        <div className="mx-auto max-w-3xl">
          <ScrollReveal>
            <div className="flex flex-col items-center text-center mb-10">
              <span className="eyebrow-mono mb-3">{isAr ? "الأسئلة الشائعة" : "FAQ"}</span>
              <h2 className="text-display-serif">
                {isAr ? "أسئلة متكررة" : "Questions, answered"}
              </h2>
            </div>
          </ScrollReveal>

          <Accordion type="single" collapsible className="w-full">
            {FAQS.map((f, i) => (
              <AccordionItem
                key={i}
                value={`faq-${i}`}
                className="paper-card mb-3 border px-5 data-[state=open]:border-primary/30"
              >
                <AccordionTrigger className="text-start text-body-lg font-medium hover:no-underline py-5">
                  {isAr ? f.qAr : f.qEn}
                </AccordionTrigger>
                <AccordionContent className="text-body text-muted-foreground leading-relaxed pb-5">
                  {isAr ? f.aAr : f.aEn}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </div>
    </section>
  );
}
