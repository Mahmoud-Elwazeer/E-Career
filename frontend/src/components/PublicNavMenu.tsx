import { Link } from "react-router-dom";
import {
  Search, MessageCircle, FileText, Mic, Sparkles, Target, DollarSign,
  Award, Code2, Building2, PlusCircle, Users, BadgeCheck, Info, Bell, Network,
} from "lucide-react";
import {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuTrigger,
  NavigationMenuContent,
  NavigationMenuLink,
} from "@/components/ui/navigation-menu";
import { useTheme } from "@/hooks/use-theme";

/**
 * PublicNavMenu — mega-menu for unauthenticated visitors.
 *
 * Two grouped dropdowns (For Individuals / For Employers) surfacing the full
 * feature set, plus direct links. Radix NavigationMenu gives hover-to-open +
 * close-on-leave + keyboard/click support for free. RTL-aware.
 *
 * Feature links point to /login with `from` state so a visitor lands on the
 * feature after authenticating; public pages link directly.
 */

interface Feature {
  to: string;
  /** when true, route through /login carrying `from` */
  gated?: boolean;
  icon: React.ComponentType<{ className?: string }>;
  en: string;
  ar: string;
  descEn: string;
  descAr: string;
}

const individualFeatures: Feature[] = [
  { to: "/app/jobs", gated: true, icon: Search, en: "Find Jobs", ar: "ابحث عن وظائف", descEn: "Search verified jobs across MENA", descAr: "وظائف موثقة عبر المنطقة" },
  { to: "/app/rashid", gated: true, icon: MessageCircle, en: "Rasheed AI Coach", ar: "المساعد رشيد", descEn: "Your 24/7 AI career assistant", descAr: "مساعدك المهني الذكي" },
  { to: "/app/resume", gated: true, icon: FileText, en: "Resume Builder", ar: "منشئ السيرة", descEn: "Build & export a standout CV", descAr: "أنشئ سيرة احترافية" },
  { to: "/app/interviews", gated: true, icon: Mic, en: "Interview Prep", ar: "تحضير المقابلات", descEn: "Practice with an AI voice coach", descAr: "تدرّب بمساعدة الذكاء الاصطناعي" },
  { to: "/app/recommendations", gated: true, icon: Sparkles, en: "For You", ar: "مقترحة لك", descEn: "Personalized job matches", descAr: "وظائف مطابقة لك" },
  { to: "/app/talent-score", gated: true, icon: Target, en: "Talent Score", ar: "نقاط الموهبة", descEn: "Measure & grow your profile", descAr: "قِس ملفك وطوّره" },
  { to: "/app/salary", gated: true, icon: DollarSign, en: "Salary Insights", ar: "رؤى الرواتب", descEn: "Benchmark your market value", descAr: "قارن قيمتك السوقية" },
  { to: "/app/assessments", gated: true, icon: Award, en: "Assessments", ar: "التقييمات", descEn: "Prove your skills with badges", descAr: "أثبت مهاراتك" },
  { to: "/app/coding-practice", gated: true, icon: Code2, en: "Coding Practice", ar: "تدريب البرمجة", descEn: "Sharpen skills with challenges", descAr: "تحدّيات برمجية" },
  { to: "/app/companies", gated: true, icon: Building2, en: "Companies", ar: "الشركات", descEn: "Browse employers hiring now", descAr: "تصفّح الشركات التي توظّف" },
  { to: "/app/career-graph", gated: true, icon: Network, en: "Career Graph", ar: "خريطة المسار", descEn: "Skills, gaps & growth paths", descAr: "المهارات والفجوات ومسارات النمو" },
  { to: "/app/skills", gated: true, icon: Sparkles, en: "Skills Explorer", ar: "مستكشف المهارات", descEn: "Browse the skills taxonomy", descAr: "تصفّح تصنيف المهارات" },
];

const employerFeatures: Feature[] = [
  { to: "/app/employer/register", gated: true, icon: BadgeCheck, en: "Become an Employer", ar: "سجّل كصاحب عمل", descEn: "Create your company account", descAr: "أنشئ حساب شركتك" },
  { to: "/app/employer/post-job", gated: true, icon: PlusCircle, en: "Post a Job", ar: "انشر وظيفة", descEn: "Reach qualified candidates", descAr: "اوصل لأفضل المرشحين" },
  { to: "/app/employer/talent-search", gated: true, icon: Users, en: "Search Talent", ar: "ابحث عن مواهب", descEn: "Browse the candidate pool", descAr: "تصفّح قاعدة المواهب" },
  { to: "/pricing", icon: DollarSign, en: "Pricing & Plans", ar: "الأسعار والباقات", descEn: "Find the right plan", descAr: "اختر الباقة المناسبة" },
];

function href(f: Feature) {
  return f.gated ? "/login" : f.to;
}
function state(f: Feature) {
  return f.gated ? { state: { from: f.to } } : {};
}

