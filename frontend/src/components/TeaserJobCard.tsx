import { useState } from "react";
import { Link } from "react-router-dom";
import { Lock, MapPin } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Job } from "@/services/jobs";
import { useTheme } from "@/hooks/use-theme";
import { Usami } from "@/components/Usami";
import { MOTION } from "@/lib/motion-tokens";

interface TeaserJobCardProps {
  job: Job;
}

export function TeaserJobCard({ job }: TeaserJobCardProps) {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const [hovered, setHovered] = useState(false);
  const reduced = useReducedMotion();

  return (
    <Link to="/login" state={{ from: `/app/jobs/${job.slug}` }} className="block">
      <Card
        className="group relative overflow-hidden border-border/60 transition-shadow duration-200 hover:shadow-md cursor-pointer"
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        <CardContent className="p-5">
          <div className="flex items-start gap-3">
            {job.company_logo && (
              <img
                src={job.company_logo}
                alt={job.company_name}
                className="h-10 w-10 rounded-lg object-cover shrink-0 bg-muted"
                loading="eager"
                fetchPriority="high"
              />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-body font-medium truncate">{job.title}</p>
              <p className="text-caption text-muted-foreground">{job.company_name}</p>
              <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                <span className="flex items-center gap-1 text-caption text-muted-foreground">
                  <MapPin className="h-3 w-3" />{job.location}
                </span>
                <Badge variant="secondary" className="text-[10px] px-2 py-0">{job.location_type}</Badge>
              </div>
            </div>
          </div>
          {/* Blur overlay */}
          <div className="mt-3 relative">
            <div className="h-8 rounded bg-muted/40 blur-sm" />
            <div className="absolute inset-0 flex items-center justify-center gap-1.5 text-caption text-muted-foreground">
              <Lock className="h-3 w-3" />
              {isAr ? "سجّل للعرض الكامل" : "Sign in to view details"}
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
