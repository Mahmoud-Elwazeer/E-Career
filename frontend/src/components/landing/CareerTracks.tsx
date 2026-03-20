import { Link } from "react-router-dom";
import { TrendingUp, Code2, Palette, Database, Cloud, Megaphone, ArrowRight, ArrowLeft } from "lucide-react";
import { ScrollReveal, StaggerContainer, StaggerItem, AnimatedCard, CountUp } from "@/components/motion";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";
// mock-data removed

const careerTracks = [
  {
    id: "uiux",
    icon: Palette,
    en: "UI/UX Design",
    ar: "تصميم واجهات",
    keywords: ["UX", "UI", "Figma", "Design"],
    avgSalary: "$4,500",
    trending: true,
  },
  {
    id: "swe",
    icon: Code2,
    en: "Software Engineering",
    ar: "هندسة البرمجيات",
    keywords: ["React", "Node", "TypeScript", "Frontend", "Backend", "Developer", "Engineer"],
    avgSalary: "$7,200",
    trending: true,
  },
  {
    id: "data",
    icon: Database,
    en: "Data Science",
    ar: "علم البيانات",
    keywords: ["Data", "SQL", "Python", "ML", "Analyst"],
    avgSalary: "$6,800",
    trending: false,
  },
  {
    id: "devops",
    icon: Cloud,
    en: "DevOps & Cloud",
    ar: "DevOps والسحابة",
    keywords: ["DevOps", "AWS", "Kubernetes", "Docker", "CI/CD"],
    avgSalary: "$8,000",
    trending: true,
  },
  {
    id: "marketing",
    icon: Megaphone,
    en: "Digital Marketing",
    ar: "التسويق الرقمي",
    keywords: ["Marketing", "SEO", "Social Media", "Content"],
    avgSalary: "$3,800",
    trending: false,
  },
];

function getTrackCounts(): Record<string, number> {
  // Static approximate counts — real counts load from API on jobs page
  return { uiux: 3, swe: 8, data: 4, cloud: 3, marketing: 4 };
}

export function CareerTracks() {
  const { lang, dir } = useTheme();
  const { isAuthenticated } = useAuth();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const jobsPath = isAuthenticated ? "/app/jobs" : "/login";
  const counts = getTrackCounts();

  return (
    <section className="py-14">
      <div className="container">
        <ScrollReveal>
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-heading-2">{isAr ? "مسارات مهنية رائجة" : "Popular Career Paths"}</h2>
              <p className="text-body text-muted-foreground mt-1">
                {isAr ? "اكتشف المسارات الأكثر طلباً في السوق" : "Explore the most in-demand career tracks"}
              </p>
            </div>
          </div>
        </ScrollReveal>
        <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4" staggerDelay={0.06}>
          {careerTracks.map((track) => {
            const count = counts[track.id] ?? 0;
            return (
              <StaggerItem key={track.id}>
                <AnimatedCard>
                  <Link
                    to={`${jobsPath}?q=${track.keywords[0]}`}
                    className="flex flex-col p-5 rounded-xl border bg-card hover:border-primary/30 transition-all duration-200 group h-full"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="rounded-lg bg-primary-muted p-2.5">
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
                      {isAr ? `متوسط الراتب: ${track.avgSalary}` : `Avg. salary: ${track.avgSalary}`}
                    </p>
                    <div className="mt-auto flex items-center justify-between">
                      <span className="text-caption font-medium text-primary">
                        <CountUp target={count} duration={800} /> {isAr ? "وظيفة" : "jobs"}
                      </span>
                      <Arrow className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5 transition-all" />
                    </div>
                  </Link>
                </AnimatedCard>
              </StaggerItem>
            );
          })}
        </StaggerContainer>
      </div>
    </section>
  );
}
