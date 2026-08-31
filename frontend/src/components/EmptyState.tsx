import { LucideIcon, FileX, MessageCircle, Search, ClipboardList, Bookmark, Lightbulb, Mic, Bell, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Link } from "react-router-dom";
import { ReactNode } from "react";
import { useRashidChat, RashidTool } from "@/hooks/use-rashid-chat";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  action?: ReactNode;
  secondaryAction?: ReactNode;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "card";
  showRashid?: boolean;
  rashidTool?: RashidTool;
  rashidMessage?: string;
}

export function EmptyState({
  icon: Icon = FileX,
  title,
  description,
  actionLabel,
  actionHref,
  action,
  secondaryAction,
  size = "md",
  variant = "default",
  showRashid = true,
  rashidTool = 'career_path',
  rashidMessage = "مفيش نتايج... عايز أساعدك تحسن البحث بتاعك؟",
}: EmptyStateProps) {
  const { openRashidChat } = useRashidChat();

  const sizeClasses = {
    sm: { container: "py-8", icon: "h-12 w-12", title: "text-base", description: "text-xs" },
    md: { container: "py-20", icon: "h-16 w-16", title: "text-lg", description: "text-sm" },
    lg: { container: "py-24", icon: "h-20 w-20", title: "text-xl", description: "text-base" },
  };

  const classes = sizeClasses[size];

  const content = (
    <div className={`flex flex-col items-center justify-center text-center animate-fade-in ${classes.container}`}>
      <div className={`text-muted-foreground ${classes.icon} flex items-center justify-center mb-4`}>
        <Icon className="h-full w-full" />
      </div>
      <h3 className={`font-medium mb-1 ${classes.title}`}>{title}</h3>
      <p className={`text-muted-foreground max-w-sm ${classes.description}`}>{description}</p>

      {showRashid && (
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800/30 max-w-xs mx-auto">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">👋</span>
            <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
              Rasheed says:
            </span>
          </div>
          <p className="text-xs text-blue-600 dark:text-blue-400 mb-2">
            {rashidMessage}
          </p>
          <Button
            variant="outline"
            size="sm"
            className="w-full text-xs h-8"
            onClick={() => openRashidChat(rashidTool)}
          >
            <MessageCircle className="w-3 h-3 me-1" />
            Help me
          </Button>
        </div>
      )}

      {(action || actionLabel) && (
        <div className="mt-4 flex flex-col sm:flex-row gap-3 items-center">
          {action || (actionLabel && actionHref && (
            <Button asChild className="press-feedback" size="sm">
              <Link to={actionHref}>{actionLabel}</Link>
            </Button>
          ))}
          {secondaryAction}
        </div>
      )}
    </div>
  );

  if (variant === "card") {
    return <Card className="w-full">{content}</Card>;
  }

  return content;
}

// Preset empty states for common scenarios
export const EmptyStates = {
  NoJobs: ({ onClearFilters }: { onClearFilters?: () => void }) => (
    <EmptyState
      icon={Search}
      title="No jobs found"
      description="Try adjusting your search criteria or filters to find more opportunities"
      action={onClearFilters && <Button onClick={onClearFilters} variant="outline" size="sm">Clear Filters</Button>}
      showRashid={true}
      rashidTool="career_path"
      rashidMessage="مش لاقي وظائف مناسبة؟ خليني أساعدك!"
    />
  ),

  NoApplications: () => (
    <EmptyState
      icon={ClipboardList}
      title="No applications yet"
      description="Start applying to jobs and track your application status here"
      actionLabel="Find Jobs"
      actionHref="/app/jobs"
      showRashid={true}
      rashidTool="career_path"
      rashidMessage="جاهز تبدأ؟ خليني أساعدك تلاقي وظائف مناسبة!"
    />
  ),

  NoSavedJobs: () => (
    <EmptyState
      icon={Bookmark}
      title="No saved jobs"
      description="Save jobs you're interested in to review later and get notified of updates"
      actionLabel="Browse Jobs"
      actionHref="/app/jobs"
      showRashid={true}
      rashidTool="career_path"
      rashidMessage="احفظ الوظائف اللي بتعجبك علشان ترجعلها بعدين!"
    />
  ),

  NoRecommendations: () => (
    <EmptyState
      icon={Lightbulb}
      title="Complete your profile for recommendations"
      description="We need to know more about your skills and experience to suggest the best jobs for you"
      actionLabel="Complete Profile"
      actionHref="/app/career"
      showRashid={true}
      rashidTool="cv_review"
      rashidMessage="كمّل بروفايلك وانا هرشحلك أحسن الوظائف!"
    />
  ),

  NoInterviews: () => (
    <EmptyState
      icon={Mic}
      title="No interview practice sessions"
      description="Start practicing with AI-powered mock interviews to improve your skills"
      actionLabel="Start Practice"
      actionHref="/app/interviews"
      showRashid={true}
      rashidTool="interview_prep"
      rashidMessage="مستعد للمقابلة؟ تعال نتدرب سوا!"
    />
  ),

  NoNotifications: () => (
    <EmptyState
      icon={Bell}
      title="No notifications"
      description="You're all caught up! We'll notify you of new job matches and application updates"
      size="sm"
      showRashid={false}
    />
  ),

  NoSearchResults: ({ query }: { query?: string }) => (
    <EmptyState
      icon={Search}
      title={query ? `No results for "${query}"` : "No results found"}
      description="Try different keywords or adjust your search filters"
      size="sm"
      showRashid={true}
      rashidTool="career_path"
      rashidMessage="مش لاقي اللي انت عايزه؟ جرب كلمات تانية!"
    />
  ),

  Error: ({ message, onRetry }: { message?: string; onRetry?: () => void }) => (
    <EmptyState
      icon={AlertCircle}
      title="Something went wrong"
      description={message || "We encountered an error loading this content"}
      action={onRetry && <Button onClick={onRetry} size="sm">Try Again</Button>}
      size="sm"
      showRashid={false}
    />
  ),
};
