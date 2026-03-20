import { useRef, useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { ScrollReveal } from "@/components/motion";
import { Skeleton } from "@/components/ui/skeleton";
import { JobCard } from "@/components/JobCard";
import { TeaserJobCard } from "@/components/TeaserJobCard";
import type { Job } from "@/services/jobs";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";
import { useSavedJobs } from "@/hooks/use-saved-jobs";
import { MOTION } from "@/lib/motion-tokens";

interface FeaturedCarouselProps {
  jobs: Job[];
}

function CarouselSkeleton() {
  return (
    <div className="flex gap-4 overflow-hidden pb-4 -mx-4 px-4">
      {[0, 1, 2].map((i) => (
        <div key={i} className="min-w-[340px] max-w-[380px] shrink-0 space-y-3 p-5 border rounded-xl bg-card">
          <div className="flex items-start gap-3">
            <Skeleton className="h-11 w-11 rounded-lg" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-5 w-16 rounded-full" />
            <Skeleton className="h-5 w-20 rounded-full" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function FeaturedCarousel({ jobs }: FeaturedCarouselProps) {
  const { lang, dir } = useTheme();
  const { isAuthenticated } = useAuth();
  const { isSaved, save, remove } = useSavedJobs();
  const isAr = lang === "ar";
  const reduced = useReducedMotion();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);
  const [isLoading] = useState(false);

  // Drag state for inertial scrolling
  const dragState = useRef({ isDragging: false, startX: 0, scrollStart: 0, velocity: 0, lastX: 0, lastTime: 0 });

  const updateScrollState = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const tolerance = 2;
    if (dir === "rtl") {
      setCanScrollRight(el.scrollLeft < -tolerance);
      setCanScrollLeft(el.scrollLeft > -(el.scrollWidth - el.clientWidth) + tolerance);
    } else {
      setCanScrollLeft(el.scrollLeft > tolerance);
      setCanScrollRight(el.scrollLeft < el.scrollWidth - el.clientWidth - tolerance);
    }
  }, [dir]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener("scroll", updateScrollState, { passive: true });
    updateScrollState();
    return () => el.removeEventListener("scroll", updateScrollState);
  }, [dir, updateScrollState]);

  const scroll = (direction: "left" | "right") => {
    if (!scrollRef.current) return;
    const amount = 380;
    const d = dir === "rtl" ? (direction === "left" ? amount : -amount) : (direction === "left" ? -amount : amount);
    scrollRef.current.scrollBy({ left: d, behavior: "smooth" });
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowLeft") { e.preventDefault(); scroll("left"); }
    if (e.key === "ArrowRight") { e.preventDefault(); scroll("right"); }
  };

  // Inertial drag handlers
  const onPointerDown = (e: React.PointerEvent) => {
    const el = scrollRef.current;
    if (!el) return;
    dragState.current = { isDragging: true, startX: e.clientX, scrollStart: el.scrollLeft, velocity: 0, lastX: e.clientX, lastTime: Date.now() };
    el.setPointerCapture(e.pointerId);
    el.style.cursor = "grabbing";
    el.style.scrollSnapType = "none";
  };

  const onPointerMove = (e: React.PointerEvent) => {
    if (!dragState.current.isDragging || !scrollRef.current) return;
    const dx = e.clientX - dragState.current.startX;
    const now = Date.now();
    const dt = now - dragState.current.lastTime;
    if (dt > 0) {
      dragState.current.velocity = (e.clientX - dragState.current.lastX) / dt;
    }
    dragState.current.lastX = e.clientX;
    dragState.current.lastTime = now;
    scrollRef.current.scrollLeft = dragState.current.scrollStart - dx;
  };

  const onPointerUp = (e: React.PointerEvent) => {
    if (!dragState.current.isDragging || !scrollRef.current) return;
    const el = scrollRef.current;
    el.releasePointerCapture(e.pointerId);
    el.style.cursor = "";
    dragState.current.isDragging = false;

    // Apply inertia
    const v = dragState.current.velocity;
    if (Math.abs(v) > 0.3) {
      const inertia = -v * 300;
      el.scrollBy({ left: inertia, behavior: "smooth" });
    }

    // Restore snap after scroll settles
    setTimeout(() => { el.style.scrollSnapType = "x mandatory"; }, 400);
  };

  return (
    <div className="pt-14">
      <div className="container">
        <ScrollReveal>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-heading-2">{isAr ? "وظائف مميزة" : "Featured Jobs"}</h2>
              <p className="text-body text-muted-foreground mt-1">
                {isAr ? "فرص منتقاة بعناية لك" : "Hand-picked opportunities for you"}
              </p>
            </div>
            <div className="hidden sm:flex items-center gap-1">
              <Button
                variant="outline"
                size="icon"
                className={`h-9 w-9 rounded-full transition-opacity ${!canScrollLeft ? "opacity-30 pointer-events-none" : ""}`}
                onClick={() => scroll("left")}
                aria-label="Scroll left"
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className={`h-9 w-9 rounded-full transition-opacity ${!canScrollRight ? "opacity-30 pointer-events-none" : ""}`}
                onClick={() => scroll("right")}
                aria-label="Scroll right"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </ScrollReveal>

        {isLoading ? (
          <CarouselSkeleton />
        ) : (
          <div
            ref={scrollRef}
            role="region"
            aria-label={isAr ? "وظائف مميزة" : "Featured jobs carousel"}
            tabIndex={0}
            onKeyDown={handleKeyDown}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            className="flex gap-4 overflow-x-auto overflow-y-hidden pb-4 snap-x snap-mandatory scrollbar-none -mx-4 px-4 cursor-grab focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-lg outline-none"
            style={{ scrollSnapType: "x mandatory", WebkitOverflowScrolling: "touch" }}
          >
            {jobs.map((job, i) => (
              <motion.div
                key={job.id}
                className="min-w-[340px] max-w-[380px] snap-start shrink-0"
                initial={reduced ? {} : { opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * MOTION.stagger.normal, duration: 0.35, ease: MOTION.ease.out }}
                whileHover={reduced ? {} : MOTION.presets.hoverLift}
              >
                {isAuthenticated ? (
                  <JobCard
                    job={job}
                    isSaved={isSaved(job.id)}
                    onToggleSave={(id) => (isSaved(id) ? remove(id) : save(Number(id)))}
                  />
                ) : (
                  <TeaserJobCard job={job} />
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
