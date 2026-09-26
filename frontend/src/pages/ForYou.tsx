/**
 * For You — the individual's personalized hub (Section 11).
 * Organizes services by context (discover, career tools, AI, grow) instead of
 * one huge feature list. Every card links to a real existing feature route.
 */
import { Link } from "react-router-dom";
import {
  Sparkles, Search, MessageCircle, FileText, Mic, Target, Network,
  DollarSign, Award, Bookmark, ClipboardList, ArrowRight, ArrowLeft, Compass,
} from "lucide-react";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";

interface Item { icon: typeof Search; to: string; en: string; ar: string; descEn: string; descAr: string; }
interface Group { titleEn: string; titleAr: string; items: Item[]; }

const GROUPS: Group[] = [
  {
    titleEn: "Discover opportunities", titleAr: "اكتشف الفرص",
    items: [
      { icon: Search, to: "/app/jobs", en: "Find Jobs", ar: "ابحث عن وظائف", descEn: "Search verified, direct-employer roles.", descAr: "وظائف موثقة من أصحاب العمل مباشرة." },
      { icon: Sparkles, to: "/app/recommendations", en: "For You Matches", ar: "توصيات لك", descEn: "Jobs picked for your skills, with reasons.", descAr: "وظائف مختارة لمهاراتك مع الأسباب." },
      { icon: Bookmark, to: "/app/saved", en: "Saved Jobs", ar: "المحفوظات", descEn: "Everything you bookmarked.", descAr: "كل ما حفظته." },
      { icon: ClipboardList, to: "/app/applications", en: "Applications", ar: "طلباتي", descEn: "Track every application's status.", descAr: "تابع حالة كل طلب." },
    ],
  },
  {
    titleEn: "Career tools", titleAr: "أدوات المسار",
    items: [
      { icon: FileText, to: "/app/resume", en: "Resume Builder", ar: "منشئ السيرة", descEn: "Build and export an ATS-ready CV.", descAr: "أنشئ سيرة متوافقة مع أنظمة التوظيف." },
      { icon: FileText, to: "/app/cover-letters", en: "Cover Letters", ar: "خطابات التغطية", descEn: "Generate tailored cover letters.", descAr: "أنشئ رسائل تقديم مخصصة." },
      { icon: Target, to: "/app/talent-score", en: "Talent Score", ar: "نقاط الموهبة", descEn: "Measure and grow your employability.", descAr: "قِس جاهزيتك المهنية وطوّرها." },
      { icon: Network, to: "/app/career-graph", en: "Career Graph", ar: "خريطة المسار", descEn: "Skills, gaps and growth paths.", descAr: "المهارات والفجوات ومسارات النمو." },
    ],
  },
  {
    titleEn: "AI & preparation", titleAr: "الذكاء والتحضير",
    items: [
      { icon: MessageCircle, to: "/app/rashid", en: "Rasheed AI Coach", ar: "المساعد رشيد", descEn: "24/7 career guidance grounded in your profile.", descAr: "إرشاد مهني على مدار الساعة بناءً على ملفك." },
      { icon: Mic, to: "/app/interviews", en: "Interview Practice", ar: "تدريب المقابلات", descEn: "Rehearse with an AI voice coach.", descAr: "تدرّب مع مدرب صوتي ذكي." },
      { icon: Award, to: "/app/assessments", en: "Assessments", ar: "التقييمات", descEn: "Prove your skills with badges.", descAr: "أثبت مهاراتك بشارات." },
      { icon: DollarSign, to: "/app/salary", en: "Salary Insights", ar: "رؤى الرواتب", descEn: "Benchmark your market value.", descAr: "قارن قيمتك السوقية." },
    ],
  },
];

export default function ForYou() {
  const { lang, dir } = useTheme();
  const { user } = useAuth();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const name = (user?.name || user?.first_name || "").split(" ")[0];

  return (
    <AppShell>
      <PageHeader
        title={name ? (isAr ? `مرحباً ${name}` : `For you, ${name}`) : (isAr ? "مخصص لك" : "For You")}
        description={isAr ? "خدماتك المهنية منظّمة حسب سياقك." : "Your career services, organized by what you need next."}
      />

      <div className="space-y-10">
        {GROUPS.map((g) => (
          <section key={g.titleEn}>
            <div className="mb-4 flex items-center gap-2">
              <Compass className="h-4 w-4 text-primary" />
              <h2 className="text-heading-3 font-semibold">{isAr ? g.titleAr : g.titleEn}</h2>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {g.items.map((it) => (
                <Link key={it.en} to={it.to} className="card-premium card-accent-top group flex h-full flex-col p-5">
                  <span className="icon-tile mb-3 h-11 w-11"><it.icon className="h-5 w-5 text-primary" /></span>
                  <h3 className="text-body font-semibold mb-1 group-hover:text-primary transition-colors">{isAr ? it.ar : it.en}</h3>
                  <p className="text-caption text-muted-foreground leading-relaxed flex-1">{isAr ? it.descAr : it.descEn}</p>
                  <span className="mt-3 inline-flex items-center gap-1 text-caption font-medium text-primary">
                    {isAr ? "افتح" : "Open"} <Arrow className="h-3 w-3 group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5 transition-transform" />
                  </span>
                </Link>
              ))}
            </div>
          </section>
        ))}
      </div>
    </AppShell>
  );
}
