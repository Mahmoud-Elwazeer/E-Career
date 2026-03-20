import { Link } from "react-router-dom";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";

export function Footer() {
  const { lang } = useTheme();
  const { isAuthenticated } = useAuth();
  const jobsPath = isAuthenticated ? "/app/jobs" : "/login";

  return (
    <footer className="us-watermark border-t bg-primary text-primary-foreground">
      <div className="container relative z-10 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <img src="/logo-dark.png" alt="USAM" className="h-9 mb-4 invert" />
            <p className="text-body opacity-80">
              {lang === "ar"
                ? "بحث واحد. كل الفرص. نجمع الوظائف من أفضل المنصات في منطقة الشرق الأوسط."
                : "One search. Every opportunity. Aggregating jobs across MENA for students and professionals."}
            </p>
          </div>
          <div>
            <h4 className="font-medium mb-3">{lang === "ar" ? "روابط سريعة" : "Quick Links"}</h4>
            <nav className="flex flex-col gap-2 text-body opacity-80">
              <Link to={jobsPath} className="hover:opacity-100 transition-opacity link-underline w-fit">
                {lang === "ar" ? "تصفح الوظائف" : "Browse Jobs"}
              </Link>
              <Link to={isAuthenticated ? "/app/profile" : "/login"} className="hover:opacity-100 transition-opacity link-underline w-fit">
                {lang === "ar" ? "الوظائف المحفوظة" : "Saved Jobs"}
              </Link>
              <Link to="/about" className="hover:opacity-100 transition-opacity link-underline w-fit">
                {lang === "ar" ? "عن USAM" : "About USAM"}
              </Link>
            </nav>
          </div>
          <div>
            <h4 className="font-medium mb-3">{lang === "ar" ? "التصنيفات" : "Categories"}</h4>
            <nav className="flex flex-col gap-2 text-body opacity-80">
              <Link to={`${jobsPath}?industry=technology`} className="hover:opacity-100 transition-opacity link-underline w-fit">
                {lang === "ar" ? "التكنولوجيا" : "Technology"}
              </Link>
              <Link to={`${jobsPath}?industry=finance`} className="hover:opacity-100 transition-opacity link-underline w-fit">
                {lang === "ar" ? "المالية" : "Finance"}
              </Link>
              <Link to={`${jobsPath}?industry=healthcare`} className="hover:opacity-100 transition-opacity link-underline w-fit">
                {lang === "ar" ? "الرعاية الصحية" : "Healthcare"}
              </Link>
              <Link to={`${jobsPath}?industry=design`} className="hover:opacity-100 transition-opacity link-underline w-fit">
                {lang === "ar" ? "التصميم" : "Design"}
              </Link>
            </nav>
          </div>
        </div>
        <div className="border-t border-primary-foreground/20 mt-8 pt-6 text-center text-caption opacity-60">
          © {new Date().getFullYear()} USAM. {lang === "ar" ? "جميع الحقوق محفوظة." : "All rights reserved."}
        </div>
      </div>
    </footer>
  );
}
