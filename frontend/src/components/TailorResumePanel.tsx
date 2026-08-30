import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { FileText, Loader2, TrendingUp, AlertCircle, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { tailorResume } from "@/services/phase5";
import type { TailorResult } from "@/services/phase5";

interface TailorResumePanelProps {
  jobId: string;
  jobTitle: string;
  isAr?: boolean;
}

function ScoreRing({ score, label, size = "lg" }: { score: number; label: string; size?: "sm" | "lg" }) {
  const radius = size === "lg" ? 36 : 24;
  const stroke = size === "lg" ? 5 : 4;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const dim = (radius + stroke) * 2;

  const color = score >= 80 ? "#10b981" : score >= 60 ? "#3b82f6" : score >= 40 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={dim} height={dim} className="transform -rotate-90">
        <circle
          cx={radius + stroke}
          cy={radius + stroke}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          className="text-muted/20"
        />
        <circle
          cx={radius + stroke}
          cy={radius + stroke}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700"
        />
      </svg>
      <span className="text-lg font-bold" style={{ color, marginTop: -(dim / 2 + 10) + "px", position: "relative" }}>
        {Math.round(score)}
      </span>
      <p className="text-caption text-muted-foreground mt-2">{label}</p>
    </div>
  );
}

export function TailorResumePanel({ jobId, jobTitle, isAr }: TailorResumePanelProps) {
  const [result, setResult] = useState<TailorResult | null>(null);

  const mutation = useMutation({
    mutationFn: () => tailorResume(jobId),
    onSuccess: (data) => setResult(data),
  });

  if (!result) {
    return (
      <Card>
        <CardContent className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-10 w-10 rounded-full bg-violet-100 dark:bg-violet-900 flex items-center justify-center">
              <FileText className="h-5 w-5 text-violet-600 dark:text-violet-400" />
            </div>
            <div>
              <h3 className="text-body font-semibold">
                {isAr ? "تخصيص السيرة الذاتية" : "Tailor Your Resume"}
              </h3>
              <p className="text-caption text-muted-foreground">
                {isAr
                  ? "احصل على نصائح لتحسين سيرتك لهذه الوظيفة"
                  : "Get ATS score improvement suggestions"}
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            className="w-full rounded-xl press-feedback"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
          >
            {mutation.isPending ? (
              <Loader2 className="h-4 w-4 me-2 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4 me-2" />
            )}
            {isAr ? "حلل سيرتي الذاتية" : "Analyze My Resume"}
          </Button>
          {mutation.isError && (
            <p className="text-caption text-destructive mt-2">
              {isAr ? "فشل التحليل. حاول مرة أخرى." : "Analysis failed. Please try again."}
            </p>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-violet-200 dark:border-violet-800">
      <CardContent className="p-5 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="h-4 w-4 text-violet-600 dark:text-violet-400" />
          <h3 className="text-body font-semibold">
            {isAr ? "نتائج تخصيص السيرة" : "Resume Tailoring Results"}
          </h3>
        </div>

        <div className="flex items-center justify-around py-2">
          <div className="text-center">
            <p className="text-2xl font-bold text-muted-foreground">{Math.round(result.original_score)}</p>
            <p className="text-caption text-muted-foreground">{isAr ? "قبل" : "Before"}</p>
          </div>
          <div className="flex items-center gap-1">
            <TrendingUp className="h-5 w-5 text-emerald-500" />
            <span className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
              +{Math.round(result.score_delta)}
            </span>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{Math.round(result.tailored_score)}</p>
            <p className="text-caption text-muted-foreground">{isAr ? "بعد" : "After"}</p>
          </div>
        </div>

        {result.missing_skills.length > 0 && (
          <div>
            <p className="text-caption font-medium mb-1.5">
              <AlertCircle className="h-3.5 w-3.5 inline me-1 text-amber-500" />
              {isAr ? "مهارات مفقودة" : "Missing Skills"}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {result.missing_skills.slice(0, 8).map((skill) => (
                <Badge key={skill} variant="outline" className="text-caption rounded-lg">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {result.suggestions.length > 0 && (
          <div>
            <p className="text-caption font-medium mb-1.5">
              {isAr ? "اقتراحات" : "Suggestions"}
            </p>
            <ul className="text-caption text-muted-foreground space-y-1.5">
              {result.suggestions.slice(0, 5).map((s, i) => (
                <li key={i} className="flex items-start gap-1.5">
                  <span className="text-violet-500 mt-0.5 shrink-0">{i + 1}.</span>
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        <Button
          variant="ghost"
          size="sm"
          className="w-full text-caption"
          onClick={() => setResult(null)}
        >
          {isAr ? "إعادة التحليل" : "Re-analyze"}
        </Button>
      </CardContent>
    </Card>
  );
}
