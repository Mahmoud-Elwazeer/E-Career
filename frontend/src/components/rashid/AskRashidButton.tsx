/**
 * Ask Rasheed button + card.
 * Dispatches the `rashid:open-tool` event that RasheedCompanion (the live,
 * globally-mounted assistant) listens for. Uses the shared RasheedAvatar so
 * there is ONE character across the whole app.
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { MessageCircle, FileText, Briefcase, User, GraduationCap } from 'lucide-react';
import { motion } from 'framer-motion';
import { RasheedAvatar } from './RasheedAvatar';

type RashidTool =
  | 'analyze_job'
  | 'cover_letter'
  | 'interview_prep'
  | 'cv_review'
  | 'linkedin_optimizer'
  | 'course_advisor'
  | 'career_path';

interface AskRashidButtonProps {
  tool: RashidTool;
  context?: Record<string, unknown>;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const TOOL_ICONS = {
  analyze_job: MessageCircle,
  cover_letter: FileText,
  interview_prep: Briefcase,
  cv_review: User,
  linkedin_optimizer: MessageCircle,
  course_advisor: GraduationCap,
  career_path: Briefcase,
};

const TOOL_LABELS = {
  analyze_job: { en: 'Analyze Job', ar: 'حلل الوظيفة' },
  cover_letter: { en: 'Cover Letter', ar: 'اكتب خطاب تغطية' },
  interview_prep: { en: 'Interview Prep', ar: 'حضرني للمقابلة' },
  cv_review: { en: 'Review CV', ar: 'راجع السيرة الذاتية' },
  linkedin_optimizer: { en: 'Optimize LinkedIn', ar: 'تحسين لينكدإن' },
  course_advisor: { en: 'Course Advisor', ar: 'استشارة الدورات' },
  career_path: { en: 'Career Path', ar: 'المسار المهني' },
};

export function AskRashidButton({
  tool,
  context = {},
  label,
  size = 'md',
  className = '',
}: AskRashidButtonProps) {
  const handleOpenRashid = () => {
    window.dispatchEvent(
      new CustomEvent('rashid:open-tool', { detail: { tool, context } }),
    );
  };

  const Icon = TOOL_ICONS[tool];
  const labelText = label && typeof label === 'string' ? label : TOOL_LABELS[tool].en;

  const sizeClasses = {
    sm: 'h-8 px-3 text-xs',
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-6 text-base',
  };

  return (
    <motion.button
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      onClick={handleOpenRashid}
      className={`
        ${sizeClasses[size]}
        ${className}
        flex items-center justify-center gap-2
        bg-primary hover:bg-primary-hover text-primary-foreground
        rounded-lg font-medium transition-all
      `}
    >
      <Icon className="w-4 h-4" />
      <span>{labelText}</span>
    </motion.button>
  );
}

// Full card component for the job detail page.
export function AskRashidCard({ jobSlug, isAr }: { jobSlug: string; isAr: boolean }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="surface-card border border-primary/30 rounded-2xl p-5"
    >
      <div className="flex items-start gap-4">
        <RasheedAvatar expression="greeting" size={48} />

        <div className="flex-1">
          <h3 className="text-base font-semibold text-foreground mb-2">
            {isAr ? 'عايز أساعدك في الوظيفة دي؟' : 'Need help with this job?'}
          </h3>

          {expanded ? (
            <div className="space-y-2">
              <AskRashidButton
                tool="analyze_job"
                context={{ jobSlug }}
                label={isAr ? 'حلل الوظيفة' : 'Analyze Job'}
                size="sm"
                className="w-full"
              />
              <AskRashidButton
                tool="cover_letter"
                context={{ jobSlug }}
                label={isAr ? 'اكتب خطاب تغطية' : 'Cover Letter'}
                size="sm"
                className="w-full"
              />
              <AskRashidButton
                tool="interview_prep"
                context={{ jobSlug }}
                label={isAr ? 'حضرني للمقابلة' : 'Interview Prep'}
                size="sm"
                className="w-full"
              />
            </div>
          ) : (
            <Button
              variant="outline"
              className="mt-2 w-full"
              onClick={() => setExpanded(true)}
            >
              {isAr ? 'عرض الخيارات' : 'Show Options'}
            </Button>
          )}
        </div>
      </div>
    </motion.div>
  );
}
