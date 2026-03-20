import { Link } from "react-router-dom";
import { Bookmark, Bell, Lock, ArrowRight, ArrowLeft } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { ScrollReveal } from "@/components/motion";
import { useAuth } from "@/hooks/use-auth";
import { useSavedJobs } from "@/hooks/use-saved-jobs";
import { useTheme } from "@/hooks/use-theme";
import { MOTION } from "@/lib/motion-tokens";

export function SavedJobsTeaser() {
  const { isAuthenticated } = useAuth();
  const { savedJobs } = useSavedJobs();
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const reduced = useReducedMotion();
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;

  return (
    <section className="py-14">
      <div className="container">
        <ScrollReveal>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Saved Jobs card */}
            <motion.div
              className="bg-card border rounded-xl p-6 flex items-start gap-4"
              whileHover={reduced ? {} : MOTION.presets.hoverLift}
            >
              <div className="rounded-lg bg-primary-muted p-3 shrink-0">
                <Bookmark className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1">
                <h3 className="text-heading-3 mb-1">
                  {isAr ? "الوظائف المحفوظة" : "Saved Jobs"}
                </h3>
                {isAuthenticated ? (
                  <>
                    <p className="text-body text-muted-foreground mb-3">
                      {isAr
                        ? `لديك ${savedJobs.length} وظيفة محفوظة`
                        : `You have ${savedJobs.length} saved job${savedJobs.length !== 1 ? "s" : ""}`}
                    </p>
                    <Button asChild variant="outline" size="sm" className="rounded-lg">
                      <Link to="/app/saved">
                        {isAr ? "عرض المحفوظات" : "View saved"} <Arrow className="h-3 w-3 ms-1" />
                      </Link>
                    </Button>
                  </>
                ) : (
                  <>
                    <p className="text-body text-muted-foreground mb-3">
                      {isAr
                        ? "احفظ الوظائف المفضلة وارجع لها لاحقاً"
                        : "Save your favorite jobs and come back to them later"}
                    </p>
                    <Button asChild variant="outline" size="sm" className="rounded-lg gap-1.5">
                      <Link to="/login">
                        <Lock className="h-3 w-3" />
                        {isAr ? "سجّل للحفظ" : "Sign in to save"}
                      </Link>
                    </Button>
                  </>
                )}
              </div>
            </motion.div>

            {/* Alerts teaser card */}
            <motion.div
              className="bg-card border rounded-xl p-6 flex items-start gap-4"
              whileHover={reduced ? {} : MOTION.presets.hoverLift}
            >
              <div className="rounded-lg bg-primary-muted p-3 shrink-0">
                <Bell className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1">
                <h3 className="text-heading-3 mb-1">
                  {isAr ? "تنبيهات الوظائف" : "Job Alerts"}
                </h3>
                {isAuthenticated ? (
                  <>
                    <p className="text-body text-muted-foreground mb-3">
                      {isAr
                        ? "احصل على إشعار فوري عند توفر وظائف جديدة تناسبك"
                        : "Get notified instantly when new matching jobs appear"}
                    </p>
                    <Button asChild variant="outline" size="sm" className="rounded-lg">
                      <Link to="/app/alerts">
                        {isAr ? "إدارة التنبيهات" : "Manage alerts"} <Arrow className="h-3 w-3 ms-1" />
                      </Link>
                    </Button>
                  </>
                ) : (
                  <>
                    <p className="text-body text-muted-foreground mb-3">
                      {isAr
                        ? "أنشئ تنبيهاً ولا تفوت أي فرصة مناسبة"
                        : "Create alerts and never miss a matching opportunity"}
                    </p>
                    <Button asChild variant="outline" size="sm" className="rounded-lg gap-1.5">
                      <Link to="/login">
                        <Lock className="h-3 w-3" />
                        {isAr ? "سجّل للتنبيهات" : "Sign in for alerts"}
                      </Link>
                    </Button>
                  </>
                )}
              </div>
            </motion.div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
