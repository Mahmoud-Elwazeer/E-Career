import { Link } from "react-router-dom";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";
import { Logo } from "@/components/Logo";

/**
 * Footer — grouped, complete navigation surface.
 * Columns: For Individuals · For Employers · Company.
 * Anonymous visitors get feature links routed through /login (with `from`),
 * so the footer is a real discovery surface, not a dead end.
 */
export function Footer() {
  const { lang } = useTheme();
  const { isAuthenticated } = useAuth();
  const isAr = lang === "ar";

  // gated link: authenticated -> real route; anonymous -> /login carrying `from`
  const g = (to: string) => (isAuthenticated ? to : "/login");
  const gs = (to: string) => (isAuthenticated ? {} : { state: { from: to } });

  const individuals = [
    { to: "/app/jobs", en: "Find Jobs", ar: "ابحث عن وظائف" },
    { to: "/app/rashid", en: "Rasheed AI Coach", ar: "المساعد رشيد" },
    { to: "/app/resume", en: "Resume Builder", ar: "منشئ السيرة" },
    { to: "/app/interviews", en: "Interview Prep", ar: "تحضير المقابلات" },
    { to: "/app/recommendations", en: "For You", ar: "مقترحة لك" },
    { to: "/app/saved", en: "Saved Jobs", ar: "الوظائف المحفوظة" },
  ];
  const employers = [
    { to: "/app/employer/register", en: "Become an Employer", ar: "سجّل كصاحب عمل" },
    { to: "/app/employer/post-job", en: "Post a Job", ar: "انشر وظيفة" },
    { to: "/app/employer/talent-search", en: "Search Talent", ar: "ابحث عن مواهب" },
  ];
  const company = [
    { to: "/pricing", en: "Pricing", ar: "الأسعار", gated: false },
    { to: "/about", en: "About USAM", ar: "عن USAM", gated: false },
    { to: "/api-docs", en: "API Docs", ar: "وثائق الواجهة", gated: false },
  ];

  const linkCls = "text-body opacity-75 hover:opacity-100 transition-opacity link-underline w-fit";

  return (
    <footer className="hero-gradient border-t border-primary-foreground/10 text-primary-foreground">
      <div className="container relative z-10 py-14">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-12">
          {/* Brand */}
          <div className="md:col-span-4 max-w-sm">
            <Logo variant="onDark" className="h-9 mb-4" />
            <p className="text-body opacity-75 leading-relaxed">
              {isAr
                ? "بحث واحد. كل الفرص. نجمع الوظائف من أفضل المنصات في منطقة الشرق الأوسط ونربطك مباشرة بأصحاب العمل."
                : "One search. Every opportunity. Verified jobs across MENA, connected directly to real employers."}
            </p>
          </div>

          {/* For Individuals */}
          <div className="md:col-span-3">
            <h4 className="font-medium mb-3">{isAr ? "للأفراد" : "For Individuals"}</h4>
            <nav className="flex flex-col gap-2">
              {individuals.map((l) => (
                <Link key={l.to} to={g(l.to)} {...gs(l.to)} className={linkCls}>
                  {isAr ? l.ar : l.en}
                </Link>
              ))}
            </nav>
          </div>

          {/* For Employers */}
          <div className="md:col-span-3">
            <h4 className="font-medium mb-3">{isAr ? "لأصحاب العمل" : "For Employers"}</h4>
            <nav className="flex flex-col gap-2">
              {employers.map((l) => (
                <Link key={l.to} to={g(l.to)} {...gs(l.to)} className={linkCls}>
                  {isAr ? l.ar : l.en}
                </Link>
              ))}
            </nav>
          </div>

          {/* Company */}
          <div className="md:col-span-2">
            <h4 className="font-medium mb-3">{isAr ? "الشركة" : "Company"}</h4>
            <nav className="flex flex-col gap-2">
              {company.map((l) => (
                <Link key={l.to} to={l.to} className={linkCls}>
                  {isAr ? l.ar : l.en}
                </Link>
              ))}
            </nav>
          </div>
        </div>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-primary-foreground/15 pt-6 text-caption opacity-70">
          <span>© {new Date().getFullYear()} USAM. {isAr ? "جميع الحقوق محفوظة." : "All rights reserved."}</span>
          <span>{isAr ? "صُنع لمنطقة الشرق الأوسط وشمال أفريقيا" : "Built for MENA talent"}</span>
        </div>
      </div>
    </footer>
  );
}
