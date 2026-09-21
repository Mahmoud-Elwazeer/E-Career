import { Link } from "react-router-dom";
import { TrendingUp, Code2, Palette, Database, Cloud, Megaphone, ArrowRight, ArrowLeft } from "lucide-react";
import { ScrollReveal, StaggerContainer, StaggerItem, AnimatedCard } from "@/components/motion";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";

// NOTE: no salary figures or job counts are hardcoded here. These are real,
// clickable search entry points — the actual, live job count is shown on the
// jobs results page after the search runs. We do not fabricate market data.

const careerTracks = [
  {
    id: "uiux",
    icon: Palette,
    en: "UI/UX Design",
    ar: "تصميم واجهات",
    keywords: ["UX", "UI", "Figma", "Design"],
    trending: true,
  },
  {
    id: "swe",
    icon: Code2,
    en: "Software Engineering",
    ar: "هندسة البرمجيات",
    keywords: ["React", "Node", "TypeScript", "Frontend", "Backend", "Developer", "Engineer"],
    trending: true,
  },
  {
    id: "data",
    icon: Database,
    en: "Data Science",
    ar: "علم البيانات",
    keywords: ["Data", "SQL", "Python", "ML", "Analyst"],
    trending: false,
  },
  {
    id: "devops",
    icon: Cloud,
    en: "DevOps & Cloud",
    ar: "DevOps والسحابة",
    keywords: ["DevOps", "AWS", "Kubernetes", "Docker", "CI/CD"],
    trending: true,
  },
  {
    id: "marketing",
    icon: Megaphone,
    en: "Digital Marketing",
    ar: "التسويق الرقمي",
    keywords: ["Marketing", "SEO", "Social Media", "Content"],
    trending: false,
  },
];

export function CareerTracks() {
  const { lang, dir } = useTheme();
  const { isAuthenticated } = useAuth();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const jobsPath = isAuthenticated ? "/app/jobs" : "/login";

  return (
    <section className="section-y">
      <div className="container">
        <ScrollReveal>
          <div className="flex items-center justify-between mb-8">
            <div>
              <span className="eyebrow-mono mb-3">{isAr ? "المسارات" : "CAREER TRACKS"}</span>
              <h2 className="text-display-serif mt-3">{isAr ? "مسارات مهنية رائجة" : "Popular career paths"}</h2>
              <p className="text-body-lg text-muted-foreground mt-2">
                {isAr ? "اكتشف المسارات الأكثر طلباً في السوق" : "Explore the most in-demand career tracks"}
              </p>
            </div>
          </div>
        </ScrollReveal>
        <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4" staggerDelay={0.06}>
          {careerTracks.map((track) => (
            <StaggerItem key={track.id}>
              <AnimatedCard>
                <Link
                  to={`${jobsPath}?q=${encodeURIComponent(track.keywords[0])}`}
                  className="card-premium card-accent-top flex flex-col p-5 group h-full"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="icon-tile p-2.5">
                      <track.icon className="h-5 w-5 text-primary" />
                    </div>
                    {track.trending && (
                      <span className="flex items-center gap-1 text-[10px] font-medium text-success bg-success/10 px-2 py-0.5 rounded-full">
                        <TrendingUp className="h-3 w-3" />
                        {isAr ? "رائج" : "Trending"}
                      </span>
                    )}
                  </div>
                  <h3 className="text-body font-medium group-hover:text-primary transition-colors mb-1">
                    {isAr ? track.ar : track.en}
                  </h3>
                  <p className="text-caption text-muted-foreground mb-3">
                    {isAr ? "استعرض الوظائف المتاحة" : "Browse open roles"}
                  </p>
                  <div className="mt-auto flex items-center justify-end">
                    <Arrow className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5 transition-all" />
                  </div>
                </Link>
              </AnimatedCard>
            </StaggerItem>
          ))}
        </StaggerContainer>
      </div>
    </section>
  );
}
