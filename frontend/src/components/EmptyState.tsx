import { LucideIcon, FileX, MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { LoginCareerGuide } from "@/components/LoginCareerGuide";
import { useRashidChat } from "@/hooks/use-rashid-chat";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
}

export function EmptyState({
  icon: _Icon = FileX,
  title,
  description,
  actionLabel,
  actionHref,
}: EmptyStateProps) {
  const { openRashidChat } = useRashidChat();

  return (
    <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in">
      <LoginCareerGuide className="mb-4" />
      <h3 className="text-lg font-medium mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-sm">{description}</p>
      
      {/* Rashid helper for no results */}
      <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800/30 max-w-xs mx-auto">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">👋</span>
          <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
            Rashid says:
          </span>
        </div>
        <p className="text-xs text-blue-600 dark:text-blue-400 mb-2">
          "مفيش نتايج... عايز أساعدك تحسن البحث بتاعك؟"
        </p>
        <Button 
          variant="outline" 
          size="sm" 
          className="w-full text-xs h-8"
          onClick={() => openRashidChat('career_path')}
        >
          <MessageCircle className="w-3 h-3 me-1" />
          Help me
        </Button>
      </div>

      {actionLabel && actionHref && (
        <Button asChild className="mt-4 press-feedback" size="sm">
          <Link to={actionHref}>{actionLabel}</Link>
        </Button>
      )}
    </div>
  );
}
