import { useRef } from "react";
import { motion, useScroll, useTransform, type MotionValue } from "framer-motion";
import { Globe, Zap, Shield } from "lucide-react";
import { WatermarkBackground } from "@/components/WatermarkBackground";
import { ScrollReveal } from "@/components/motion";
import { CountUp } from "@/components/motion/CountUp";

/* ─── Stats Strip ─── */

interface StatItem {
  n: number;
  suffix: string;
  label: string;
}

export function StatsStrip({
  stats,
  reduced,
}: {
  stats: StatItem[];
  reduced: boolean | null;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start 0.9", "end 0.6"],
  });

  return (
    <section className="py-20" ref={ref}>
      <div className="container">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s, i) => (
            <StatCard key={s.label} stat={s} index={i} reduced={reduced} scrollProgress={scrollYProgress} />
          ))}
        </div>
      </div>
    </section>
  );
}

function StatCard({
  stat,
  index,
  reduced,
  scrollProgress,
}: {
  stat: StatItem;
  index: number;
  reduced: boolean | null;
  scrollProgress: MotionValue<number>;
}) {
  const start = index * 0.15;
  const end = start + 0.4;
  const underlineScale = useTransform(scrollProgress, [start, end], [0, 1]);

  return (
    <motion.div
      className="text-center"
      initial={reduced ? false : { opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{ duration: 0.5, delay: index * 0.1, ease: [0, 0, 0.2, 1] }}
    >
      <CountUp
        target={stat.n}
        suffix={stat.suffix}
        className="text-display text-primary"
        separator={false}
        duration={1400}
      />
      <p className="text-body text-muted-foreground mt-1">{stat.label}</p>
      {/* Scroll-driven progress underline */}
      <div className="mx-auto mt-3 h-[2px] w-10 rounded-full bg-border">
        <motion.div
          className="h-full rounded-full bg-primary origin-left"
          style={{ scaleX: reduced ? 1 : underlineScale }}
        />
      </div>
    </motion.div>
  );
}

/* ─── Why USAM Section ─── */

export function WhyUsamSection({
  isAr,
  reduced,
}: {
  isAr: boolean;
  reduced: boolean | null;
}) {
  const items = [
    {
      icon: Globe,
      title: isAr ? "مصادر متعددة" : "Multiple Sources",
      desc: isAr
        ? "نجمع الوظائف من أفضل المنصات في منطقة الشرق الأوسط وشمال أفريقيا في مكان واحد"
        : "We aggregate from top platforms across MENA in one place",
    },
    {
      icon: Zap,
      title: isAr ? "بحث سريع" : "Lightning Fast",
      desc: isAr
        ? "فلاتر ذكية وبحث فوري للوصول لوظيفتك المثالية بأقل من 3 دقائق"
        : "Smart filters and instant search to find your ideal role in under 3 minutes",
    },
    {
      icon: Shield,
      title: isAr ? "موثوق وآمن" : "Trusted & Safe",
      desc: isAr
        ? "جميع الوظائف مرتبطة مباشرة بمصادرها الأصلية"
        : "All jobs link directly to their original source — no middleman",
    },
  ];

  return (
    <section className="relative overflow-hidden py-16">
      <WatermarkBackground variant="tilt" />
      <div className="container">
        <ScrollReveal>
          <div className="text-center mb-10">
            <h2 className="text-heading-2">{isAr ? "لماذا USAM؟" : "Why USAM?"}</h2>
            <p className="text-body text-muted-foreground mt-2 max-w-md mx-auto">
              {isAr ? "نوفر لك الوقت والجهد في البحث عن عمل" : "We save you time and effort in your job search"}
            </p>
          </div>
        </ScrollReveal>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {items.map((item, i) => (
            <motion.div
              key={item.title}
              initial={
                reduced
                  ? { opacity: 0 }
                  : {
                      opacity: 0,
                      y: 40 + i * 12,
                      x: (i - 1) * -20,
                      scale: 0.92,
                      rotate: (i - 1) * -2,
                    }
              }
              whileInView={{
                opacity: 1,
                y: 0,
                x: 0,
                scale: 1,
                rotate: 0,
              }}
              viewport={{ once: true, amount: 0.15 }}
              transition={{
                duration: reduced ? 0.01 : 0.55,
                delay: reduced ? 0 : i * 0.14,
                ease: [0.16, 1, 0.3, 1],
              }}
              whileHover={
                reduced
                  ? {}
                  : {
                      y: -4,
                      boxShadow: "var(--shadow-lg)",
                      transition: { duration: 0.25, ease: [0, 0, 0.2, 1] },
                    }
              }
              className="bg-card rounded-xl border p-6 h-full transition-colors duration-200"
            >
              <motion.div
                className="rounded-lg bg-primary-muted p-3 w-fit mb-4"
                whileHover={reduced ? {} : { rotate: [0, -6, 6, 0], scale: 1.05 }}
                transition={{ duration: 0.45 }}
              >
                <item.icon className="h-5 w-5 text-primary" />
              </motion.div>
              <h3 className="text-heading-3 mb-2">{item.title}</h3>
              <p className="text-body text-muted-foreground leading-relaxed">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
