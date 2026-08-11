import { CheckCircle, AlertTriangle, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface DirectApplyBadgeProps {
  isVerified?: boolean;
  sourceUrl?: string;
  sourceName?: string;
  size?: "sm" | "md" | "lg";
  showTooltip?: boolean;
}

export function DirectApplyBadge({
  isVerified = false,
  sourceUrl,
  sourceName,
  size = "md",
  showTooltip = true,
}: DirectApplyBadgeProps) {
  const sizeClasses = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-3 py-1",
    lg: "text-base px-4 py-1.5",
  };

  const iconSizes = {
    sm: "h-3 w-3",
    md: "h-4 w-4",
    lg: "h-5 w-5",
  };

  if (isVerified) {
    const badge = (
      <Badge
        variant="default"
        className={`${sizeClasses[size]} gap-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800 hover:bg-green-200 dark:hover:bg-green-900/50`}
      >
        <CheckCircle className={iconSizes[size]} />
        <span className="font-medium">Direct Apply</span>
      </Badge>
    );

    if (!showTooltip) return badge;

    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>{badge}</TooltipTrigger>
          <TooltipContent className="max-w-xs">
            <p className="font-medium mb-1">✓ Verified Direct Application</p>
            <p className="text-xs text-muted-foreground">
              Apply directly at {sourceName || "the company"}'s website.
              Your application goes straight to the employer.
            </p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Not verified or aggregator source
  const badge = (
    <Badge
      variant="outline"
      className={`${sizeClasses[size]} gap-1.5 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800`}
    >
      <AlertTriangle className={iconSizes[size]} />
      <span className="font-medium">External Source</span>
    </Badge>
  );

  if (!showTooltip) return badge;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>{badge}</TooltipTrigger>
        <TooltipContent className="max-w-xs">
          <p className="font-medium mb-1">⚠ External Job Listing</p>
          <p className="text-xs text-muted-foreground">
            This job is sourced from {sourceName || "a job aggregator"}.
            You'll be redirected to apply on their platform.
          </p>
          {sourceUrl && (
            <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
              <ExternalLink className="h-3 w-3" />
              <span className="truncate">{new URL(sourceUrl).hostname}</span>
            </p>
          )}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// Inline text version for smaller spaces
export function DirectApplyText({
  isVerified = false,
  className = "",
}: {
  isVerified?: boolean;
  className?: string;
}) {
  if (isVerified) {
    return (
      <span className={`inline-flex items-center gap-1 text-sm text-green-600 dark:text-green-400 ${className}`}>
        <CheckCircle className="h-3.5 w-3.5" />
        <span>Apply directly at company website</span>
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-1 text-sm text-yellow-600 dark:text-yellow-400 ${className}`}>
      <ExternalLink className="h-3.5 w-3.5" />
      <span>Apply via external platform</span>
    </span>
  );
}
