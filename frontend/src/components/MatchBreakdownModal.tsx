import { useQuery } from "@tanstack/react-query";
import { X, CheckCircle, AlertTriangle, Lightbulb } from "lucide-react";
import { getMatchBreakdown } from "@/services/recommendations";
import { Button } from "@/components/ui/button";

interface MatchBreakdownModalProps {
  jobId: number;
  jobTitle: string;
  onClose: () => void;
}

export function MatchBreakdownModal({ jobId, jobTitle, onClose }: MatchBreakdownModalProps) {
  // Fetch match breakdown
  const { data, isLoading, error } = useQuery({
    queryKey: ['match-breakdown', jobId],
    queryFn: () => getMatchBreakdown(jobId),
  });
  
  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-card rounded-lg p-8">
          <div className="animate-spin w-12 h-12 border-4 border-primary border-t-transparent rounded-full mx-auto"></div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-card rounded-lg max-w-md w-full p-6">
          <div className="text-center">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Error Loading Breakdown</h3>
            <p className="text-muted-foreground mb-4">Could not load match breakdown.</p>
            <Button variant="outline" onClick={onClose}>Close</Button>
          </div>
        </div>
      </div>
    );
  }
  
  const overallScore = data?.overall_score || 0;
  
  // Determine score color
  let scoreColor = "text-gray-500";
  let scoreBg = "bg-gray-100";
  let scoreBorder = "border-gray-300";
  
  if (overallScore >= 90) {
    scoreColor = "text-green-600";
    scoreBg = "bg-green-50";
    scoreBorder = "border-green-500";
  } else if (overallScore >= 75) {
    scoreColor = "text-blue-600";
    scoreBg = "bg-blue-50";
    scoreBorder = "border-blue-500";
  } else if (overallScore >= 60) {
    scoreColor = "text-yellow-600";
    scoreBg = "bg-yellow-50";
    scoreBorder = "border-yellow-500";
  }
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-foreground">Match Breakdown</h2>
            <p className="text-muted-foreground">{jobTitle}</p>
          </div>
          <button 
            onClick={onClose} 
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Overall Score */}
          <div className="text-center">
            <div className={`inline-flex items-center justify-center w-32 h-32 rounded-full ${scoreBg} border-4 ${scoreBorder} mb-4`}>
              <span className={`text-4xl font-bold ${scoreColor}`}>
                {overallScore}%
              </span>
            </div>
            <p className="text-muted-foreground">{data?.recommendation}</p>
          </div>
          
          {/* Breakdown */}
          <div className="space-y-4">
            <h3 className="font-semibold text-foreground">Detailed Breakdown</h3>
            
            {Object.entries(data?.breakdown || {}).map(([key, value]) => (
              <div key={key} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-foreground capitalize">{key}</span>
                  <span className="text-lg font-semibold text-primary">
                    {(value as any).score}%
                  </span>
                </div>
                <p className="text-sm text-muted-foreground">{(value as any).reasoning}</p>
              </div>
            ))}
          </div>
          
          {/* Strengths */}
          {data?.strengths && data.strengths.length > 0 && (
            <div>
              <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                Your Strengths
              </h3>
              <ul className="space-y-2">
                {data.strengths.map((strength, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-foreground">
                    <span className="text-green-600 mt-1">✓</span>
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Gaps */}
          {data?.gaps && data.gaps.length > 0 && (
            <div>
              <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                Areas to Improve
              </h3>
              <ul className="space-y-2">
                {data.gaps.map((gap, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-foreground">
                    <span className="text-yellow-600 mt-1">!</span>
                    <span>{gap}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Improvement Tips */}
          {data?.improvement_tips && data.improvement_tips.length > 0 && (
            <div className="bg-primary-muted/30 border border-primary/20 rounded-lg p-4">
              <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                <Lightbulb className="h-5 w-5 text-primary" />
                How to Improve Your Match
              </h3>
              <ul className="space-y-2">
                {data.improvement_tips.map((tip, idx) => (
                  <li key={idx} className="text-sm text-foreground">
                    • {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-6 border-t flex justify-end gap-4">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          <Button>
            Apply Now
          </Button>
        </div>
      </div>
    </div>
  );
}

export default MatchBreakdownModal;