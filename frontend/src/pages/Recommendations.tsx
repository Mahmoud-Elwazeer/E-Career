import { useState } from "react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Target, TrendingUp, Lightbulb, AlertCircle, ChevronRight } from "lucide-react";
import { Layout } from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/use-theme";
import { getRecommendations, RecommendedJob } from "@/services/recommendations";

// Match score badge component
function MatchBadge({ score }: { score: number }) {
  let bgColor = "bg-gray-500";
  const textColor = "text-primary-foreground";

  if (score >= 90) {
    bgColor = "bg-success";
  } else if (score >= 75) {
    bgColor = "bg-primary";
  } else if (score >= 60) {
    bgColor = "bg-yellow-500";
  }
  
  return (
    <div className={`${bgColor} ${textColor} px-3 py-1 rounded-full text-sm font-semibold`}>
      {score}% Match
    </div>
  );
}

// Job recommendation card
function RecommendationCard({ 
  recommendation, 
}: { 
  recommendation: RecommendedJob;
}) {
  const {
    job_id, job_title, company_name, location, score,
    employment_type, work_arrangement, salary_min, salary_max,
    match_reasons, explanation, match_factors,
  } = recommendation;
  const matchScore = Math.round(score <= 1 ? score * 100 : score);
  const reasons = match_reasons && match_reasons.length ? match_reasons : (explanation ? [explanation] : []);
  const [expanded, setExpanded] = useState(false);
  const factorEntries = match_factors ? Object.entries(match_factors).filter(([, v]) => v != null && v !== "") : [];

  return (
    <div className="bg-card border rounded-lg overflow-hidden hover:shadow-md transition-shadow">
      {/* Match badge */}
      <div className="flex justify-between items-start p-4 pb-0">
        <div className="flex-1">
          <Link to={`/app/jobs/${job_id}`} className="hover:text-primary">
            <h3 className="text-lg font-semibold text-foreground">{job_title}</h3>
          </Link>
          <p className="text-muted-foreground">{company_name}</p>
        </div>
        <MatchBadge score={matchScore} />
      </div>

      {/* Job details */}
      <div className="p-4 pt-2">
        <div className="flex flex-wrap gap-2 text-sm text-muted-foreground mb-3">
          {location && <span>{location}</span>}
          {work_arrangement && (
            <>
              <span>•</span>
              <span className="capitalize">{work_arrangement}</span>
            </>
          )}
          {employment_type && (
            <>
              <span>•</span>
              <span className="capitalize">{employment_type}</span>
            </>
          )}
        </div>

        {/* Salary */}
        {(salary_min || salary_max) && (
          <div className="text-sm text-muted-foreground mb-3">
            {salary_min?.toLocaleString()} - {salary_max?.toLocaleString()} EGP
          </div>
        )}

        {/* Explainable match reasons (evidence-grounded, no opaque scores) */}
        {reasons.length > 0 && (
          <div className="bg-primary-muted/30 border border-primary/20 rounded-lg p-3 mb-3">
            <p className="text-sm font-medium text-primary mb-1">Why this matches</p>
            <ul className="text-sm text-foreground space-y-1">
              {reasons.map((r, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-primary">•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Expandable factor breakdown */}
        {expanded && factorEntries.length > 0 && (
          <div className="mb-3 rounded-lg border border-border bg-muted/40 p-3">
            <p className="text-sm font-medium text-foreground mb-2">Match breakdown</p>
            <div className="space-y-1.5">
              {factorEntries.map(([k, v]) => (
                <div key={k} className="flex items-center justify-between text-sm">
                  <span className="capitalize text-muted-foreground">{k.replace(/_/g, " ")}</span>
                  <span className="font-medium text-foreground">
                    {typeof v === "number" ? `${Math.round(v <= 1 ? v * 100 : v)}%` : String(v)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
        {expanded && factorEntries.length === 0 && (
          <p className="mb-3 text-sm text-muted-foreground">No additional breakdown available — see the reasons above.</p>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setExpanded((v) => !v)}>
            {expanded ? "Hide breakdown" : "View breakdown"}
          </Button>
          <Button asChild size="sm">
            <Link to={`/app/jobs/${job_id}`}>
              View Job <ChevronRight className="h-4 w-4 ml-1" />
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

// Loading skeleton
function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-card border rounded-lg p-6 animate-pulse">
          <div className="h-6 bg-muted rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-muted rounded w-1/2 mb-3"></div>
          <div className="h-16 bg-muted rounded w-full"></div>
        </div>
      ))}
    </div>
  );
}

// Empty state
function EmptyState() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  
  return (
    <div className="bg-card border rounded-lg p-12 text-center">
      <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
      <h3 className="text-lg font-semibold mb-2">
        {isAr ? "لا توجد توصيات بعد" : "No recommendations yet"}
      </h3>
      <p className="text-muted-foreground mb-4">
        {isAr 
          ? "أكمل ملفك الشخصي للحصول على توصيات وظيفية مخصصة"
          : "Complete your profile to get personalized job recommendations"}
      </p>
      <Button asChild>
        <Link to="/app/profile">
          {isAr ? "أكمل ملفك الشخصي" : "Complete Profile"}
        </Link>
      </Button>
    </div>
  );
}

export default function Recommendations() {
  const { lang } = useTheme();
  const isAr = lang === "ar";

  // Fetch recommendations
  const { data, isLoading, error } = useQuery({
    queryKey: ['recommendations'],
    queryFn: () => getRecommendations(20, 60),
  });
  
  // Calculate stats (scores may be 0-1 or 0-100 depending on path; normalize).
  const normScore = (s: number) => Math.round(s <= 1 ? s * 100 : s);
  const strongMatches = data?.recommendations?.filter(r => normScore(r.score) >= 80).length || 0;
  const avgScore = data?.recommendations?.length
    ? Math.round(
        data.recommendations.reduce((sum, r) => sum + normScore(r.score), 0) / data.recommendations.length
      )
    : 0;
  
  return (
    <Layout>
      <div className="min-h-screen bg-background py-8">
        <div className="container max-w-4xl">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
              <Target className="h-8 w-8 text-primary" />
              {isAr ? "وظائف موصى بها لك" : "Recommended For You"}
            </h1>
            <p className="text-muted-foreground mt-2">
              {isAr 
                ? "وظائف تتناسب مع مهاراتك وتفضيلاتك"
                : "Jobs that match your skills and preferences"}
            </p>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-card border rounded-lg p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary-muted rounded-lg">
                  <TrendingUp className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-foreground">
                    {data?.count || 0}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {isAr ? "وظيفة مطابقة" : "Matches Found"}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-card border rounded-lg p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-success/15 rounded-lg">
                  <Target className="h-5 w-5 text-success" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-foreground">
                    {strongMatches}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {isAr ? "مطابقة قوية" : "Strong Matches"}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-card border rounded-lg p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Lightbulb className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-foreground">
                    {avgScore}%
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {isAr ? "متوسط المطابقة" : "Avg Match Score"}
                  </p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Content */}
          {isLoading ? (
            <LoadingSkeleton />
          ) : error ? (
            <div className="bg-destructive/10 border border-destructive rounded-lg p-4 text-center">
              <p className="text-destructive">
                {isAr ? "حدث خطأ في تحميل التوصيات" : "Error loading recommendations"}
              </p>
            </div>
          ) : data?.count === 0 ? (
            <EmptyState />
          ) : (
            <div className="space-y-4">
              {data?.recommendations?.map((rec) => (
                <RecommendationCard 
                  key={rec.job_id} 
                  recommendation={rec}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}