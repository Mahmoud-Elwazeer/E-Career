import { Link } from "react-router-dom";
import { Wifi, GraduationCap, Rocket, Laptop, Megaphone } from "lucide-react";
import { ScrollReveal } from "@/components/motion";
import { motion, useReducedMotion } from "framer-motion";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";

const filters = [
  { icon: Wifi, en: "Remote Jobs", ar: "وظائف عن بعد", query: "locationType=remote" },
  { icon: GraduationCap, en: "Internships", ar: "تدريب", query: "experienceLevel=entry" },
  { icon: Rocket, en: "Entry Level", ar: "مبتدئ", query: "experienceLevel=entry" },
  { icon: Laptop, en: "Tech", ar: "تكنولوجيا", query: "industry=technology" },
  { icon: Megaphone, en: "Marketing", ar: "تسويق", query: "industry=marketing" },
];

export function QuickFilters() {
  const { lang } = useTheme();
  const { isAuthenticated } = useAuth();
  const isAr = lang === "ar";
  const reduced = useReducedMotion();
  const basePath = isAuthenticated ? "/app/jobs" : "/login";

  return (
    <section className="border-b bg-surface-1">
      <div className="container py-5">
        <ScrollReveal>
          <div className="flex items-center gap-3 overflow-x-auto pb-1 scrollbar-none">
            <span className="text-caption text-muted-foreground whitespace-nowrap shrink-0">
              {isAr ? "فلتر سريع:" : "Quick filter:"}
            </span>
            {filters.map((f, i) => (
              <motion.div
                key={f.en}
                initial={reduced ? {} : { opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.06, duration: 0.25 }}
              >
                <Link
                  to={`${basePath}?${f.query}`}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-full border bg-card text-body text-foreground/80 hover:border-primary/40 hover:text-primary whitespace-nowrap transition-all duration-200 press-feedback"
                >
                  <f.icon className="h-3.5 w-3.5" />
                  {isAr ? f.ar : f.en}
                </Link>
              </motion.div>
            ))}
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
