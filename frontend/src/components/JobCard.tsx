import { Link } from "react-router-dom";
import { MapPin, Clock, Bookmark, BookmarkCheck, DollarSign } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { Job } from "@/services/jobs";
import { formatDistanceToNow } from "date-fns";
import { MOTION } from "@/lib/motion-tokens";

interface JobCardProps {
  job: Job;
  isSaved: boolean;
  onToggleSave: (jobId: number | string) => void;
}

function isExpired(job: Job): boolean {
  if (!job.deadline) return false;
  return new Date(job.deadline) < new Date();
}

export function JobCard({ job, isSaved, onToggleSave }: JobCardProps) {
  const expired = isExpired(job);
  const reduced = useReducedMotion();
  const locationClass = `location-${job.location_type}`;

  const salaryLabel =
    job.salary_min && job.salary_max
      ? `${job.salary_min.toLocaleString()}–${job.salary_max.toLocaleString()} ${job.salary_currency ?? ""}`
      : job.salary_min
      ? `From ${job.salary_min.toLocaleString()} ${job.salary_currency ?? ""}`
      : null;

  return (
    <Card className="group hover:shadow-md hover:border-primary/20 transition-all duration-normal border-border/60 animate-fade-in relative overflow-hidden">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            {job.company_logo && (
              <motion.img
                layoutId={reduced ? undefined : `job-${job.id}-logo`}
                src={job.company_logo}
                alt={job.company_name}
                className="h-11 w-11 rounded-lg object-cover shrink-0"
                loading="lazy"
                transition={{ type: "spring", stiffness: 300, damping: 26 }}
              />
            )}
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <Link
                  to={`/app/jobs/${job.slug}`}
                  className="text-body-lg font-medium text-foreground hover:text-primary transition-colors duration-fast truncate"
                >
                  <motion.span
                    layoutId={reduced ? undefined : `job-${job.id}-title`}
                    transition={{ type: "spring", stiffness: 300, damping: 26 }}
                  >
                    {job.title}
                  </motion.span>
                </Link>
                {expired && (
                  <Badge variant="destructive" className="text-[10px] px-1.5 py-0">Expired</Badge>
                )}
              </div>
              <Link
                to={`/app/companies/${job.company_slug}`}
                className="text-body text-muted-foreground mt-0.5 hover:text-primary transition-colors block"
              >
                {job.company_name}
              </Link>
              <div className="flex items-center gap-3 mt-2 text-caption text-muted-foreground flex-wrap">
                <span className="flex items-center gap-1">
                  <MapPin className="h-3 w-3 flip-rtl" />
                  {job.location}
                </span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${locationClass}`}>
                  {job.location_type}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDistanceToNow(new Date(job.posted_at), { addSuffix: true })}
                </span>
                {salaryLabel && (
                  <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                    <DollarSign className="h-3 w-3" />
                    {salaryLabel}
                  </span>
                )}
              </div>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0 text-muted-foreground hover:text-primary"
            onClick={(e) => {
              e.preventDefault();
              onToggleSave(job.id);
            }}
            aria-label={isSaved ? "Unsave job" : "Save job"}
          >
            {isSaved
              ? <BookmarkCheck className="h-4 w-4 text-primary" />
              : <Bookmark className="h-4 w-4" />}
          </Button>
        </div>
        {job.tags && job.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {job.tags.slice(0, 4).map((tag) => (
              <Badge key={tag.id} variant="secondary" className="text-[10px] px-2 py-0.5 rounded-full">
                {tag.name}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