function FeatureGrid({ items, cols = 2 }: { items: Feature[]; cols?: 1 | 2 }) {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  return (
    <ul className={`grid gap-1 p-3 ${cols === 2 ? "w-[560px] grid-cols-2" : "w-[340px] grid-cols-1"}`}>
      {items.map((f) => (
        <li key={f.to}>
          <NavigationMenuLink asChild>
            <Link
              to={href(f)}
              {...state(f)}
              className="group flex items-start gap-3 rounded-xl p-3 transition-colors hover:bg-accent focus:bg-accent focus:outline-none"
            >
              <span className="icon-tile mt-0.5 h-9 w-9 shrink-0">
                <f.icon className="h-4 w-4 text-primary" />
              </span>
              <span className="min-w-0">
                <span className="block text-body font-medium text-foreground group-hover:text-primary transition-colors">
                  {isAr ? f.ar : f.en}
                </span>
                <span className="block text-caption text-muted-foreground truncate">
                  {isAr ? f.descAr : f.descEn}
                </span>
              </span>
            </Link>
          </NavigationMenuLink>
        </li>
      ))}
    </ul>
  );
}

export function PublicNavMenu() {
  const { lang } = useTheme();
  const isAr = lang === "ar";

  return (
    <NavigationMenu className="hidden md:flex">
      <NavigationMenuList className="gap-0.5">
        {/* For Individuals */}
        <NavigationMenuItem>
          <NavigationMenuTrigger className="h-9 rounded-lg bg-transparent px-3 text-body font-medium text-foreground/70 hover:text-foreground data-[state=open]:text-foreground">
            {isAr ? "للأفراد" : "For Individuals"}
          </NavigationMenuTrigger>
          <NavigationMenuContent>
            <div className="p-2">
              <p className="px-3 pt-2 pb-1 text-overline tracking-widest text-muted-foreground">
                {isAr ? "أدوات مهنية مدعومة بالذكاء الاصطناعي" : "AI-powered career tools"}
              </p>
              <FeatureGrid items={individualFeatures} cols={2} />
            </div>
          </NavigationMenuContent>
        </NavigationMenuItem>

        {/* For Employers */}
        <NavigationMenuItem>
          <NavigationMenuTrigger className="h-9 rounded-lg bg-transparent px-3 text-body font-medium text-foreground/70 hover:text-foreground data-[state=open]:text-foreground">
            {isAr ? "لأصحاب العمل" : "For Employers"}
          </NavigationMenuTrigger>
          <NavigationMenuContent>
            <div className="p-2">
              <p className="px-3 pt-2 pb-1 text-overline tracking-widest text-muted-foreground">
                {isAr ? "وظّف أسرع وأذكى" : "Hire faster and smarter"}
              </p>
              <FeatureGrid items={employerFeatures} cols={1} />
              <div className="mx-3 my-2 rounded-xl bg-primary/5 border border-primary/10 p-3">
                <div className="flex items-center gap-2 text-body font-medium text-primary">
                  <Building2 className="h-4 w-4" />
                  {isAr ? "ابدأ التوظيف اليوم" : "Start hiring today"}
                </div>
                <Link
                  to="/login"
                  state={{ from: "/app/employer/register" }}
                  className="mt-1 inline-flex items-center gap-1 text-caption font-medium text-primary link-underline"
                >
                  {isAr ? "أنشئ حساب شركة" : "Create a company account"}
                </Link>
              </div>
            </div>
          </NavigationMenuContent>
        </NavigationMenuItem>

        {/* Direct links */}
        <NavigationMenuItem>
          <NavigationMenuLink asChild>
            <Link
              to="/pricing"
              className="inline-flex h-9 items-center rounded-lg px-3 text-body font-medium text-foreground/70 hover:text-foreground transition-colors"
            >
              {isAr ? "الأسعار" : "Pricing"}
            </Link>
          </NavigationMenuLink>
        </NavigationMenuItem>
        <NavigationMenuItem>
          <NavigationMenuLink asChild>
            <Link
              to="/about"
              className="inline-flex h-9 items-center gap-1.5 rounded-lg px-3 text-body font-medium text-foreground/70 hover:text-foreground transition-colors"
            >
              {isAr ? "عن USAM" : "About"}
            </Link>
          </NavigationMenuLink>
        </NavigationMenuItem>
      </NavigationMenuList>
    </NavigationMenu>
  );
}

/** Grouped nav for the mobile sheet (unauthenticated). */
export const MOBILE_PUBLIC_GROUPS = [
  { titleEn: "For Individuals", titleAr: "للأفراد", items: individualFeatures },
  { titleEn: "For Employers", titleAr: "لأصحاب العمل", items: employerFeatures },
];
export { individualFeatures, employerFeatures, href as publicHref, state as publicState };
export type { Feature as PublicFeature };
