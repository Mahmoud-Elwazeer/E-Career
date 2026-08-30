import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Star, ChevronDown, ChevronUp, TrendingUp, AlertCircle, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { getMatchBreakdown } from "@/services/recommendations";
import type { MatchBreakdown } from "@/services/recommendations";

interface MatchScoreCardProps {
  jobId: string;
  matchScore?: number;
  isAr?: boolean;
}

function scoreColor(score: number): string {
  if (score >= 80) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 60) return "text-blue-600 dark:text-blue-400";
  if (score >= 40) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

function progressColor(score: number): string {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 60) return "bg-blue-500";
  if (score >= 40) return "bg-amber-500";
  return "bg-red-500";
}

export function MatchScoreCard({ jobId, matchScore, isAr }: MatchScoreCardProps) {
  const [expanded, setExpanded] = useState(false);

  const { data: breakdown, isLoading } = useQuery<MatchBreakdown>({
    queryKey: ["match-breakdown", jobId],
    queryFn: () => getMatchBreakdown(jobId),
    enabled: expanded,
    staleTime: 5 * 60 * 1000,
  });

  const overall = breakdown?.overall_score ?? matchScore;
  if (!overall && overall !== 0) return null;

  return (
    <Card className="border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-950/50">
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center">
              <span className={`text-lg font-bold ${scoreColor(overall)}`}>
                {Math.round(overall)}
              </span>
            </div>
            <div>
              <h3 className="text-body font-semibold text-emerald-800 dark:text-emerald-200">
                {isAr ? "نقاط التطابق" : "Match Score"}
              </h3>
              <p className="text-caption text-emerald-600 dark:text-emerald-400">
                {overall >= 80
                  ? (isAr ? "تطابق ممتاز" : "Excellent match")
                  : overall >= 60
                  ? (isAr ? "تطابق جيد" : "Good match")
                  : (isAr ? "تطابق جزئي" : "Partial match")}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="text-emerald-700 dark:text-emerald-300"
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
        </div>

        {expanded && (
          <div className="mt-4 space-y-4">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-emerald-600" />
              </div>
            ) : breakdown ? (
              <>
                {Object.entries(breakdown.breakdown).map(([factor, detail]) => (
                  <div key={factor} className="space-y-1.5">
                    <div className="flex items-center justify-between text-caption">
                      <span className="text-muted-foreground capitalize">
                        {factor.replace(/_/g, " ")}
                      </span>
                      <span className={`font-semibold ${scoreColor(detail.score)}`}>
                        {Math.round(detail.score)}%
                      </span>
                    </div>
                    <div className="relative h-2 w-full overflow-hidden rounded-full bg-secondary">
                      <div
                        className={`h-full rounded-full transition-all ${progressColor(detail.score)}`}
                        style={{ width: `${detail.score}%` }}
                      />
                    </div>
                    {detail.reasoning && (
                      <p className="text-caption text-muted-foreground/80">{detail.reasoning}</p>
                    )}
                  </div>
                ))}

                {breakdown.strengths.length > 0 && (
                  <div className="pt-2">
                    <p className="text-caption font-medium text-emerald-700 dark:text-emerald-300 mb-1.5">
                      <TrendingUp className="h-3.5 w-3.5 inline me-1" />
                      {isAr ? "نقاط القوة" : "Strengths"}
                    </p>
                    <ul className="text-caption text-muted-foreground space-y-1">
                      {breakdown.strengths.map((s, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-emerald-500 mt-0.5">+</span>
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {breakdown.gaps.length > 0 && (
                  <div>
                    <p className="text-caption font-medium text-amber-700 dark:text-amber-300 mb-1.5">
                      <AlertCircle className="h-3.5 w-3.5 inline me-1" />
                      {isAr ? "فجوات" : "Gaps"}
                    </p>
                    <ul className="text-caption text-muted-foreground space-y-1">
                      {breakdown.gaps.map((g, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-amber-500 mt-0.5">-</span>
                          {g}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {breakdown.recommendation && (
                  <p className="text-caption text-muted-foreground italic border-t pt-3">
                    {breakdown.recommendation}
                  </p>
                )}
              </>
            ) : null}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
