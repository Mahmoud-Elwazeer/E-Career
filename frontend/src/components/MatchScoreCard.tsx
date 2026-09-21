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
  if (score >= 80) return "text-success";
  if (score >= 60) return "text-info";
  if (score >= 40) return "text-warning-foreground";
  return "text-destructive";
}

function progressColor(score: number): string {
  if (score >= 80) return "bg-success";
  if (score >= 60) return "bg-info";
  if (score >= 40) return "bg-warning";
  return "bg-destructive";
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
    <Card className="border-success/30 bg-success/5">
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-success/15 flex items-center justify-center">
              <span className={`text-lg font-bold ${scoreColor(overall)}`}>
                {Math.round(overall)}
              </span>
            </div>
            <div>
              <h3 className="text-body font-semibold text-foreground">
                {isAr ? "نقاط التطابق" : "Match Score"}
              </h3>
              <p className="text-caption text-muted-foreground">
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
            className="text-success"
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
        </div>

        {expanded && (
          <div className="mt-4 space-y-4">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-success" />
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
                    <p className="text-caption font-medium text-success mb-1.5">
                      <TrendingUp className="h-3.5 w-3.5 inline me-1" />
                      {isAr ? "نقاط القوة" : "Strengths"}
                    </p>
                    <ul className="text-caption text-muted-foreground space-y-1">
                      {breakdown.strengths.map((s, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-success mt-0.5">+</span>
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {breakdown.gaps.length > 0 && (
                  <div>
                    <p className="text-caption font-medium text-warning-foreground mb-1.5">
                      <AlertCircle className="h-3.5 w-3.5 inline me-1" />
                      {isAr ? "فجوات" : "Gaps"}
                    </p>
                    <ul className="text-caption text-muted-foreground space-y-1">
                      {breakdown.gaps.map((g, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-warning-foreground mt-0.5">-</span>
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
